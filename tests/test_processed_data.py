"""Integrity checks on the committed data/processed/ files (no raw data needed)."""

import pandas as pd
import pytest

from medibridge.config import PROCESSED_DIR, SPLITS, SUBSETS
from medibridge.io import load_all_splits, split_path
from medibridge.split import leakage_report

pytestmark = pytest.mark.skipif(
    not split_path("hi", "train").exists(), reason="processed data not generated"
)


@pytest.fixture(scope="module", params=SUBSETS)
def processed(request) -> pd.DataFrame:
    return load_all_splits(request.param, PROCESSED_DIR)


def test_every_span_matches_its_text(processed):
    for text, entities, nested in zip(
        processed.text, processed.entities, processed.nested_entities
    ):
        for span in entities + nested:
            assert text[span["start"] : span["end"]] == span["text"]


def test_main_entities_do_not_overlap(processed):
    for entities in processed.entities:
        for a, b in zip(entities, entities[1:]):
            assert a["end"] <= b["start"]


def test_no_leakage_between_splits(processed):
    report = leakage_report(processed)
    assert all(n == 0 for pairs in report.values() for n in pairs.values()), report


def test_each_row_in_exactly_one_split(processed):
    assert processed["id"].is_unique
    assert set(processed["split"]) == set(SPLITS)


def test_no_duplicate_transcripts(processed):
    assert not processed["text"].str.lower().duplicated().any()
