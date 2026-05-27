#!/usr/bin/env python
# =============================================================================
# STT Evaluation Script — WER & CER for Whisper Baseline
# =============================================================================
"""
Evaluate Whisper STT transcription quality against ground truth labels.

Reads the CSV produced by run_baseline_stt.py, computes per-file and
aggregate Word Error Rate (WER) and Character Error Rate (CER),
prints a summary to the terminal, and saves detailed results to JSON.

Usage:
    python ai-core/scripts/evaluate_stt.py
"""

import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any

from jiwer import wer, cer

# ---------------------------------------------------------------------------
# Paths (resolved relative to *this* script → ai-core/scripts/)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
AI_CORE_DIR = SCRIPT_DIR.parent

INPUT_CSV = AI_CORE_DIR / "data" / "processed" / "custom_baseline_labels.csv"
OUTPUT_JSON = AI_CORE_DIR / "data" / "processed" / "evaluation_results.json"


# ---------------------------------------------------------------------------
# Text Normalization
# ---------------------------------------------------------------------------
def normalize_text(text: str) -> str:
    """Lowercase and strip punctuation for fair WER/CER comparison."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)   # remove all non-alphanumeric / non-space
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------
def evaluate() -> None:
    # 1. Validate input --------------------------------------------------
    if not INPUT_CSV.exists():
        print(f"[ERROR] Input CSV not found: {INPUT_CSV}")
        print("       Run run_baseline_stt.py first to generate it.")
        sys.exit(1)

    # 2. Read & filter CSV -----------------------------------------------
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
        print("[ERROR] No valid rows found after filtering.")
        sys.exit(1)

    print("=" * 65)
    print("  STT Evaluation — WER & CER")
    print("=" * 65)
    print(f"  Input    : {INPUT_CSV}")
    print(f"  Samples  : {len(rows)}  (skipped {skipped})")
    print("-" * 65)

    # 3. Per-file evaluation ---------------------------------------------
    per_file_results: List[Dict[str, Any]] = []
    total_wer = 0.0
    total_cer = 0.0

    for row in rows:
        file_name = row["file_name"]
        hypothesis = normalize_text(row["whisper_transcript"])
        reference = normalize_text(row["ground_truth"])

        file_wer = wer(reference, hypothesis)
        file_cer = cer(reference, hypothesis)

        total_wer += file_wer
        total_cer += file_cer

        per_file_results.append({
            "file_name": file_name,
            "reference": reference,
            "hypothesis": hypothesis,
            "wer": round(file_wer, 4),
            "cer": round(file_cer, 4),
            "processing_time": float(row.get("processing_time", 0)),
        })

        print(f"  {file_name:<35} WER={file_wer:.2%}  CER={file_cer:.2%}")

    # 4. Aggregate metrics -----------------------------------------------
    n = len(per_file_results)
    avg_wer = total_wer / n
    avg_cer = total_cer / n

    # Also compute corpus-level WER/CER (all references / hypotheses at once)
    all_references = [r["reference"] for r in per_file_results]
    all_hypotheses = [r["hypothesis"] for r in per_file_results]
    corpus_wer = wer(all_references, all_hypotheses)
    corpus_cer = cer(all_references, all_hypotheses)

    print("-" * 65)
    print(f"  Average WER (per-file) : {avg_wer:.2%}")
    print(f"  Average CER (per-file) : {avg_cer:.2%}")
    print(f"  Corpus  WER            : {corpus_wer:.2%}")
    print(f"  Corpus  CER            : {corpus_cer:.2%}")
    print("=" * 65)

    # 5. Save detailed JSON ----------------------------------------------
    output_payload: Dict[str, Any] = {
        "summary": {
            "total_files": n,
            "skipped_files": skipped,
            "average_wer": round(avg_wer, 4),
            "average_cer": round(avg_cer, 4),
            "corpus_wer": round(corpus_wer, 4),
            "corpus_cer": round(corpus_cer, 4),
        },
        "per_file": per_file_results,
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)

    print(f"\n  Results saved to: {OUTPUT_JSON}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    evaluate()
