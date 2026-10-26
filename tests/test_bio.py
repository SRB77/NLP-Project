from medibridge.bio import to_bio, unaligned_spans


def test_to_bio_multi_token_span(span):
    text = "Augmentin 650 mg दिया"
    tags = to_bio(text, [span(text, "Augmentin 650 mg", "drugs")])
    assert tags == [("Augmentin", "B-drugs"), ("650", "I-drugs"), ("mg", "I-drugs"), ("दिया", "O")]


def test_to_bio_adjacent_spans_each_start_with_b(span):
    text = "daily सुबह शाम"
    spans = [span(text, "daily", "advices"), span(text, "सुबह शाम", "advices")]
    assert [tag for _, tag in to_bio(text, spans)] == ["B-advices", "B-advices", "I-advices"]


def test_unaligned_spans(span):
    text = "650mg tablet"
    inside_token = span(text, "mg", "drugs")
    aligned = span(text, "tablet", "drugs")
    assert unaligned_spans(text, [inside_token, aligned]) == [inside_token]
