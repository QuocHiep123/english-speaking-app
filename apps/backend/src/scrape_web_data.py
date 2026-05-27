# =============================================================================
# Scrape & Extract IELTS Speaking Questions → Supabase
# =============================================================================
#
# Architecture:
#   1. Scrape public IELTS question pages with requests + BeautifulSoup
#   2. Chunk cleaned text into ~2500-char segments
#   3. Send each chunk to Groq LLM for structured extraction
#   4. Insert valid questions into ielts_prompts (deduplicated)
#   5. Stop cleanly once 300 unique questions are reached
#
# Fallback: If scraping yields < 300, the LLM generates the remainder.
#
# Usage:
#     cd apps/backend
#     python -m src.scrape_web_data
#
# Note: Respect robots.txt and site ToS. Add rate-limiting delays between
#       requests. These URLs are public IELTS study resources.

import asyncio
import json
import os
import re
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from groq import AsyncGroq

from src.database import IELTSPrompt, SessionLocal, init_db

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = "llama-3.3-70b-versatile"
TARGET_COUNT = 300
MAX_CONSECUTIVE_FAILURES = 5  # abort if LLM fails this many times in a row
CHUNK_SIZE = 2500          # characters per chunk sent to LLM
REQUEST_DELAY = 2.0        # seconds between HTTP requests (be polite)
LLM_DELAY = 1.0            # seconds between Groq API calls (rate-limit)

# Public IELTS Speaking resource pages
TARGET_URLS = [
    # Part 1
    "https://ieltsliz.com/ielts-speaking-part-1-topics/",
    "https://ieltsliz.com/ielts-speaking-free-lessons-tips-and-more/",
    "https://www.ieltsadvantage.com/2015/03/03/ielts-speaking-part-1-questions/",
    "https://www.ieltsbuddy.com/ielts-speaking-part-1.html",
    # Part 2
    "https://ieltsliz.com/ielts-speaking-part-2-topics/",
    "https://ieltsliz.com/ielts-speaking-part-2-topics-cue-cards/",
    "https://www.ieltsadvantage.com/2015/04/06/ielts-speaking-part-2-questions/",
    "https://www.ieltsbuddy.com/ielts-speaking-part-2.html",
    # Part 3
    "https://ieltsliz.com/ielts-speaking-part-3-topics/",
    "https://www.ieltsadvantage.com/2015/04/13/ielts-speaking-part-3-questions/",
    "https://www.ieltsbuddy.com/ielts-speaking-part-3.html",
]

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------
EXTRACT_SYSTEM_PROMPT = (
    "You are an IELTS data extraction assistant. "
    "Given a chunk of text scraped from an IELTS preparation website, "
    "extract ALL valid IELTS Speaking questions you can identify. "
    "Classify each question by its part (1, 2, or 3) and topic. "
    "Return a JSON object with a single key \"questions\" whose value is an "
    "array of objects with keys: \"part\" (int), \"topic\" (str), \"question\" (str). "
    "If the text contains no valid IELTS questions, return {\"questions\": []}. "
    "Output ONLY valid JSON."
)

GENERATE_SYSTEM_PROMPT = (
    "You are an expert IELTS examiner. "
    "Generate exactly {count} unique IELTS Speaking questions. "
    "Distribute them roughly equally across Part 1, Part 2, and Part 3. "
    "Use a wide variety of topics (hobbies, education, technology, environment, "
    "travel, health, work, culture, family, media, sports, food, art, music, "
    "science, history, transport, housing, fashion, animals, language). "
    "Do NOT repeat any of the following topics that have already been used: {used_topics}. "
    "Return a JSON object with a single key \"questions\" whose value is an "
    "array of objects. Each object must have exactly three keys: "
    "\"part\" (int 1-3), \"topic\" (str), \"question\" (str). "
    "Output ONLY valid JSON."
)

# ---------------------------------------------------------------------------
# HTTP headers (mimic a real browser to avoid blocks)
# ---------------------------------------------------------------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ============================= SCRAPING ====================================

