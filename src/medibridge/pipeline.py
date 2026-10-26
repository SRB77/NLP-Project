"""Data preparation pipeline: raw parquet -> cleaned, leak-free splits + reports.

Usage:
    medibridge-prepare                 # all subsets
    medibridge-prepare --subsets hi    # just one

Writes to data/processed/:
    {subset}_{split}.jsonl         one transcript per line; entities as character spans
    bio/{subset}_{split}.conll     token<TAB>BIO tag; blank line between transcripts
    cleaning_report.json           counts for every cleaning step
    split_report.json              sizes, leakage checks and representativeness per split
"""

from __future__ import annotations

import argparse
import logging
from typing import Any

import pandas as pd

from medibridge.bio import unaligned_spans
from medibridge.cleaning import clean
from medibridge.config import BIO_DIR, PROCESSED_DIR, SPLITS, SUBSETS
from medibridge.io import load_raw, split_path, write_conll, write_json, write_jsonl
from medibridge.split import assign_splits, leakage_report, type_distribution_test

logger = logging.getLogger(__name__)


def prepare_subset(subset: str) -> tuple[dict[str, int], dict[str, Any]]:
    """Clean and split one subset, write its files, and return (cleaning, split) reports."""
    cleaned, cleaning_report = clean(load_raw(subset))
    cleaning_report["spans_not_token_aligned"] = sum(
        len(unaligned_spans(text, spans)) for text, spans in zip(cleaned.text, cleaned.entities)
    )

    cleaned["split"] = assign_splits(cleaned)
    for split in SPLITS:
        part = cleaned[cleaned["split"] == split].drop(columns="split")
        write_jsonl(part, split_path(subset, split))
        write_conll(part, BIO_DIR / f"{subset}_{split}.conll")

    split_report = summarise_splits(cleaned)
    logger.info(
        "%s: %d -> %d rows, splits %s",
        subset,
        cleaning_report["input_rows"],
        cleaning_report["output_rows"],
        split_report["rows"],
    )
    return cleaning_report, split_report


def summarise_splits(frame: pd.DataFrame) -> dict[str, Any]:
    """Sizes, context mix, entity-type mix and leakage checks for a frame with a `split` column."""
    by_split = frame.groupby("split")
    type_table, type_test = type_distribution_test(frame)
    return {
        "rows": frame["split"].value_counts().reindex(SPLITS).to_dict(),
        "sessions": by_split["session_id"].nunique().reindex(SPLITS).to_dict(),
        "entities": by_split["n_entities"].sum().reindex(SPLITS).to_dict(),
        "rows_by_context": (
            frame.groupby(["split", "context"]).size().unstack(fill_value=0).reindex(SPLITS)
        ).to_dict(orient="index"),
        "entity_types": type_table.reindex(SPLITS).to_dict(orient="index"),
        "type_distribution_chi2": type_test,
        "leakage": leakage_report(frame),
    }


def run(subsets: tuple[str, ...] = SUBSETS) -> None:
    BIO_DIR.mkdir(parents=True, exist_ok=True)
    cleaning_reports, split_reports = {}, {}
    for subset in subsets:
        cleaning_reports[subset], split_reports[subset] = prepare_subset(subset)
    write_json(cleaning_reports, PROCESSED_DIR / "cleaning_report.json")
    write_json(split_reports, PROCESSED_DIR / "split_report.json")
    logger.info("wrote processed data to %s", PROCESSED_DIR)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subsets", nargs="+", choices=SUBSETS, default=list(SUBSETS))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run(tuple(args.subsets))


if __name__ == "__main__":
    main()
