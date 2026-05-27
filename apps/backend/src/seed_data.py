# =============================================================================
# Seed the ielts_prompts table with IELTS Speaking questions.
# =============================================================================
#
# Usage:
#     cd apps/backend
#     python -m src.seed_data              # Load from static JSON (default)
#     python -m src.seed_data --generate   # Generate via Groq API instead

import argparse
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from src.database import IELTSPrompt, SessionLocal, init_db

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = "llama-3.3-70b-versatile"

# Static dataset bundled with the project
STATIC_DATA_PATH = Path(__file__).parent / "data" / "ielts_questions.json"

SYSTEM_PROMPT = (
    "You are an expert IELTS examiner. "
    "Generate exactly 15 IELTS Speaking questions: "
    "5 for Part 1, 5 for Part 2, and 5 for Part 3. "
    "Cover a variety of common topics (e.g. hobbies, education, technology, "
    "environment, travel, health, work, culture). "
    "Return your answer as a JSON object with a single key \"questions\" "
    "whose value is an array of 15 objects. "
    "Each object must have exactly three keys: "
    "\"part\" (integer 1, 2, or 3), \"topic\" (string), \"question\" (string). "
    "Output ONLY valid JSON — no markdown, no explanation."
)


def load_static_questions() -> list[dict]:
    """Load IELTS questions from the bundled JSON file."""
    with open(STATIC_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["questions"]


async def generate_questions() -> list[dict]:
    """Call Groq LLM to generate IELTS Speaking questions."""
    from groq import AsyncGroq

    client = AsyncGroq(api_key=GROQ_API_KEY)

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Generate the 15 IELTS Speaking questions as JSON."},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)
    return data["questions"]


def seed_if_empty() -> int:
    """Seed prompts from the bundled static JSON only when the table is empty.

    Safe to call on every startup: it never makes network calls and is a no-op
    once prompts already exist. Returns the number of prompts inserted.
    """
    init_db()  # Ensure tables exist on the active engine
    session = SessionLocal()
    try:
        if session.query(IELTSPrompt).count() > 0:
            return 0
        questions = load_static_questions()
        for q in questions:
            session.add(
                IELTSPrompt(part=q["part"], topic=q["topic"], question=q["question"])
            )
        session.commit()
        return len(questions)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def insert_questions(questions: list[dict]) -> None:
    """Insert generated questions into the ielts_prompts table."""
    init_db()  # Ensure tables exist
    session = SessionLocal()
    try:
        for q in questions:
            prompt = IELTSPrompt(
                part=q["part"],
                topic=q["topic"],
                question=q["question"],
            )
            session.add(prompt)
        session.commit()
        print(f"Successfully inserted {len(questions)} IELTS prompts.")
    except Exception as exc:
        session.rollback()
        print(f"Error inserting prompts: {exc}")
        raise
    finally:
        session.close()


async def main() -> None:
    """Generate and seed IELTS prompts."""
    parser = argparse.ArgumentParser(description="Seed IELTS Speaking prompts")
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate questions via Groq API instead of using the static dataset",
    )
    args = parser.parse_args()

    if args.generate:
        print(f"Generating questions via Groq ({MODEL})...")
        questions = await generate_questions()
    else:
        print(f"Loading questions from {STATIC_DATA_PATH}...")
        questions = load_static_questions()

    print(f"Received {len(questions)} questions. Inserting into database...")
    insert_questions(questions)
    print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(main())
