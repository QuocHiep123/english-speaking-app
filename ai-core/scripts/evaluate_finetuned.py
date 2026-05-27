#!/usr/bin/env python
# =============================================================================
# Evaluate Fine-Tuned Whisper on Custom Baseline Audio
# =============================================================================
"""
Load the locally fine-tuned Whisper model (whisper-small-vi-accent) and
evaluate it on the 15 custom baseline audio files.  Compare WER/CER
against the zero-shot Whisper base and small results.

Prerequisites:
    - Fine-tuned model at ai-core/models/whisper-small-vi-accent/
    - custom_baseline_labels.csv   (Whisper base transcripts)
    - whisper_experiments.csv      (Whisper small transcripts)
    - Audio files in data/raw/custom_baseline/

On Intel XPU systems, set PATH before running:
    $env:PATH = "D:\\speaking_app\\.venv\\Library\\bin;" +
                 "D:\\speaking_app\\.venv\\Lib\\site-packages\\torch\\lib;" +
                 $env:PATH

Usage:
    python ai-core/scripts/evaluate_finetuned.py
"""

import csv
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

os.environ.setdefault("PYTORCH_ENABLE_XPU_FALLBACK", "1")

import librosa
import numpy as np
import torch
from jiwer import cer, wer
from transformers import WhisperForConditionalGeneration, WhisperProcessor

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
AI_CORE_DIR = SCRIPT_DIR.parent

MODEL_DIR = AI_CORE_DIR / "models" / "whisper-small-vi-accent"
AUDIO_DIR = AI_CORE_DIR / "data" / "raw" / "custom_baseline"
BASELINE_CSV = AI_CORE_DIR / "data" / "processed" / "custom_baseline_labels.csv"
EXPERIMENT_CSV = AI_CORE_DIR / "data" / "processed" / "whisper_experiments.csv"
OUTPUT_CSV = AI_CORE_DIR / "data" / "processed" / "final_evaluation.csv"

TARGET_SR = 16_000  # Whisper expects 16 kHz


