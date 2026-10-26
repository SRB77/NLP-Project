"""Download the Eka Medical ASR Evaluation Dataset (MIT licence) into data/raw/.

The raw files are not committed to git. Run once after cloning:

    medibridge-download

Files are fetched from a pinned commit (config.HF_REVISION) so everyone gets identical data.
"""

from __future__ import annotations

import argparse
import json
import logging
import urllib.request
from pathlib import Path

from medibridge.config import HF_REPO, HF_REVISION, RAW_DIR, SUBSETS

logger = logging.getLogger(__name__)

_API = "https://huggingface.co/api/datasets"
_FILES = "https://huggingface.co/datasets"


def list_parquet_files(subset: str, revision: str = HF_REVISION) -> list[str]:
    """Repository paths of the parquet shards of one subset, e.g. 'hi/test-00000.parquet'."""
    with urllib.request.urlopen(f"{_API}/{HF_REPO}/tree/{revision}/{subset}") as response:
        return [f["path"] for f in json.load(response) if f["path"].endswith(".parquet")]


def download(subsets: tuple[str, ...] = SUBSETS, raw_dir: Path = RAW_DIR) -> None:
    for subset in subsets:
        (raw_dir / subset).mkdir(parents=True, exist_ok=True)
        for path in list_parquet_files(subset):
            destination = raw_dir / path
            if destination.exists():
                logger.info("already present: %s", path)
                continue
            logger.info("downloading %s", path)
            urllib.request.urlretrieve(
                f"{_FILES}/{HF_REPO}/resolve/{HF_REVISION}/{path}", destination
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the raw dataset into data/raw/.")
    parser.add_argument("--subsets", nargs="+", choices=SUBSETS, default=list(SUBSETS))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    download(tuple(args.subsets))


if __name__ == "__main__":
    main()
