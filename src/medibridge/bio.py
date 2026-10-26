"""Conversion of character spans to token-level BIO tags (for token-classification models)."""

from __future__ import annotations

from medibridge.spans import Span
from medibridge.text import tokenize


def to_bio(text: str, spans: list[Span]) -> list[tuple[str, str]]:
    """Tag each token: `B-<type>` for the first token of a span, `I-<type>` inside it, else `O`.

    A token is tagged only if it lies completely inside a span (see `unaligned_spans`).
    """
    tagged = []
    opened: set[int] = set()
    for token in tokenize(text):
        tag = "O"
        for i, span in enumerate(spans):
            if span["start"] <= token.start and token.end <= span["end"]:
                tag = ("I-" if i in opened else "B-") + span["type"]
                opened.add(i)
                break
        tagged.append((token.text, tag))
    return tagged


def unaligned_spans(text: str, spans: list[Span]) -> list[Span]:
    """Spans whose start or end falls inside a token, so BIO tags cannot represent them exactly."""
    tokens = tokenize(text)
    starts = {t.start for t in tokens}
    ends = {t.end for t in tokens}
    return [s for s in spans if s["start"] not in starts or s["end"] not in ends]
