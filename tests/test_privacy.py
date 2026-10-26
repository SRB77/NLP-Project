from medibridge.config import NAME_MASK
from medibridge.privacy import mask_names, pii_scan


def test_mask_names_replaces_every_occurrence_and_shifts_offsets(span):
    text = "मेरा नाम भास्कर है। भास्कर जी को बुखार है"
    fever = span(text, "बुखार", "clinical_findings")
    masked, (new_fever,), _, names = mask_names(text, [fever])
    assert names == ["भास्कर"]
    assert "भास्कर" not in masked
    assert masked.count(NAME_MASK) == 2
    assert masked[new_fever["start"] : new_fever["end"]] == "बुखार"


def test_mask_names_handles_name_after_copula():
    masked, _, _, names = mask_names("अह मेरा नाम है भास्कर। ओके", [])
    assert names == ["भास्कर"]
    assert masked == f"अह मेरा नाम है {NAME_MASK}। ओके"


def test_mask_names_does_not_touch_entities(span):
    text = "my name is Augmentin and Augmentin 650 mg helps"
    drug = span(text, "Augmentin 650 mg", "drugs")
    masked, (new_drug,), _, _ = mask_names(text, [drug])
    assert masked[new_drug["start"] : new_drug["end"]] == "Augmentin 650 mg"


def test_mask_names_does_not_modify_inputs(span):
    text = "my name is Ravi, fever since Monday"
    fever = span(text, "fever", "clinical_findings")
    mask_names(text, [fever])
    assert fever == span(text, "fever", "clinical_findings")


def test_pii_scan():
    assert pii_scan("call 9876543210 or mail a.b@x.com") == {
        "PHONE": ["9876543210"],
        "EMAIL": ["a.b@x.com"],
    }
    assert pii_scan("Paracetamol 650 mg twice daily") == {}