# ---------------------------------------------------------------------------
# Text normalization (consistent with other eval scripts)
# ---------------------------------------------------------------------------
def normalize_text(text: str) -> str:
    """Lowercase and strip punctuation for fair WER/CER comparison."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Device selection
# ---------------------------------------------------------------------------
def select_device() -> torch.device:
    """Pick best available device: XPU > CUDA > CPU.
    For inference with generate(), XPU may OOM so we fall back to CPU."""
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        # Test if XPU has enough memory for generate() — small model ~1 GB,
        # but autoregressive decoding can spike.  Try it; fall back on OOM.
        return torch.device("xpu")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    # 1. Validate paths --------------------------------------------------
    for label, path in [
        ("Fine-tuned model", MODEL_DIR),
        ("Baseline CSV", BASELINE_CSV),
        ("Audio directory", AUDIO_DIR),
    ]:
        if not path.exists():
            print(f"[ERROR] {label} not found: {path}")
            sys.exit(1)

    # 2. Read baseline CSV (base transcripts + ground truth) -------------
    baseline_map: Dict[str, Dict[str, str]] = {}
    with open(BASELINE_CSV, "r", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            gt = row.get("ground_truth", "").strip()
            if gt and "[unintelligible]" not in gt.lower():
                baseline_map[row["file_name"]] = row

    # 3. Read experiment CSV (small transcripts) — optional --------------
    small_map: Dict[str, str] = {}
    if EXPERIMENT_CSV.exists():
        with open(EXPERIMENT_CSV, "r", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                small_map[row["file_name"]] = row.get("transcript_small", "")

    if not baseline_map:
        print("[ERROR] No valid rows in baseline CSV.")
        sys.exit(1)

    # 4. Load fine-tuned model -------------------------------------------
    device = select_device()
    print("=" * 70)
    print("  Evaluate Fine-Tuned Whisper — Custom Baseline")
    print("=" * 70)
    print(f"  Model   : {MODEL_DIR.name}")
    print(f"  Device  : {device}")
    print(f"  Samples : {len(baseline_map)}")
    print("-" * 70)

    processor = WhisperProcessor.from_pretrained(str(MODEL_DIR))
    model = WhisperForConditionalGeneration.from_pretrained(str(MODEL_DIR))
    model.eval()

    # Try XPU first; fall back to CPU if generate() OOMs
    use_cpu_fallback = False
    if device.type == "xpu":
        try:
            model = model.to(device)
        except RuntimeError:
            print("  [WARN] XPU load failed — falling back to CPU.")
            device = torch.device("cpu")
            use_cpu_fallback = True
    else:
        model = model.to(device)

    # Note: do NOT pass forced_decoder_ids manually — the fine-tuned
    # model's generation_config already has them baked in.  Passing both
    # causes a ValueError in transformers 4.37.

    # 5. Inference -------------------------------------------------------
    results: List[Dict[str, Any]] = []

    for file_name in sorted(baseline_map.keys()):
        audio_path = AUDIO_DIR / file_name
        if not audio_path.exists():
            print(f"  [SKIP] Audio not found: {audio_path}")
            continue

        row = baseline_map[file_name]
        ground_truth = row["ground_truth"]
        transcript_base = row["whisper_transcript"]
        transcript_small = small_map.get(file_name, "")

        # Load & resample audio
        audio_array, sr = librosa.load(str(audio_path), sr=TARGET_SR, mono=True)

        # Prepare features
        input_features = processor.feature_extractor(
            audio_array, sampling_rate=TARGET_SR, return_tensors="pt"
        ).input_features.to(device)

        # Generate
        start = time.perf_counter()
        try:
            with torch.no_grad():
                predicted_ids = model.generate(
                    input_features,
                    language="en",
                    task="transcribe",
                    max_length=225,
                )
        except RuntimeError as e:
            if "OUT_OF_DEVICE_MEMORY" in str(e) and device.type == "xpu":
                # Fall back to CPU for the rest of inference
                print("  [WARN] XPU OOM on generate() — switching to CPU.")
                torch.xpu.empty_cache()
                model = model.to("cpu")
                device = torch.device("cpu")
                input_features = input_features.to("cpu")
                with torch.no_grad():
                    predicted_ids = model.generate(
                        input_features,
                        language="en",
                        task="transcribe",
                        max_length=225,
                    )
            else:
                raise
        elapsed = time.perf_counter() - start

        transcript_finetuned = processor.tokenizer.decode(
            predicted_ids[0], skip_special_tokens=True
        ).strip()

        # Normalize for metrics
        gt_norm = normalize_text(ground_truth)
        base_norm = normalize_text(transcript_base)
        small_norm = normalize_text(transcript_small) if transcript_small else ""
        ft_norm = normalize_text(transcript_finetuned)

        wer_base = wer(gt_norm, base_norm)
        wer_small = wer(gt_norm, small_norm) if small_norm else None
        wer_ft = wer(gt_norm, ft_norm)

        cer_base = cer(gt_norm, base_norm)
        cer_small = cer(gt_norm, small_norm) if small_norm else None
        cer_ft = cer(gt_norm, ft_norm)

        results.append({
            "file_name": file_name,
            "ground_truth": ground_truth,
            "transcript_base": transcript_base,
            "transcript_small": transcript_small,
            "transcript_finetuned": transcript_finetuned,
            "wer_base": round(wer_base, 4),
            "wer_small": round(wer_small, 4) if wer_small is not None else "",
            "wer_finetuned": round(wer_ft, 4),
            "cer_base": round(cer_base, 4),
            "cer_small": round(cer_small, 4) if cer_small is not None else "",
            "cer_finetuned": round(cer_ft, 4),
            "processing_time_finetuned": round(elapsed, 2),
        })

        short_name = file_name[:30].ljust(30)
        ws = f"{wer_small:.2%}" if wer_small is not None else "  N/A "
        print(
            f"  {short_name}  "
            f"WER: {wer_base:.2%} → {ws} → {wer_ft:.2%}  "
            f"({elapsed:.1f}s)"
        )

    if not results:
        print("[ERROR] No files were successfully processed.")
        sys.exit(1)

    # 6. Aggregate metrics -----------------------------------------------
    n = len(results)
    all_gt = [normalize_text(r["ground_truth"]) for r in results]
    all_base = [normalize_text(r["transcript_base"]) for r in results]
    all_ft = [normalize_text(r["transcript_finetuned"]) for r in results]

    corpus_wer_base = wer(all_gt, all_base)
    corpus_cer_base = cer(all_gt, all_base)
    corpus_wer_ft = wer(all_gt, all_ft)
    corpus_cer_ft = cer(all_gt, all_ft)

    has_small = any(r["transcript_small"] for r in results)
    if has_small:
        all_small = [normalize_text(r["transcript_small"]) for r in results]
        corpus_wer_small = wer(all_gt, all_small)
        corpus_cer_small = cer(all_gt, all_small)

    print("\n" + "=" * 70)
    print("  CORPUS-LEVEL RESULTS")
    print("=" * 70)
    header = f"  {'Metric':<12} {'Base':>12} "
    if has_small:
        header += f"{'Small':>12} "
    header += f"{'Fine-Tuned':>12}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    wer_line = f"  {'WER':<12} {corpus_wer_base:>11.2%} "
    if has_small:
        wer_line += f"{corpus_wer_small:>11.2%} "
    wer_line += f"{corpus_wer_ft:>11.2%}"
    print(wer_line)

    cer_line = f"  {'CER':<12} {corpus_cer_base:>11.2%} "
    if has_small:
        cer_line += f"{corpus_cer_small:>11.2%} "
    cer_line += f"{corpus_cer_ft:>11.2%}"
    print(cer_line)

    # Relative improvement
    wer_reduction = (1 - corpus_wer_ft / corpus_wer_base) * 100 if corpus_wer_base > 0 else 0
    print(f"\n  WER reduction (base → fine-tuned): {wer_reduction:.1f}%")
    if has_small:
        wer_red_small = (1 - corpus_wer_ft / corpus_wer_small) * 100 if corpus_wer_small > 0 else 0
        print(f"  WER reduction (small → fine-tuned): {wer_red_small:.1f}%")
    print("=" * 70)

    # 7. Save CSV --------------------------------------------------------
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "file_name", "ground_truth",
        "transcript_base", "transcript_small", "transcript_finetuned",
        "wer_base", "wer_small", "wer_finetuned",
        "cer_base", "cer_small", "cer_finetuned",
        "processing_time_finetuned",
    ]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n  Results saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
