"""Project-wide paths and constants.

Everything that a teammate might want to tune (split ratios, seed, thresholds) lives here,
so behaviour can be changed in one place.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- Paths -----------------------------------------------------------------------------------
# The package is installed in editable mode (`pip install -e .`), so the repository root is two
# levels above this file. Set MEDIBRIDGE_DATA_DIR to keep data somewhere else.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("MEDIBRIDGE_DATA_DIR", PROJECT_ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
BIO_DIR = PROCESSED_DIR / "bio"

# --- Source dataset --------------------------------------------------------------------------
HF_REPO = "ekacare/eka-medical-asr-evaluation-dataset"
HF_REVISION = "433e66037c8aebb8f396b938624a5ab6afc4ca36"  # pinned commit used for M2

SUBSETS = ("hi", "en")  # hi = Hindi/Hinglish (primary), en = Indian English (auxiliary)

# Every raw column except the audio waveform: text-side work never needs the audio.
RAW_TEXT_COLUMNS = [
    "file_name",
    "duration",
    "text",
    "audio_language",
    "text_language",
    "session_id",
    "speaker",
    "type_concept",
    "recording_context",
    "medical_entities",
    "md5_text",
    "md5_audio",
]

ENTITY_TYPES = ("drugs", "clinical_findings", "diagnostics", "advices", "misc_medical")

# --- Cleaning --------------------------------------------------------------------------------
SHORT_AUDIO_SECONDS = 1.0
UNKNOWN_SPEAKER = "unknown"
NAME_MASK = "[NAME]"

# --- Splitting -------------------------------------------------------------------------------
SPLITS = ("train", "val", "test")
SPLIT_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}
SPLIT_SEED = 42
