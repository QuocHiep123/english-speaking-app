#!/usr/bin/env python
# =============================================================================
# Fine-Tune Whisper "small" on L2-ARCTIC Vietnamese-Accented English
# =============================================================================
"""
Fine-tune openai/whisper-small on the prepared L2-ARCTIC HuggingFace dataset
to improve STT accuracy for Vietnamese English speakers.

Prerequisites:
    - Dataset prepared at ai-core/data/processed/hf_l2_arctic/
      (run prepare_hf_dataset.py first)
    - On Intel XPU systems, set PATH before running:
        $env:PATH = "D:\\speaking_app\\.venv\\Library\\bin;" +
                     "D:\\speaking_app\\.venv\\Lib\\site-packages\\torch\\lib;" +
                     $env:PATH

Usage:
    python ai-core/scripts/train_whisper.py
"""

import sys
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Union

# Enable XPU fallback: unsupported XPU ops will execute on CPU automatically
os.environ.setdefault("PYTORCH_ENABLE_XPU_FALLBACK", "1")

import torch

# ---------------------------------------------------------------------------
# Intel XPU support — import IPEX if available so PyTorch sees the XPU device
# ---------------------------------------------------------------------------
try:
    import intel_extension_for_pytorch as ipex  # noqa: F401
    print(f"[INFO] IPEX loaded: {ipex.__version__}")
except ImportError:
    pass  # XPU may still work via native PyTorch XPU support

import numpy as np
from datasets import Dataset, DatasetDict, load_from_disk
from jiwer import wer as compute_wer
from transformers import (
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    WhisperForConditionalGeneration,
    WhisperProcessor,
)
from collections.abc import Mapping


# ---------------------------------------------------------------------------
# XPU-aware Trainer  (transformers 4.37 does not know about XPU)
# ---------------------------------------------------------------------------
class XPUSeq2SeqTrainer(Seq2SeqTrainer):
    """Override input/output handling so every tensor flows through XPU."""

    def __init__(self, *args, target_device: str = "xpu", **kwargs):
        super().__init__(*args, **kwargs)
        self._target_device = torch.device(target_device)

    def _prepare_input(self, data):
        if isinstance(data, Mapping):
            return type(data)({k: self._prepare_input(v) for k, v in data.items()})
        elif isinstance(data, (tuple, list)):
            return type(data)(self._prepare_input(v) for v in data)
        elif isinstance(data, torch.Tensor):
            return data.to(self._target_device)
        return data

    def training_step(self, model, inputs):
        """Run forward + backward on XPU, then move scalar loss to CPU
        so the Trainer's internal loss accumulator (which lives on CPU) works."""
        loss = super().training_step(model, inputs)
        return loss.to("cpu")

    def _save_checkpoint(self, model, trial, metrics=None):
        """Work around Windows bug: os.open(directory, O_RDONLY) raises
        PermissionError.  We wrap the parent call in a try/except and
        handle the fsync failure gracefully."""
        try:
            super()._save_checkpoint(model, trial, metrics=metrics)
        except PermissionError:
            # The checkpoint files were already written and renamed;
            # only the directory fsync failed, which is safe to skip
            # on Windows (NTFS journals metadata changes anyway).
            pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
AI_CORE_DIR = SCRIPT_DIR.parent
DATASET_DIR = AI_CORE_DIR / "data" / "processed" / "hf_l2_arctic"
OUTPUT_DIR = AI_CORE_DIR / "models" / "whisper-small-vi-accent"

MODEL_NAME = "openai/whisper-small"

# ---------------------------------------------------------------------------
# Device detection (XPU > CUDA > CPU)
# ---------------------------------------------------------------------------
if hasattr(torch, "xpu") and torch.xpu.is_available():
    DEVICE = "xpu"
    DEVICE_NAME = torch.xpu.get_device_name(0)
elif torch.cuda.is_available():
    DEVICE = "cuda"
    DEVICE_NAME = torch.cuda.get_device_name(0)
