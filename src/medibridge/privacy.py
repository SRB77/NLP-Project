"""Personal-data detection and masking for transcripts.

Two complementary checks:
- `pii_scan` finds structured identifiers (phone, e-mail, Aadhaar-like numbers, URLs).
- `mask_names` replaces names a speaker introduces ("मेरा नाम भास्कर है") with a placeholder and
  shifts entity offsets so the annotations stay valid.
"""

from __future__ import annotations

import re

from medibridge.config import NAME_MASK
from medibridge.spans import Span, overlaps, shift_spans

PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "PHONE": re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)"),  # Indian mobile
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "AADHAAR": re.compile(r"(?<!\d)\d{4}\s?\d{4}\s?\d{4}(?!\d)"),  # 12-digit ID
    "URL": re.compile(r"https?://\S+|www\.\S+"),
}

# "my name is X" in Hindi (Devanagari), Hinglish (Roman) and English; captures the name X.
_NAME_INTRODUCTION_RE = re.compile(
    r"(?:मेरा नाम\s+(?:है\s+)?|(?i:my name is\s+|mera naam\s+(?:hai\s+)?))([^\s।,.?!]+)"
)
_NOT_A_NAME = frozenset({"है", "hai"})  # the copula, captured when the name comes later


def pii_scan(text: str) -> dict[str, list[str]]:
    """Return the identifiers found in `text` as {pattern_name: [matches]}; empty if none."""
    hits = {name: pattern.findall(text) for name, pattern in PII_PATTERNS.items()}
    return {name: found for name, found in hits.items() if found}


def mask_names(
    text: str, spans: list[Span], nested: list[Span] = ()
) -> tuple[str, list[Span], list[Span], list[str]]:
    """Replace every occurrence of a self-introduced name with NAME_MASK.

    Occurrences inside an entity span are left untouched. Span offsets after each replacement
    are shifted. Inputs are not modified.

    Returns:
        (masked_text, spans, nested, sorted list of names found)
    """
    names = {
        m.group(1) for m in _NAME_INTRODUCTION_RE.finditer(text) if m.group(1) not in _NOT_A_NAME
    }
    spans = [dict(s) for s in spans]
    nested = [dict(s) for s in nested]
    all_spans = spans + nested

    occurrences = sorted(
        (m.start(), m.end()) for name in names for m in re.finditer(re.escape(name), text)
    )
    for start, end in reversed(occurrences):  # right to left, so earlier offsets stay valid
        mention = {"start": start, "end": end}
        if any(overlaps(mention, s) for s in all_spans):
            continue
        text = text[:start] + NAME_MASK + text[end:]
        shift_spans(all_spans, from_offset=end, delta=len(NAME_MASK) - (end - start))
    return text, spans, nested, sorted(names)
