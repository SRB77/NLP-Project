"""Text utilities for Hindi-English (Hinglish) transcripts.

- `tokenize`: offset-preserving tokenizer that keeps Devanagari words whole.
- `token_script` / `code_mixing_index`: script tagging and the Code-Mixing Index.
- `normalize_text`: Unicode and whitespace normalisation that remaps entity offsets.
"""

from __future__ import annotations

import re
import unicodedata
from typing import NamedTuple

from medibridge.spans import Span

# Devanagari letters, vowel signs and digits: U+0900–U+097F without the danda (।) and
# double danda (॥), which are punctuation.
_DEVANAGARI = "\u0900-\u0963\u0966-\u097f"
_ZWNJ_ZWJ = "\u200c\u200d"  # zero-width non-joiner and joiner

# Python's \w misses Devanagari vowel signs and the virama, so they are added explicitly.
# A token is a run of word characters, or a single punctuation character.
_TOKEN_RE = re.compile(rf"[\w{_DEVANAGARI}{_ZWNJ_ZWJ}]+|[^\w\s{_DEVANAGARI}]")
_DEVANAGARI_RE = re.compile(rf"[{_DEVANAGARI}]")
_LATIN_RE = re.compile(r"[A-Za-z]")
_NUMBER_RE = re.compile(r"^[0-9\u0966-\u096f.,/%]+$")  # Latin and Devanagari digits

# Removed during normalisation. ZWJ/ZWNJ are kept because they change Devanagari rendering.
_ZERO_WIDTH = frozenset({"\u200b", "\ufeff", "\u2060"})  # ZW space, BOM, word joiner
_PUNCTUATION_MAP = {
    "\u201c": '"',  # left double quotation mark
    "\u201d": '"',  # right double quotation mark
    "\u2018": "'",  # left single quotation mark
    "\u2019": "'",  # right single quotation mark
    "\u0965": "\u0964\u0964",  # double danda -> two dandas
}


class Token(NamedTuple):
    text: str
    start: int
    end: int


def tokenize(text: str) -> list[Token]:
    """Split on whitespace and punctuation, keeping character offsets into `text`."""
    return [Token(m.group(), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]


def token_script(token: str) -> str:
    """Script of a token: 'dev', 'lat', 'mixed', 'num' or 'other' (punctuation, symbols)."""
    if _NUMBER_RE.match(token):
        return "num"
    has_devanagari = bool(_DEVANAGARI_RE.search(token))
    has_latin = bool(_LATIN_RE.search(token))
    if has_devanagari and has_latin:
        return "mixed"
    if has_devanagari:
        return "dev"
    if has_latin:
        return "lat"
    return "other"


def code_mixing_index(tokens: list[str]) -> float:
    """Code-Mixing Index (Das & Gambäck, 2014) using script as the language tag.

    CMI = 100 * (1 - max_language_tokens / language_tokens): 0 for monolingual text, up to 50
    when two languages are mixed equally. Numbers and punctuation are language-independent and
    ignored. English words written in Devanagari count as Hindi, so this is a lower bound.
    """
    scripts = [token_script(t) for t in tokens]
    devanagari, latin = scripts.count("dev"), scripts.count("lat")
    if devanagari + latin == 0:
        return 0.0
    return 100.0 * (1 - max(devanagari, latin) / (devanagari + latin))


def normalize_text(text: str, spans: list[Span]) -> tuple[str, list[Span]]:
    """Normalise `text` and return it with `spans` remapped to the new offsets.

    1. Unicode NFC, zero-width removal and punctuation mapping. NFC also decomposes
       precomposed nukta letters (e.g. U+095B ज़ -> ज + ़), so both spellings become identical.
    2. Runs of whitespace collapse to a single space and the ends are stripped.
    """
    text, spans = _normalize_characters(text, spans)
    return _collapse_whitespace(text, spans)


def _normalize_characters(text: str, spans: list[Span]) -> tuple[str, list[Span]]:
    """Character-level normalisation that never moves a span boundary into the wrong place.

    The text is cut at every span boundary and each segment is normalised on its own, so a
    change in length inside one segment only shifts the boundaries after it.
    """
    boundaries = sorted({0, len(text), *(s["start"] for s in spans), *(s["end"] for s in spans)})
    new_offset = {}
    segments = []
    position = 0
    for seg_start, seg_end in zip(boundaries, boundaries[1:]):
        new_offset[seg_start] = position
        segment = _normalize_segment(text[seg_start:seg_end])
        segments.append(segment)
        position += len(segment)
    new_offset[boundaries[-1]] = position

    remapped = [{**s, "start": new_offset[s["start"]], "end": new_offset[s["end"]]} for s in spans]
    return "".join(segments), remapped


def _normalize_segment(segment: str) -> str:
    segment = unicodedata.normalize("NFC", segment)
    return "".join(_PUNCTUATION_MAP.get(ch, ch) for ch in segment if ch not in _ZERO_WIDTH)


def _collapse_whitespace(text: str, spans: list[Span]) -> tuple[str, list[Span]]:
    """Collapse whitespace runs to one space, strip the ends, and remap the span offsets."""
    kept_chars: list[str] = []
    new_index: list[int] = []  # new_index[i] = position of old character i in the output
    for i, ch in enumerate(text):
        new_index.append(len(kept_chars))
        if not ch.isspace():
            kept_chars.append(ch)
        elif i == 0 or not text[i - 1].isspace():
            kept_chars.append(" ")
    new_index.append(len(kept_chars))

    collapsed = "".join(kept_chars)
    leading = len(collapsed) - len(collapsed.lstrip())
    result = collapsed.strip()

    remapped = []
    for span in spans:
        start, end = new_index[span["start"]] - leading, new_index[span["end"]] - leading
        start, end = _trim_whitespace(result, start, end)
        remapped.append({**span, "start": start, "end": end, "text": result[start:end]})
    return result, remapped


def _trim_whitespace(text: str, start: int, end: int) -> tuple[int, int]:
    """Shrink [start, end) so it neither starts nor ends with whitespace."""
    surface = text[start:end]
    return start + len(surface) - len(surface.lstrip()), end - (
        len(surface) - len(surface.rstrip())
    )
