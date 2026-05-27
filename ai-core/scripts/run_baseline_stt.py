#!/usr/bin/env python
# =============================================================================
# Baseline STT — Whisper Transcription for Custom Recordings
# =============================================================================
"""
Transcribe all .wav files in the custom_baseline folder using OpenAI Whisper
and export the results to a CSV for downstream evaluation.

Usage:
    python ai-core/scripts/run_baseline_stt.py

Output:
    ai-core/data/processed/custom_baseline_labels.csv
"""

import csv
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (resolved relative to *this* script → ai-core/scripts/)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
AI_CORE_DIR = SCRIPT_DIR.parent                               # ai-core/

INPUT_DIR = AI_CORE_DIR / "data" / "raw" / "custom_baseline"
OUTPUT_DIR = AI_CORE_DIR / "data" / "processed"
OUTPUT_CSV = OUTPUT_DIR / "custom_baseline_labels.csv"

WHISPER_MODEL_NAME = "base"   # see docs for trade-off rationale
CSV_HEADER = ["file_name", "whisper_transcript", "ground_truth", "processing_time"]


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Late imports — fail fast with a clear message if deps are missing
    # ------------------------------------------------------------------
    try:
        import torch
    except ImportError:
        print("[ERROR] PyTorch is not installed. Run: pip install torch")
        sys.exit(1)

    try:
        import whisper  # openai-whisper
    except ImportError:
        print("[ERROR] openai-whisper is not installed. Run: pip install openai-whisper")
        sys.exit(1)

    try:
        from tqdm import tqdm
    except ImportError:
        print("[WARN] tqdm not installed — falling back to plain progress logs.")
        tqdm = None  # type: ignore[assignment]

    # ------------------------------------------------------------------
    # 2. Validate input directory
    # ------------------------------------------------------------------
    if not INPUT_DIR.exists():
        print(f"[ERROR] Input directory not found: {INPUT_DIR}")
        sys.exit(1)

    wav_files = sorted(INPUT_DIR.glob("*.wav"))
    if not wav_files:
        print(f"[ERROR] No .wav files found in {INPUT_DIR}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 3. Load Whisper model
    # ------------------------------------------------------------------
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("=" * 65)
    print("  Baseline STT — OpenAI Whisper Transcription")
    print("=" * 65)
    print(f"  Model   : whisper-{WHISPER_MODEL_NAME}")
    print(f"  Device  : {device}")
    print(f"  Files   : {len(wav_files)} .wav files")
    print("-" * 65)

    try:
        model = whisper.load_model(WHISPER_MODEL_NAME, device=device)
    except Exception as exc:
        print(f"[ERROR] Failed to load Whisper model '{WHISPER_MODEL_NAME}': {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 4. Transcription loop
    # ------------------------------------------------------------------
    results: list[list[str]] = []
    total_time = 0.0

    iterator = tqdm(wav_files, desc="Transcribing", unit="file") if tqdm else wav_files

    for wav_path in iterator:
        file_name = wav_path.name

        try:
            start = time.perf_counter()
            output = model.transcribe(
                str(wav_path),
                language="en",
                fp16=(device == "cuda"),
            )
            elapsed = time.perf_counter() - start
        except Exception as exc:
            print(f"  [ERROR] {file_name}: {exc}")
            results.append([file_name, f"ERROR: {exc}", "", ""])
            continue

        transcript = output.get("text", "").strip()
        processing_time = f"{elapsed:.2f}"
        total_time += elapsed

        results.append([file_name, transcript, "", processing_time])

        if tqdm is None:
            print(f"  ✓ {file_name}  ({processing_time}s)")

    # ------------------------------------------------------------------
    # 5. Write CSV
    # ------------------------------------------------------------------
    try:
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)
            writer.writerows(results)
    except OSError as exc:
        print(f"\n[ERROR] Could not write CSV: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 6. Summary
    # ------------------------------------------------------------------
    success_count = sum(1 for r in results if not r[1].startswith("ERROR"))
    print()
    print("-" * 65)
    print(f"  Done!  Transcribed: {success_count}/{len(wav_files)} files")
    print(f"  Total processing time : {total_time:.2f}s")
    print(f"  Output saved to       : {OUTPUT_CSV}")
    print("-" * 65)


if __name__ == "__main__":
    main()
