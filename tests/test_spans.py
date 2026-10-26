import pytest

from medibridge.spans import SpanError, parse_entities, resolve_overlaps, validate_spans


def test_parse_entities_expands_repeated_mentions():
    raw = (
        '[["lab test", "diagnostics", [[10, 18], [30, 38]]],'
        ' ["fever", "clinical_findings", [[0, 5]]]]'
    )
    spans = parse_entities(raw)
    assert [(s["start"], s["text"]) for s in spans] == [
        (0, "fever"),
        (10, "lab test"),
        (30, "lab test"),
    ]


@pytest.mark.parametrize("raw", [None, "", "[]"])
def test_parse_entities_empty(raw):
    assert parse_entities(raw) == []


def test_validate_spans_rejects_mismatch():
    validate_spans("high fever", [{"start": 5, "end": 10, "text": "fever", "type": "x"}])
    with pytest.raises(SpanError):
        validate_spans("high fever", [{"start": 4, "end": 10, "text": "fever", "type": "x"}])
    with pytest.raises(SpanError):
        validate_spans("fever", [{"start": 3, "end": 3, "text": "", "type": "x"}])


def test_resolve_overlaps_keeps_longest_and_preserves_nested(span):
    text = "Augmentin 650 mg"
    outer = span(text, "Augmentin 650 mg", "drugs")
    inner = span(text, "Augmentin", "drugs")
    kept, nested = resolve_overlaps([outer, inner, dict(outer)])  # includes an exact repeat
    assert kept == [outer]
    assert nested == [inner]


def test_resolve_overlaps_leaves_disjoint_spans(span):
    text = "fever and cough"
    spans = [span(text, "fever", "clinical_findings"), span(text, "cough", "clinical_findings")]
    assert resolve_overlaps(spans) == (spans, [])
