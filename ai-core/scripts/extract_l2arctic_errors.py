#!/usr/bin/env python
# =============================================================================
# L2-ARCTIC Pronunciation Error Extraction Script
# =============================================================================
"""
Extract pronunciation errors from L2-ARCTIC TextGrid annotations
for Vietnamese speakers (HQTV, PNV, THV, TLV).

In L2-ARCTIC, the 'phones' tier uses comma-separated labels to mark errors:
  - Substitution (s): "DH,D,s"   → expected DH, produced D
  - Deletion    (d): "R,sil,d"   → expected R, produced silence
  - Addition    (a): "sil,AH0,a" → expected silence, produced AH0
  - Asterisk  (*) markers also indicate error variants

Output: ai-core/data/processed/vietnamese_errors.csv
Columns: Speaker | File_ID | Start_Time | End_Time | Error_Annotation

Usage:
    python ai-core/scripts/extract_l2arctic_errors.py
"""

import csv
import sys
from pathlib import Path
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VIETNAMESE_SPEAKERS = ["HQTV", "PNV", "THV", "TLV"]
PHONES_TIER_NAME = "phones"

# Resolve paths relative to project root (one level above ai-core/)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent                       # ai-core/
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "vietnamese_errors.csv"

CSV_HEADER = ["Speaker", "File_ID", "Start_Time", "End_Time", "Error_Annotation"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def is_error_annotation(text: str) -> bool:
    """Return True if the interval text represents a pronunciation error.

    L2-ARCTIC error conventions:
      • Comma (,) separates <expected>,<actual>,<type>  →  substitution / deletion / addition
      • Asterisk (*) marks special error variants (e.g. "AY1,AA*,s")
    """
    stripped = text.strip()
    if not stripped:
        return False
    return ("," in stripped) or ("*" in stripped)


def extract_errors_from_textgrid(
    filepath: Path,
) -> List[Tuple[float, float, str]]:
    """Parse a single TextGrid file and return a list of error intervals.

    Returns:
        List of (start_time, end_time, annotation_text) tuples.
    """
    import tgt  # lazy import so missing-lib error is caught cleanly

    tg = tgt.io.read_textgrid(str(filepath))

    # Locate the 'phones' tier
    try:
        phones_tier = tg.get_tier_by_name(PHONES_TIER_NAME)
    except ValueError:
        print(f"  [WARN] Tier '{PHONES_TIER_NAME}' not found in {filepath.name}, skipping.")
        return []

    errors: List[Tuple[float, float, str]] = []
    for interval in phones_tier:
        text = interval.text.strip()
        if is_error_annotation(text):
            errors.append((interval.start_time, interval.end_time, text))

    return errors


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 65)
    print("  L2-ARCTIC Vietnamese Pronunciation Error Extraction")
    print("=" * 65)

    # ------ Validate input directory ------
    if not RAW_DATA_DIR.exists():
        print(f"[ERROR] Raw data directory not found: {RAW_DATA_DIR}")
        sys.exit(1)

    # ------ Ensure output directory exists ------
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: List[List[str]] = []
    total_files = 0
    total_errors = 0

    for speaker in VIETNAMESE_SPEAKERS:
        annotation_dir = RAW_DATA_DIR / speaker / "annotation"

        # --- Check speaker directory ---
        if not annotation_dir.exists():
            print(f"\n[WARN] Annotation directory missing for speaker '{speaker}': "
                  f"{annotation_dir}")
            continue

        textgrid_files = sorted(annotation_dir.glob("*.TextGrid"))
        if not textgrid_files:
            print(f"\n[WARN] No .TextGrid files found for speaker '{speaker}'.")
            continue

        print(f"\n>> Speaker: {speaker}  ({len(textgrid_files)} TextGrid files)")

        speaker_error_count = 0

        for tg_path in textgrid_files:
            file_id = tg_path.stem  # e.g. "arctic_a0003"

            try:
                errors = extract_errors_from_textgrid(tg_path)
            except Exception as exc:
                print(f"  [ERROR] Failed to parse {tg_path.name}: {exc}")
                continue

            for start, end, annotation in errors:
                all_rows.append([
                    speaker,
                    file_id,
                    f"{start:.4f}",
                    f"{end:.4f}",
                    annotation,
                ])

            if errors:
                speaker_error_count += len(errors)
                total_files += 1

        total_errors += speaker_error_count
        print(f"   └─ Errors extracted: {speaker_error_count}")

    # ------ Write CSV ------
    if not all_rows:
        print("\n[INFO] No errors found across all speakers. CSV not created.")
        return

    try:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)
            writer.writerows(all_rows)
    except OSError as exc:
        print(f"\n[ERROR] Could not write output file: {exc}")
        sys.exit(1)

    print("\n" + "-" * 65)
    print(f"  Done!  Total errors: {total_errors}  |  Files with errors: {total_files}")
    print(f"  Output saved to: {OUTPUT_FILE}")
    print("-" * 65)


if __name__ == "__main__":
    main()
