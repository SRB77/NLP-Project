"""Entity spans: parsing, validation, overlap resolution and offset shifting.

A span is a plain dict (so it serialises straight to JSON) with the keys of `Span`:
character offsets `start` (inclusive) and `end` (exclusive) into the transcript, the surface
`text` (always equal to `transcript[start:end]`) and the entity `type`.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import TypedDict


class Span(TypedDict):
    start: int
    end: int
    text: str
    type: str


class SpanError(ValueError):
    """A span does not match the text it points into."""


def parse_entities(raw: str | None) -> list[Span]:
    """Parse the dataset's `[[text, type, [[start, end], ...]], ...]` string into spans.

    An entity mentioned several times becomes one span per occurrence. Spans are sorted by
    start, longest first.
    """
    spans: list[Span] = []
    for text, entity_type, offsets in json.loads(raw) if raw else []:
        for start, end in offsets:
            spans.append(Span(start=int(start), end=int(end), text=text, type=entity_type))
    return sorted(spans, key=lambda s: (s["start"], -s["end"]))


def validate_spans(text: str, spans: Iterable[Span]) -> None:
    """Raise SpanError unless every span is non-empty, inside `text` and matches its surface."""
    for span in spans:
        in_bounds = 0 <= span["start"] < span["end"] <= len(text)
        if not in_bounds or text[span["start"] : span["end"]] != span["text"]:
            raise SpanError(f"span {span} does not match text {text!r}")


def overlaps(a: Span, b: Span) -> bool:
    return a["start"] < b["end"] and b["start"] < a["end"]


def resolve_overlaps(spans: Iterable[Span]) -> tuple[list[Span], list[Span]]:
    """Flatten nested annotations so the main spans never overlap.

    The longest of any overlapping spans is kept. Shorter spans that overlap it are returned
    separately as `nested` so no annotation is lost; exact repeats of a kept span are dropped.

    Returns:
        (kept, nested), both sorted by start offset.
    """
    kept: list[Span] = []
    nested: list[Span] = []
    for span in sorted(spans, key=lambda s: (s["start"] - s["end"], s["start"])):
        clashes = [k for k in kept if overlaps(span, k)]
        if not clashes:
            kept.append(span)
        elif not any(_same_annotation(span, k) for k in clashes):
            nested.append(span)
    return sorted(kept, key=_by_start), sorted(nested, key=_by_start)


def shift_spans(spans: Iterable[Span], from_offset: int, delta: int) -> None:
    """In place: move every span starting at or after `from_offset` by `delta` characters."""
    for span in spans:
        if span["start"] >= from_offset:
            span["start"] += delta
            span["end"] += delta


def _same_annotation(a: Span, b: Span) -> bool:
    return (a["start"], a["end"], a["type"]) == (b["start"], b["end"], b["type"])


def _by_start(span: Span) -> int:
    return span["start"]
