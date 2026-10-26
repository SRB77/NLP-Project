"""Reading the raw dataset and reading/writing processed files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from medibridge.bio import to_bio
from medibridge.config import PROCESSED_DIR, RAW_DIR, RAW_TEXT_COLUMNS, SPLITS


def load_raw(subset: str, raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Load one raw subset ('hi' or 'en') without the audio column; adds a `subset` column."""
    files = sorted((raw_dir / subset).glob("*.parquet"))
    if not files:
        raise FileNotFoundError(
            f"No parquet files in {raw_dir / subset}. Run `medibridge-download` first."
        )
    frame = pd.concat(
        [pd.read_parquet(f, columns=RAW_TEXT_COLUMNS) for f in files], ignore_index=True
    )
    frame.insert(0, "subset", subset)
    return frame


def split_path(subset: str, split: str, processed_dir: Path = PROCESSED_DIR) -> Path:
    return processed_dir / f"{subset}_{split}.jsonl"


def load_split(subset: str, split: str, processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Load one processed split, e.g. `load_split("hi", "train")`."""
    return pd.read_json(split_path(subset, split, processed_dir), lines=True)


def load_all_splits(subset: str, processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """All splits of a subset in one frame, with a `split` column."""
    return pd.concat(
        [load_split(subset, s, processed_dir).assign(split=s) for s in SPLITS], ignore_index=True
    )


def write_jsonl(frame: pd.DataFrame, path: Path) -> None:
    frame.to_json(path, orient="records", lines=True, force_ascii=False)


def write_conll(frame: pd.DataFrame, path: Path) -> None:
    """One `token<TAB>tag` line per token, a `# id = ...` header and a blank line per transcript."""
    with open(path, "w", encoding="utf-8") as f:
        for row in frame.itertuples(index=False):
            f.write(f"# id = {row.id}\n")
            for token, tag in to_bio(row.text, row.entities):
                f.write(f"{token}\t{tag}\n")
            f.write("\n")


def write_json(obj: Any, path: Path) -> None:
    """Pretty JSON; numpy scalars are converted to plain Python numbers."""
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=_to_builtin))


def _to_builtin(value: Any) -> Any:
    return value.item() if hasattr(value, "item") else str(value)
