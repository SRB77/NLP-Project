"""Cleaning pipeline: raw transcripts -> validated, normalised, de-duplicated records.

`clean()` is the single entry point. Each transcript goes through `_clean_row`:

    parse spans -> validate -> normalise text (offsets remapped) -> flatten nested spans
    -> mask names -> re-validate -> compute features

then the whole subset is de-duplicated and flagged. Every step is counted in the returned
report, which is saved as data/processed/cleaning_report.json.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from medibridge.config import SHORT_AUDIO_SECONDS, UNKNOWN_SPEAKER
from medibridge.privacy import mask_names, pii_scan
from medibridge.spans import parse_entities, resolve_overlaps, validate_spans
from medibridge.text import code_mixing_index, normalize_text, token_script, tokenize


@dataclass
class _RowResult:
    record: dict[str, Any]
    text_changed: bool
    names_masked: bool


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Clean one raw subset (as returned by `io.load_raw`).

    Returns:
        (cleaned frame with one row per unique transcript, report with a count for every step)

    Raises:
        SpanError: if any raw or cleaned entity span does not match its text.
    """
    report = {"input_rows": len(raw)}

    frame = raw.assign(text=raw["text"].fillna(""))
    is_empty = frame["text"].str.strip() == ""
    report["dropped_empty_text"] = int(is_empty.sum())
    frame = frame[~is_empty]

    rows = [_clean_row(row) for row in frame.itertuples(index=False)]
    cleaned = pd.DataFrame([r.record for r in rows])
    report["texts_changed_by_normalisation"] = sum(r.text_changed for r in rows)
    report["nested_spans_moved_to_nested_entities"] = int(cleaned["nested_entities"].map(len).sum())
    report["rows_with_names_masked"] = sum(r.names_masked for r in rows)
    report["spans_validated"] = int(cleaned["n_entities"].sum())

    cleaned, n_duplicates, n_conflicting = _drop_duplicate_transcripts(cleaned)
    report["dropped_duplicate_text"] = n_duplicates
    report["duplicate_groups_with_conflicting_labels"] = n_conflicting

    cleaned = _add_quality_flags(cleaned)
    for flag in ("flag_no_entities", "flag_short_audio", "flag_pii"):
        report[flag] = int(cleaned[flag].sum())
    report["speaker_unknown"] = int((cleaned["speaker"] == UNKNOWN_SPEAKER).sum())
    report["output_rows"] = len(cleaned)
    report["output_entities"] = int(cleaned["n_entities"].sum())
    return cleaned, report


def _clean_row(row: Any) -> _RowResult:
    spans = parse_entities(row.medical_entities)
    validate_spans(row.text, spans)  # the raw annotations must already be consistent

    text, spans = normalize_text(row.text, spans)
    spans, nested = resolve_overlaps(spans)
    text, spans, nested, names = mask_names(text, spans, nested)
    validate_spans(text, spans)
    validate_spans(text, nested)

    record = {
        "id": row.md5_audio,
        "subset": row.subset,
        "text": text,
        "entities": spans,
        "nested_entities": nested,
        "session_id": row.session_id,
        "speaker": row.speaker if isinstance(row.speaker, str) else UNKNOWN_SPEAKER,
        "context": row.recording_context,
        "type_concept": row.type_concept,
        "duration": round(float(row.duration), 3),
        "md5_text": row.md5_text,
        **_text_features(text, n_entities=len(spans)),
        "pii": pii_scan(text),
    }
    return _RowResult(record=record, text_changed=text != row.text, names_masked=bool(names))


def _text_features(text: str, n_entities: int) -> dict[str, Any]:
    tokens = [t.text for t in tokenize(text)]
    scripts = [token_script(t) for t in tokens]
    n_tokens = max(len(tokens), 1)
    return {
        "n_tokens": len(tokens),
        "n_entities": n_entities,
        "pct_devanagari": round(scripts.count("dev") / n_tokens, 4),
        "pct_latin": round(scripts.count("lat") / n_tokens, 4),
        "cmi": round(code_mixing_index(tokens), 2),
    }


def _drop_duplicate_transcripts(frame: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """Keep the first copy of each transcript (case-insensitive).

    Duplicates add no information for text NER and would leak between splits.

    Returns:
        (de-duplicated frame, number of rows dropped, number of duplicate groups whose copies
        were labelled differently)
    """
    key = frame["text"].str.lower()
    is_duplicate = key.duplicated(keep="first")
    label_signature = frame["entities"].map(
        lambda spans: tuple((s["start"], s["end"], s["type"]) for s in spans)
    )
    n_conflicting = int(label_signature.groupby(key).nunique().gt(1).sum())
    return frame[~is_duplicate].reset_index(drop=True), int(is_duplicate.sum()), n_conflicting


def _add_quality_flags(frame: pd.DataFrame) -> pd.DataFrame:
    """Rows are kept but flagged so modelling code can decide how to treat them."""
    return frame.assign(
        flag_no_entities=frame["n_entities"] == 0,
        flag_short_audio=frame["duration"] < SHORT_AUDIO_SECONDS,
        flag_pii=frame["pii"].map(bool),
    )
