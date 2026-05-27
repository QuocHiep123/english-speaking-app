#!/usr/bin/env python
# =============================================================================
# A/B Experiment — Whisper "base" vs "small"
# =============================================================================
"""
Re-transcribe custom_baseline audio with the Whisper "small" model,
then compare WER/CER head-to-head against the existing "base" results.

Usage:
    python ai-core/scripts/run_experiment_whisper_small.py

Outputs:
    ai-core/data/processed/whisper_experiments.csv
"""

import csv
import re
import sys
import time
from pathlib import Path
from typing import Dict, List

from jiwer import wer, cer

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
AI_CORE_DIR = SCRIPT_DIR.parent

INPUT_CSV = AI_CORE_DIR / "data" / "processed" / "custom_baseline_labels.csv"
AUDIO_DIR = AI_CORE_DIR / "data" / "raw" / "custom_baseline"
OUTPUT_CSV = AI_CORE_DIR / "data" / "processed" / "whisper_experiments.csv"

WHISPER_SMALL = "small"


# ---------------------------------------------------------------------------
# Text normalization (same logic as evaluate_stt.py)
# ---------------------------------------------------------------------------
def normalize_text(text: str) -> str:
    """Lowercase and strip punctuation for fair WER/CER comparison."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    # 1. Late imports ----------------------------------------------------
    try:
        import torch
    except ImportError:
        print("[ERROR] PyTorch is not installed. Run: pip install torch")
        sys.exit(1)

    try:
        import whisper
    except ImportError:
        print("[ERROR] openai-whisper is not installed. Run: pip install openai-whisper")
        sys.exit(1)

    try:
        from tqdm import tqdm
    except ImportError:
        print("[WARN] tqdm not installed — falling back to plain progress logs.")
        tqdm = None  # type: ignore[assignment]

    # 2. Read existing baseline CSV --------------------------------------
    if not INPUT_CSV.exists():
        print(f"[ERROR] Baseline CSV not found: {INPUT_CSV}")
        print("       Run run_baseline_stt.py first.")
        sys.exit(1)

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

    # 3. Load Whisper "small" model --------------------------------------
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print("=" * 65)
    print("  A/B Experiment — Whisper base vs small")
    print("=" * 65)
    print(f"  Model   : whisper-{WHISPER_SMALL}")
    print(f"  Device  : {device}")
    print(f"  Samples : {len(rows)}  (skipped {skipped})")
    print("-" * 65)

    model = whisper.load_model(WHISPER_SMALL, device=device)

    # 4. Transcribe with "small" & collect results -----------------------
    experiment_rows: List[Dict[str, str]] = []

    iterator = tqdm(rows, desc="Transcribing (small)", unit="file") if tqdm else rows

    for row in iterator:
        file_name = row["file_name"]
        audio_path = AUDIO_DIR / file_name

        if not audio_path.exists():
            print(f"  [SKIP] Audio not found: {audio_path}")
            continue

        start = time.perf_counter()
        result = model.transcribe(
            str(audio_path),
            language="en",
            fp16=(device == "cuda"),
        )
        elapsed = time.perf_counter() - start

        transcript_small = result.get("text", "").strip()

        experiment_rows.append({
            "file_name": file_name,
            "ground_truth": row["ground_truth"],
            "transcript_base": row["whisper_transcript"],
            "transcript_small": transcript_small,
            "processing_time_small": f"{elapsed:.2f}",
        })

        if tqdm is None:
            print(f"  ✓ {file_name}  ({elapsed:.2f}s)")

    if not experiment_rows:
        print("[ERROR] No files were transcribed.")
        sys.exit(1)

    # 5. Compute per-file WER/CER for both models -----------------------
    print()
    print(f"  {'File':<35} {'WER base':>10} {'WER small':>10}  {'Δ':>7}")
    print("  " + "-" * 63)

    base_wers: List[float] = []
    small_wers: List[float] = []
    base_cers: List[float] = []
    small_cers: List[float] = []

    for er in experiment_rows:
        ref = normalize_text(er["ground_truth"])
        hyp_base = normalize_text(er["transcript_base"])
        hyp_small = normalize_text(er["transcript_small"])

        w_base = wer(ref, hyp_base)
        w_small = wer(ref, hyp_small)
        c_base = cer(ref, hyp_base)
        c_small = cer(ref, hyp_small)

        base_wers.append(w_base)
        small_wers.append(w_small)
        base_cers.append(c_base)
        small_cers.append(c_small)

        delta = w_small - w_base
        arrow = "↓" if delta < 0 else ("↑" if delta > 0 else "=")
        print(
            f"  {er['file_name']:<35} "
            f"{w_base:>9.2%} {w_small:>9.2%}  {arrow} {abs(delta):.2%}"
        )

    # 6. Aggregate comparison --------------------------------------------
    n = len(experiment_rows)
    avg_wer_base = sum(base_wers) / n
    avg_wer_small = sum(small_wers) / n
    avg_cer_base = sum(base_cers) / n
    avg_cer_small = sum(small_cers) / n

    # Corpus-level
    all_refs = [normalize_text(r["ground_truth"]) for r in experiment_rows]
    all_hyp_base = [normalize_text(r["transcript_base"]) for r in experiment_rows]
    all_hyp_small = [normalize_text(r["transcript_small"]) for r in experiment_rows]

    corpus_wer_base = wer(all_refs, all_hyp_base)
    corpus_wer_small = wer(all_refs, all_hyp_small)
    corpus_cer_base = cer(all_refs, all_hyp_base)
    corpus_cer_small = cer(all_refs, all_hyp_small)

    print()
    print("=" * 65)
    print("  COMPARISON SUMMARY")
    print("=" * 65)
    print(f"  {'Metric':<28} {'base':>10} {'small':>10} {'Δ':>10}")
    print("  " + "-" * 58)
    for label, vb, vs in [
        ("Avg WER (per-file)", avg_wer_base, avg_wer_small),
        ("Avg CER (per-file)", avg_cer_base, avg_cer_small),
        ("Corpus WER", corpus_wer_base, corpus_wer_small),
        ("Corpus CER", corpus_cer_base, corpus_cer_small),
    ]:
        d = vs - vb
        sign = "+" if d > 0 else ""
        print(f"  {label:<28} {vb:>9.2%} {vs:>9.2%} {sign}{d:>9.2%}")
    print("=" * 65)

    # 7. Save experiment CSV ---------------------------------------------
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "file_name",
        "ground_truth",
        "transcript_base",
        "transcript_small",
        "processing_time_small",
    ]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(experiment_rows)

    print(f"\n  Experiment CSV saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
