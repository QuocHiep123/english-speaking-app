#!/usr/bin/env python
# =============================================================================
# L2-ARCTIC Dataset — Exploratory Data Analysis (EDA)
# =============================================================================
"""
Scan the L2-ARCTIC dataset stored under ai-core/data/raw/ and produce a
per-speaker summary table including audio count, transcript count, total
duration (minutes), and sample rate.

Usage:
    python ai-core/scripts/explore_l2_arctic.py
"""

import sys
from pathlib import Path
from typing import Dict, List, NamedTuple

import soundfile as sf
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Paths (resolved relative to *this* script → ai-core/scripts/)
# ---------------------------------------------------------------------------
SCRIPT_DIR: Path = Path(__file__).resolve().parent
AI_CORE_DIR: Path = SCRIPT_DIR.parent
DATA_RAW_DIR: Path = AI_CORE_DIR / "data" / "raw"

# Subfolders that are known *not* to be L2-ARCTIC speakers
_EXCLUDE_DIRS: set[str] = {"custom_baseline"}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
class SpeakerStats(NamedTuple):
    """Statistics for a single L2-ARCTIC speaker."""
    name: str
    num_audio: int
    num_text: int
    total_duration_min: float
    sample_rates: set[int]


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------
def analyse_speaker(speaker_dir: Path) -> SpeakerStats:
    """Compute statistics for one speaker directory.

    Args:
        speaker_dir: Path to a speaker folder containing wav/ and transcript/.

    Returns:
        A SpeakerStats named-tuple with the collected metrics.
    """
    wav_dir: Path = speaker_dir / "wav"
    txt_dir: Path = speaker_dir / "transcript"

    wav_files: List[Path] = sorted(wav_dir.glob("*.wav")) if wav_dir.is_dir() else []
    txt_files: List[Path] = sorted(txt_dir.glob("*.txt")) if txt_dir.is_dir() else []

    total_seconds: float = 0.0
    sample_rates: set[int] = set()

    for wav_path in tqdm(wav_files, desc=f"  {speaker_dir.name}", unit="file", leave=False):
        info: sf.SoundFile = sf.SoundFile(str(wav_path))
        sr: int = info.samplerate
        frames: int = info.frames
        sample_rates.add(sr)
        total_seconds += frames / sr

    return SpeakerStats(
        name=speaker_dir.name,
        num_audio=len(wav_files),
        num_text=len(txt_files),
        total_duration_min=round(total_seconds / 60, 2),
        sample_rates=sample_rates,
    )


def discover_speakers(root: Path) -> List[Path]:
    """Return sorted list of speaker directories under *root*.

    A directory qualifies as a speaker folder if it contains a ``wav/``
    subdirectory and is not in the exclusion list.
    """
    speakers: List[Path] = [
        d for d in sorted(root.iterdir())
        if d.is_dir()
        and d.name not in _EXCLUDE_DIRS
        and (d / "wav").is_dir()
    ]
    return speakers


# ---------------------------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------------------------
def print_summary(stats_list: List[SpeakerStats]) -> None:
    """Print a neat summary table to stdout."""
    header: str = (
        f"{'Speaker':<10} {'Audio':>7} {'Text':>7} "
        f"{'Duration (min)':>16} {'Sample Rate':>14}"
    )
    sep: str = "-" * len(header)

    print("\n" + sep)
    print("  L2-ARCTIC Dataset — EDA Summary")
    print(sep)
    print(header)
    print(sep)

    total_audio: int = 0
    total_text: int = 0
    total_duration: float = 0.0

    for s in stats_list:
        sr_str: str = ", ".join(f"{r} Hz" for r in sorted(s.sample_rates))
        print(
            f"{s.name:<10} {s.num_audio:>7} {s.num_text:>7} "
            f"{s.total_duration_min:>16.2f} {sr_str:>14}"
        )
        total_audio += s.num_audio
        total_text += s.num_text
        total_duration += s.total_duration_min

    print(sep)
    print(
        f"{'TOTAL':<10} {total_audio:>7} {total_text:>7} "
        f"{total_duration:>16.2f}"
    )
    print(sep + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    if not DATA_RAW_DIR.is_dir():
        print(f"[ERROR] Data directory not found: {DATA_RAW_DIR}", file=sys.stderr)
        sys.exit(1)

    speakers: List[Path] = discover_speakers(DATA_RAW_DIR)
    if not speakers:
        print(f"[WARNING] No speaker directories found in {DATA_RAW_DIR}", file=sys.stderr)
        sys.exit(0)

    print(f"Found {len(speakers)} speaker(s): {[s.name for s in speakers]}")

    stats_list: List[SpeakerStats] = []
    for speaker_dir in speakers:
        stats: SpeakerStats = analyse_speaker(speaker_dir)
        stats_list.append(stats)

    print_summary(stats_list)


if __name__ == "__main__":
    main()
