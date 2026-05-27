#!/usr/bin/env python
# =============================================================================
# LLM Error Correction Experiment — Ollama (Local)
# =============================================================================
"""
Use a local LLM via Ollama to post-correct Whisper "small" transcriptions,
then measure whether WER improves compared to the raw STT output.

Prerequisites:
    1. Install Ollama: https://ollama.com
    2. Pull the model:  ollama pull llama3.1
    3. Ensure the server is running (default: http://localhost:11434)

Usage:
    python ai-core/scripts/run_ollama_correction.py

Outputs:
    ai-core/data/processed/llm_correction_results.csv
"""

import csv
import re
import sys
import time
from pathlib import Path
from typing import Dict, List

import requests
from jiwer import wer, cer

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
AI_CORE_DIR = SCRIPT_DIR.parent

INPUT_CSV = AI_CORE_DIR / "data" / "processed" / "whisper_experiments.csv"
OUTPUT_CSV = AI_CORE_DIR / "data" / "processed" / "llm_correction_results.csv"

# ---------------------------------------------------------------------------
# Ollama config
# ---------------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"
REQUEST_TIMEOUT = 120  # seconds per request

SYSTEM_PROMPT = (
    "You are an expert IELTS examiner. Your task is to correct the "
    "transcription errors in the following text caused by a Speech-to-Text "
    "system listening to a Vietnamese speaker. Fix ONLY the obvious "
    "transcription errors, grammar, and typos to make it a coherent English "
    "sentence based on context. DO NOT change the user's original meaning or "
    "add new ideas. Return ONLY the corrected text, without any explanations."
)


# ---------------------------------------------------------------------------
# Text normalization (consistent with evaluate_stt.py)
# ---------------------------------------------------------------------------
def normalize_text(text: str) -> str:
    """Lowercase and strip punctuation for fair WER/CER comparison."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Ollama helper
# ---------------------------------------------------------------------------
def call_ollama(transcript: str) -> str:
    """Send a transcript to the local Ollama server and return corrected text."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": transcript,
        "system": SYSTEM_PROMPT,
        "stream": False,
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    return resp.json().get("response", "").strip()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    # 1. Validate input --------------------------------------------------
    if not INPUT_CSV.exists():
        print(f"[ERROR] Input CSV not found: {INPUT_CSV}")
        print("       Run run_experiment_whisper_small.py first.")
        sys.exit(1)

    # 2. Quick connectivity check ----------------------------------------
    try:
        health = requests.get(
            "http://localhost:11434/api/tags", timeout=5
        )
        health.raise_for_status()
    except requests.ConnectionError:
        print("[ERROR] Cannot reach Ollama at http://localhost:11434")
        print("       Make sure Ollama is running: ollama serve")
        sys.exit(1)

    # 3. Read experiment CSV ---------------------------------------------
    rows: List[Dict[str, str]] = []
    skipped = 0

    with open(INPUT_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gt = row.get("ground_truth", "").strip()
            if not gt or "[unintelligible]" in gt.lower():
                skipped += 1
                continue
            rows.append(row)

    if not rows:
        print("[ERROR] No valid rows after filtering.")
        sys.exit(1)

    print("=" * 65)
    print("  LLM Error Correction — Ollama (local)")
    print("=" * 65)
    print(f"  Model   : {OLLAMA_MODEL}")
    print(f"  Samples : {len(rows)}  (skipped {skipped})")
    print("-" * 65)

    # 4. Correction loop -------------------------------------------------
    result_rows: List[Dict[str, str]] = []

    for i, row in enumerate(rows, 1):
        file_name = row["file_name"]
        transcript_small = row["transcript_small"]

        print(f"  [{i}/{len(rows)}] {file_name} ... ", end="", flush=True)

        start = time.perf_counter()
        try:
            corrected = call_ollama(transcript_small)
        except (requests.RequestException, KeyError) as exc:
            print(f"ERROR: {exc}")
            corrected = transcript_small  # fallback to original on failure
        elapsed = time.perf_counter() - start

        print(f"done ({elapsed:.1f}s)")

        result_rows.append({
            "file_name": file_name,
            "ground_truth": row["ground_truth"],
            "transcript_small": transcript_small,
            "corrected_text": corrected,
            "correction_time": f"{elapsed:.2f}",
        })

    # 5. Compute WER/CER comparison -------------------------------------
    print()
    print(f"  {'File':<35} {'WER small':>10} {'WER LLM':>10}  {'Δ':>7}")
    print("  " + "-" * 63)

    small_wers: List[float] = []
    llm_wers: List[float] = []
    small_cers: List[float] = []
    llm_cers: List[float] = []

    for r in result_rows:
        ref = normalize_text(r["ground_truth"])
        hyp_small = normalize_text(r["transcript_small"])
        hyp_llm = normalize_text(r["corrected_text"])

        w_small = wer(ref, hyp_small)
        w_llm = wer(ref, hyp_llm)
        c_small = cer(ref, hyp_small)
        c_llm = cer(ref, hyp_llm)

        small_wers.append(w_small)
        llm_wers.append(w_llm)
        small_cers.append(c_small)
        llm_cers.append(c_llm)

        delta = w_llm - w_small
        arrow = "↓" if delta < 0 else ("↑" if delta > 0 else "=")
        print(
            f"  {r['file_name']:<35} "
            f"{w_small:>9.2%} {w_llm:>9.2%}  {arrow} {abs(delta):.2%}"
        )

    # 6. Aggregate summary -----------------------------------------------
    n = len(result_rows)
    avg_wer_small = sum(small_wers) / n
    avg_wer_llm = sum(llm_wers) / n
    avg_cer_small = sum(small_cers) / n
    avg_cer_llm = sum(llm_cers) / n

    all_refs = [normalize_text(r["ground_truth"]) for r in result_rows]
    all_hyp_small = [normalize_text(r["transcript_small"]) for r in result_rows]
    all_hyp_llm = [normalize_text(r["corrected_text"]) for r in result_rows]

    corpus_wer_small = wer(all_refs, all_hyp_small)
    corpus_wer_llm = wer(all_refs, all_hyp_llm)
    corpus_cer_small = cer(all_refs, all_hyp_small)
    corpus_cer_llm = cer(all_refs, all_hyp_llm)

    print()
    print("=" * 65)
    print("  COMPARISON SUMMARY — small vs LLM-corrected")
    print("=" * 65)
    print(f"  {'Metric':<28} {'small':>10} {'LLM':>10} {'Δ':>10}")
    print("  " + "-" * 58)
    for label, vs, vl in [
        ("Avg WER (per-file)", avg_wer_small, avg_wer_llm),
        ("Avg CER (per-file)", avg_cer_small, avg_cer_llm),
        ("Corpus WER", corpus_wer_small, corpus_wer_llm),
        ("Corpus CER", corpus_cer_small, corpus_cer_llm),
    ]:
        d = vl - vs
        sign = "+" if d > 0 else ""
        print(f"  {label:<28} {vs:>9.2%} {vl:>9.2%} {sign}{d:>9.2%}")
    print("=" * 65)

    # 7. Save CSV --------------------------------------------------------
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "file_name",
        "ground_truth",
        "transcript_small",
        "corrected_text",
        "correction_time",
    ]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result_rows)

    print(f"\n  Results saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
