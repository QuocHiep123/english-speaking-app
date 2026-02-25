#!/usr/bin/env python
# =============================================================================
# Data Preparation Script
# =============================================================================
"""
Prepare datasets for pronunciation model training.

Supports:
- VIVOS dataset (Vietnamese read speech)
- LibriSpeech (English reference)
- Custom pronunciation datasets

Usage:
    python data_prep.py --dataset vivos --output data/processed
"""

import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
import json

import pandas as pd
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_vivos_dataset(
    raw_path: Path,
    output_path: Path,
    split_ratio: tuple = (0.8, 0.1, 0.1),
) -> Dict[str, int]:
    """
    Prepare VIVOS dataset for training.
    
    VIVOS is a Vietnamese read speech corpus, useful for:
    - Understanding Vietnamese phonetic patterns
    - Identifying L1 interference in English pronunciation
    
    Args:
        raw_path: Path to raw VIVOS data
        output_path: Output directory
        split_ratio: Train/val/test split ratios
        
    Returns:
        Dictionary with split sizes
    """
    logger.info(f"Preparing VIVOS dataset from {raw_path}")
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load transcripts
    prompts_file = raw_path / "prompts.txt"
    
    if not prompts_file.exists():
        logger.warning(f"VIVOS prompts file not found at {prompts_file}")
        logger.info("Creating sample manifest for demonstration...")
        
        # Create sample manifest
        sample_manifest = [
            {
                "audio_path": "sample_001.wav",
                "text": "Hello, how are you today?",
                "speaker_id": "speaker_001",
                "duration": 2.5,
            },
            {
                "audio_path": "sample_002.wav",
                "text": "Nice to meet you.",
                "speaker_id": "speaker_001",
                "duration": 1.8,
            },
        ]
        
        manifest_path = output_path / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(sample_manifest, f, indent=2)
        
        return {"train": 0, "val": 0, "test": 0}
    
    # Process actual VIVOS data
    data = []
    with open(prompts_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(" ", 1)
            if len(parts) == 2:
                audio_id, text = parts
                data.append({
                    "audio_id": audio_id,
                    "text": text,
                    "audio_path": f"{audio_id}.wav",
                })
    
    df = pd.DataFrame(data)
    logger.info(f"Loaded {len(df)} samples from VIVOS")
    
    # Split data
    train_size = int(len(df) * split_ratio[0])
    val_size = int(len(df) * split_ratio[1])
    
    df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    train_df = df_shuffled[:train_size]
    val_df = df_shuffled[train_size:train_size + val_size]
    test_df = df_shuffled[train_size + val_size:]
    
    # Save splits
    for name, split_df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        split_path = output_path / name
        split_path.mkdir(exist_ok=True)
        split_df.to_json(split_path / "manifest.json", orient="records", indent=2)
    
    return {
        "train": len(train_df),
        "val": len(val_df),
        "test": len(test_df),
    }


def extract_phonemes(text: str) -> List[str]:
    """
    Extract phonemes from text using G2P.
    
    Args:
        text: Input text
        
    Returns:
        List of phonemes (CMU format)
    """
    try:
        from g2p_en import G2p
        g2p = G2p()
        phonemes = g2p(text)
        return [p for p in phonemes if p.strip()]
    except ImportError:
        logger.warning("g2p_en not installed, returning empty phonemes")
        return []


def generate_pronunciation_labels(
    manifest_path: Path,
    output_path: Path,
) -> None:
    """
    Generate phoneme-level labels for pronunciation scoring.
    
    Args:
        manifest_path: Path to manifest JSON
        output_path: Output path for labeled data
    """
    logger.info(f"Generating pronunciation labels from {manifest_path}")
    
    with open(manifest_path, "r") as f:
        data = json.load(f)
    
    labeled_data = []
    for item in tqdm(data, desc="Generating phonemes"):
        phonemes = extract_phonemes(item["text"])
        labeled_data.append({
            **item,
            "phonemes": phonemes,
            "num_phonemes": len(phonemes),
        })
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(labeled_data, f, indent=2)
    
    logger.info(f"Saved labeled data to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Prepare datasets for training")
    parser.add_argument(
        "--dataset",
        type=str,
        default="vivos",
        choices=["vivos", "librispeech", "custom"],
        help="Dataset to prepare",
    )
    parser.add_argument(
        "--raw-path",
        type=Path,
        default=Path("data/raw"),
        help="Path to raw data",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed"),
        help="Output directory",
    )
    
    args = parser.parse_args()
    
    logger.info(f"Preparing {args.dataset} dataset")
    
    if args.dataset == "vivos":
        stats = prepare_vivos_dataset(
            raw_path=args.raw_path / "vivos",
            output_path=args.output / "vivos",
        )
    else:
        logger.error(f"Dataset {args.dataset} not yet implemented")
        return
    
    logger.info(f"Dataset preparation complete: {stats}")


if __name__ == "__main__":
    main()