def fetch_page(url: str) -> Optional[str]:
    """Fetch a URL and return the HTML, or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        print(f"  [WARN] Failed to fetch {url}: {exc}")
        return None


def extract_text(html: str) -> str:
    """Extract clean text from HTML, removing scripts/styles/nav."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside",
                     "form", "noscript", "iframe"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Clean excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def chunk_text(text: str, max_chars: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks of roughly max_chars, breaking on paragraphs."""
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 > max_chars and current:
            chunks.append(current.strip())
            current = para
        else:
            current = current + "\n\n" + para if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


# ========================== LLM EXTRACTION =================================

async def extract_questions_from_chunk(
    client: AsyncGroq,
    chunk: str,
) -> list[dict]:
    """Send a text chunk to Groq and return extracted IELTS questions."""
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract IELTS questions from this text:\n\n{chunk}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        raw = response.choices[0].message.content
        data = json.loads(raw)
        questions = data.get("questions", [])
        # Validate structure
        return [
            q for q in questions
            if isinstance(q.get("part"), int)
            and isinstance(q.get("topic"), str)
            and isinstance(q.get("question"), str)
            and q["part"] in (1, 2, 3)
            and len(q["question"]) > 10
        ]
    except Exception as exc:
        print(f"  [WARN] LLM extraction error: {exc}")
        return []


async def generate_remaining(
    client: AsyncGroq,
    count: int,
    used_topics: set[str],
) -> list[dict]:
    """Generate additional questions via LLM to reach the target count."""
    prompt = GENERATE_SYSTEM_PROMPT.format(
        count=count,
        used_topics=", ".join(sorted(used_topics)[:50]) or "none",
    )
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Generate {count} unique IELTS Speaking questions as JSON."},
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
        )
        raw = response.choices[0].message.content
        data = json.loads(raw)
        questions = data.get("questions", [])
        return [
            q for q in questions
            if isinstance(q.get("part"), int)
            and isinstance(q.get("topic"), str)
            and isinstance(q.get("question"), str)
            and q["part"] in (1, 2, 3)
            and len(q["question"]) > 10
        ]
    except Exception as exc:
        print(f"  [WARN] LLM generation error: {exc}")
        return []


# ========================= DEDUPLICATION ===================================

def normalise(text: str) -> str:
    """Lowercase, strip punctuation for dedup comparison."""
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def deduplicate(
    new_questions: list[dict],
    seen: set[str],
) -> list[dict]:
    """Return only questions whose normalised text hasn't been seen."""
    unique = []
    for q in new_questions:
        key = normalise(q["question"])
        if key not in seen and len(key) > 5:
            seen.add(key)
            unique.append(q)
    return unique


# ========================= DB INSERTION ====================================

def insert_batch(questions: list[dict]) -> int:
    """Insert a batch of questions into ielts_prompts. Returns count inserted."""
    if not questions:
        return 0
    session = SessionLocal()
    try:
        for q in questions:
            session.add(IELTSPrompt(
                part=q["part"],
                topic=q["topic"][:255],
                question=q["question"],
            ))
        session.commit()
        return len(questions)
    except Exception as exc:
        session.rollback()
        print(f"  [ERROR] DB insert failed: {exc}")
        return 0
    finally:
        session.close()


# ========================= MAIN PIPELINE ==================================

async def main() -> None:
    """Scrape → Extract → Store pipeline targeting 300 questions."""
    init_db()
    client = AsyncGroq(api_key=GROQ_API_KEY)

    total_extracted = 0
    seen: set[str] = set()       # normalised question texts for dedup
    used_topics: set[str] = set()

    # Load existing questions from DB so we don't insert duplicates
    session = SessionLocal()
    try:
        existing = session.query(IELTSPrompt).all()
        for row in existing:
            seen.add(normalise(row.question))
            used_topics.add(row.topic.lower())
        print(f"Found {len(existing)} existing prompts in DB. "
              f"Will add up to {TARGET_COUNT - len(existing)} more.\n")
        remaining_target = TARGET_COUNT - len(existing)
        if remaining_target <= 0:
            print(f"Already have {len(existing)} >= {TARGET_COUNT} prompts. Nothing to do.")
            return
    finally:
        session.close()

    # ---- Phase 1: Scrape & Extract ----------------------------------------
    print("=" * 60)
    print("PHASE 1: Scraping IELTS websites")
    print("=" * 60)

    for i, url in enumerate(TARGET_URLS, 1):
        if total_extracted >= remaining_target:
            break

        print(f"\n[{i}/{len(TARGET_URLS)}] Fetching: {url}")
        html = fetch_page(url)
        if not html:
            continue

        text = extract_text(html)
        chunks = chunk_text(text)
        print(f"  Extracted {len(text):,} chars → {len(chunks)} chunks")

        for j, chunk in enumerate(chunks, 1):
            if total_extracted >= remaining_target:
                break

            questions = await extract_questions_from_chunk(client, chunk)
            unique = deduplicate(questions, seen)

            # Trim to not exceed target
            if total_extracted + len(unique) > remaining_target:
                unique = unique[: remaining_target - total_extracted]

            if unique:
                inserted = insert_batch(unique)
                total_extracted += inserted
                for q in unique:
                    used_topics.add(q["topic"].lower())
                print(f"  Chunk {j}/{len(chunks)}: +{inserted} questions "
                      f"(Total: {total_extracted}/{remaining_target})")
            else:
                print(f"  Chunk {j}/{len(chunks)}: no new questions found")

            await asyncio.sleep(LLM_DELAY)

        time.sleep(REQUEST_DELAY)

    # ---- Phase 2: Generate remainder via LLM ------------------------------
    if total_extracted < remaining_target:
        shortfall = remaining_target - total_extracted
        print(f"\n{'=' * 60}")
        print(f"PHASE 2: Generating {shortfall} remaining questions via LLM")
        print("=" * 60)

        # Generate in batches of 20 to stay within token limits
        batch_size = 20
        consecutive_failures = 0
        while total_extracted < remaining_target:
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                print(f"\n  [ABORT] {MAX_CONSECUTIVE_FAILURES} consecutive failures. "
                      f"Stopping with {total_extracted} new questions.")
                break

            need = min(batch_size, remaining_target - total_extracted)
            print(f"\n  Requesting batch of {need} questions...")

            generated = await generate_remaining(client, need, used_topics)
            unique = deduplicate(generated, seen)

            if total_extracted + len(unique) > remaining_target:
                unique = unique[: remaining_target - total_extracted]

            if unique:
                inserted = insert_batch(unique)
                total_extracted += inserted
                consecutive_failures = 0
                for q in unique:
                    used_topics.add(q["topic"].lower())
                print(f"  +{inserted} questions (Total: {total_extracted}/{remaining_target})")
            else:
                consecutive_failures += 1
                print(f"  No new unique questions generated "
                      f"(failure {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})")

            await asyncio.sleep(LLM_DELAY)

    # ---- Done -------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print(f"SUCCESS: Extracted {total_extracted} questions "
          f"(DB now has {total_extracted + len(seen) - total_extracted} total).")
    print("=" * 60)

    # Final count verification
    session = SessionLocal()
    try:
        count = session.query(IELTSPrompt).count()
        print(f"Verified: {count} total prompts in ielts_prompts table.")
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(main())
