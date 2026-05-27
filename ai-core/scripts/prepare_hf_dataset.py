#!/usr/bin/env python
# =============================================================================
# Prepare L2-ARCTIC as a Hugging Face Dataset for Whisper Fine-Tuning
# =============================================================================
"""
Pair each .wav with its transcript, resample audio to 16 kHz,
split into train/test, and save as a HuggingFace DatasetDict.

Usage:
    python ai-core/scripts/prepare_hf_dataset.py

Output:
    ai-core/data/processed/hf_l2_arctic/   (saved DatasetDict)
"""

import sys
from pathlib import Path
from typing import Dict, List

from datasets import Audio, Dataset, DatasetDict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
AI_CORE_DIR = SCRIPT_DIR.parent
RAW_DIR = AI_CORE_DIR / "data" / "raw"
OUTPUT_DIR = AI_CORE_DIR / "data" / "processed" / "hf_l2_arctic"

SPEAKERS = ["HQTV", "PNV", "THV", "TLV"]
TARGET_SR = 16_000
TEST_SIZE = 0.1
SEED = 42


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------
def collect_pairs(speakers: List[str]) -> List[Dict[str, str]]:
    """Walk speaker dirs and pair each wav with its transcript text."""
    pairs: List[Dict[str, str]] = []
    skipped = 0

    for speaker in speakers:
        wav_dir = RAW_DIR / speaker / "wav"
        txt_dir = RAW_DIR / speaker / "transcript"

        if not wav_dir.is_dir():
            print(f"  [WARN] wav/ not found for {speaker}, skipping.")
            continue

        for wav_path in sorted(wav_dir.glob("*.wav")):
            txt_path = txt_dir / (wav_path.stem + ".txt")

            if not txt_path.exists():
                skipped += 1
                continue

            sentence = txt_path.read_text(encoding="utf-8").strip()
            if not sentence:
                skipped += 1
                continue

            pairs.append({
                "audio": str(wav_path),
                "sentence": sentence,
            })

    if skipped:
        print(f"  Skipped {skipped} files (missing transcript or empty text).")

    return pairs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 65)
    print("  Prepare L2-ARCTIC → Hugging Face Dataset")
    print("=" * 65)

    # 1. Collect audio–text pairs ----------------------------------------
    pairs = collect_pairs(SPEAKERS)
    if not pairs:
        print("[ERROR] No audio-transcript pairs found.")
        sys.exit(1)

    print(f"  Collected {len(pairs)} audio-transcript pairs.")

    # 2. Build HF Dataset ------------------------------------------------
    ds = Dataset.from_dict({
        "audio": [p["audio"] for p in pairs],
        "sentence": [p["sentence"] for p in pairs],
    })

    # 3. Cast audio column → 16 kHz -------------------------------------
    ds = ds.cast_column("audio", Audio(sampling_rate=TARGET_SR))
    print(f"  Audio column cast to {TARGET_SR} Hz.")

    # 4. Train / Test split ----------------------------------------------
    split = ds.train_test_split(test_size=TEST_SIZE, seed=SEED)
    dataset_dict = DatasetDict({
        "train": split["train"],
        "test": split["test"],
    })

    print(f"  Train : {len(dataset_dict['train']):,} samples")
    print(f"  Test  : {len(dataset_dict['test']):,} samples")

    # 5. Save to disk ----------------------------------------------------
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset_dict.save_to_disk(str(OUTPUT_DIR))

    print("-" * 65)
    print(f"  Saved to: {OUTPUT_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    main()
