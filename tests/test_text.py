import pytest

from medibridge.text import code_mixing_index, normalize_text, token_script, tokenize


def test_tokenizer_keeps_devanagari_words_whole():
    assert [t.text for t in tokenize("इन्फेक्शन है।")] == ["इन्फेक्शन", "है", "।"]


def test_tokenizer_offsets_point_into_text():
    text = "Augmentin 650 mg दिया।"
    for token in tokenize(text):
        assert text[token.start : token.end] == token.text


@pytest.mark.parametrize(
    ("token", "script"),
    [
        ("बुखार", "dev"),
        ("fever", "lat"),
        ("650", "num"),
        ("१२", "num"),
        ("।", "other"),
        ("CBCटेस्ट", "mixed"),
    ],
)
def test_token_script(token, script):
    assert token_script(token) == script


def test_code_mixing_index():
    assert code_mixing_index(["मुझे", "fever", "है"]) == pytest.approx(100 / 3)
    assert code_mixing_index(["मुझे", "बुखार"]) == 0
    assert code_mixing_index(["650", "।"]) == 0  # no language tokens


def test_normalisation_collapses_whitespace_and_remaps_offsets(span):
    text = "मरीज़  को\u200b  तेज़ बुखार  है "
    entity = span(text, "तेज़ बुखार", "clinical_findings")
    new_text, (new_span,) = normalize_text(text, [entity])
    assert "  " not in new_text
    assert "\u200b" not in new_text
    assert new_text == new_text.strip()
    assert new_text[new_span["start"] : new_span["end"]] == new_span["text"]


def test_normalisation_decomposes_precomposed_nukta(span):
    text = "\u095b\u0941\u0915\u093e\u092e"  # "zukaam" with precomposed ZA (U+095B)
    new_text, (new_span,) = normalize_text(text, [span(text, text, "clinical_findings")])
    assert new_text == "\u091c\u093c\u0941\u0915\u093e\u092e"  # JA + nukta (U+093C)
    assert new_span["end"] == len(new_text)


def test_normalisation_trims_whitespace_inside_span_edges():
    text = "take  rest "
    _, (new_span,) = normalize_text(
        text, [{"start": 4, "end": 11, "text": "  rest ", "type": "advices"}]
    )
    assert new_span["text"] == "rest"