else:
    DEVICE = "cpu"
    DEVICE_NAME = "CPU"


# ---------------------------------------------------------------------------
# Data Collator
# ---------------------------------------------------------------------------
@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    """Pad input_features and labels to the longest sample in each batch."""

    processor: WhisperProcessor

    def __call__(
        self, features: List[Dict[str, Union[List[int], torch.Tensor]]]
    ) -> Dict[str, torch.Tensor]:
        # --- Pad input_features (mel spectrograms) ---
        input_features = [
            {"input_features": f["input_features"]} for f in features
        ]
        batch = self.processor.feature_extractor.pad(
            input_features, return_tensors="pt"
        )

        # --- Pad labels (token IDs) ---
        label_features = [{"input_ids": f["labels"]} for f in features]
        labels_batch = self.processor.tokenizer.pad(
            label_features, return_tensors="pt"
        )

        # Replace padding token id with -100 so the loss ignores them
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )

        # Strip the BOS token if the decoder adds it automatically
        if (labels[:, 0] == self.processor.tokenizer.bos_token_id).all().cpu().item():
            labels = labels[:, 1:]

        batch["labels"] = labels
        return batch


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 65)
    print("  Fine-Tune Whisper-Small — Vietnamese-Accented English")
    print("=" * 65)
    print(f"  Model   : {MODEL_NAME}")
    print(f"  Device  : {DEVICE} ({DEVICE_NAME})")
    print(f"  Dataset : {DATASET_DIR}")
    print("-" * 65)

    # 1. Load dataset ----------------------------------------------------
    if not DATASET_DIR.exists():
        print(f"[ERROR] Dataset not found: {DATASET_DIR}")
        print("       Run prepare_hf_dataset.py first.")
        sys.exit(1)

    raw_dataset: DatasetDict = load_from_disk(str(DATASET_DIR))
    print(f"  Train samples : {len(raw_dataset['train']):,}")
    print(f"  Test  samples : {len(raw_dataset['test']):,}")

    # --- Extract audio bytes and sentences from the Arrow table ----------
    #     (bypasses HF Audio decoder which requires torchcodec on v4.6+)
    import io
    import soundfile as sf
    import librosa

    def _extract_plain(split_ds) -> Dataset:
        """Pull audio bytes + sentences from the raw Arrow data."""
        arrow_table = split_ds.data
        audio_col = arrow_table.column("audio")
        audio_bytes = [audio_col[i].as_py()["bytes"] for i in range(len(audio_col))]
        sentences = arrow_table.column("sentence").to_pylist()
        return Dataset.from_dict({"audio_bytes": audio_bytes, "sentence": sentences})

    dataset = DatasetDict({
        "train": _extract_plain(raw_dataset["train"]),
        "test": _extract_plain(raw_dataset["test"]),
    })

    # 2. Load processor & model ------------------------------------------
    processor = WhisperProcessor.from_pretrained(MODEL_NAME)
    model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME)

    # Force English + transcribe task tokens
    model.config.forced_decoder_ids = processor.get_decoder_prompt_ids(
        language="en", task="transcribe"
    )
    model.config.suppress_tokens = []

    # 3. Prepare features via dataset.map() ------------------------------
    def prepare_dataset(batch: Dict[str, Any]) -> Dict[str, Any]:
        # Load audio from embedded bytes (avoids torchcodec + path issues)
        audio_array, sr = sf.read(io.BytesIO(batch["audio_bytes"]))
        if sr != 16000:
            audio_array = librosa.resample(audio_array, orig_sr=sr, target_sr=16000)
            sr = 16000

        # Extract mel-spectrogram input features
        batch["input_features"] = processor.feature_extractor(
            audio_array, sampling_rate=sr,
        ).input_features[0]

        # Tokenize the transcript
        batch["labels"] = processor.tokenizer(batch["sentence"]).input_ids

        return batch

    print("\n  Preparing features (this may take a while) ...")
    dataset = dataset.map(
        prepare_dataset,
        remove_columns=dataset["train"].column_names,
    )
    print("  Feature preparation complete.")

    # 4. Data collator ---------------------------------------------------
    data_collator = DataCollatorSpeechSeq2SeqWithPadding(processor=processor)

    # 5. WER metric (using jiwer directly) --------------------------------
    def compute_metrics(pred) -> Dict[str, float]:
        pred_ids = pred.predictions
        label_ids = pred.label_ids

        # Replace -100 with pad token for decoding
        label_ids[label_ids == -100] = processor.tokenizer.pad_token_id

        pred_str = processor.tokenizer.batch_decode(
            pred_ids, skip_special_tokens=True
        )
        label_str = processor.tokenizer.batch_decode(
            label_ids, skip_special_tokens=True
        )

        wer_val = 100 * compute_wer(label_str, pred_str)
        return {"wer": wer_val}

    # 6. Training arguments ----------------------------------------------
    # Intel XPU + transformers 4.37: autocast triggers unsupported dispatch
    #   paths on XPU.  Keep fp32 — the XPU fallback env var handles the rest.
    training_args = Seq2SeqTrainingArguments(
        output_dir=str(OUTPUT_DIR),
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=1e-5,
        warmup_steps=50,
        max_steps=400,
        fp16=False,
        bf16=False,
        # Disable eval during training: model.generate() OOMs on XPU.
        # We run evaluation post-training on CPU instead.
        evaluation_strategy="no",
        save_strategy="steps",
        save_steps=100,
        logging_steps=25,
        predict_with_generate=True,
        generation_max_length=225,
        report_to=["none"],
        save_total_limit=3,
        push_to_hub=False,
        dataloader_num_workers=0,  # avoid multiprocessing issues on Windows
        use_cpu=False,
    )

    # 7. Trainer ---------------------------------------------------------
    if DEVICE == "xpu":
        model = model.to("xpu")
        trainer = XPUSeq2SeqTrainer(
            model=model,
            args=training_args,
            train_dataset=dataset["train"],
            eval_dataset=dataset["test"],
            data_collator=data_collator,
            compute_metrics=compute_metrics,
            tokenizer=processor.feature_extractor,
            target_device="xpu",
        )
    else:
        trainer = Seq2SeqTrainer(
            model=model,
            args=training_args,
            train_dataset=dataset["train"],
            eval_dataset=dataset["test"],
            data_collator=data_collator,
            compute_metrics=compute_metrics,
            tokenizer=processor.feature_extractor,
        )

    # 8. Train! ----------------------------------------------------------
    print("\n" + "=" * 65)
    print("  Starting training ...")
    print("=" * 65)

    trainer.train()

    # 9. Save final model ------------------------------------------------
    trainer.save_model(str(OUTPUT_DIR))
    processor.save_pretrained(str(OUTPUT_DIR))

    print("\n" + "=" * 65)
    print(f"  Training complete. Model saved to: {OUTPUT_DIR}")
    print("=" * 65)

    # 10. Post-training evaluation on CPU --------------------------------
    #   model.generate() OOMs on XPU, so we move to CPU for eval.
    print("\n  Running post-training evaluation on CPU ...")
    model.to("cpu")
    torch.xpu.empty_cache() if hasattr(torch, "xpu") else None

    eval_args = Seq2SeqTrainingArguments(
        output_dir=str(OUTPUT_DIR / "eval_tmp"),
        per_device_eval_batch_size=4,
        predict_with_generate=True,
        generation_max_length=225,
        report_to=["none"],
        use_cpu=True,
        fp16=False,
        bf16=False,
        dataloader_num_workers=0,
    )
    eval_trainer = Seq2SeqTrainer(
        model=model,
        args=eval_args,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        tokenizer=processor.feature_extractor,
    )
    metrics = eval_trainer.evaluate(eval_dataset=dataset["test"])
    print(f"\n  Post-training WER: {metrics.get('eval_wer', 'N/A'):.2f}%")
    print("=" * 65)


if __name__ == "__main__":
    main()
