from __future__ import annotations

import pytest

from medibridge.spans import Span


def make_span(text: str, surface: str, entity_type: str, occurrence: int = 0) -> Span:
    """Build a span for the `occurrence`-th appearance of `surface` in `text`."""
    start = -1
    for _ in range(occurrence + 1):
        start = text.index(surface, start + 1)
    return Span(start=start, end=start + len(surface), text=surface, type=entity_type)


@pytest.fixture
def span():
    return make_span
