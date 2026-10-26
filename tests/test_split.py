import pandas as pd

from medibridge.config import SPLITS
from medibridge.split import assign_splits, leak_groups, leakage_report


def _toy_frame(n_sessions: int = 60) -> pd.DataFrame:
    """Sessions of 1-3 rows, two contexts, plus duplicate texts across different sessions."""
    rows = []
    for s in range(n_sessions):
        context = "conversation" if s % 3 == 0 else "narration_sentence"
        for k in range(1 + s % 3):
            rows.append({"session_id": f"s{s}", "text": f"note {s}-{k}", "context": context})
    rows.append({"session_id": "dup-a", "text": "Same text!", "context": "narration_sentence"})
    rows.append({"session_id": "dup-b", "text": "same text", "context": "narration_sentence"})
    return pd.DataFrame(rows)


def test_leak_groups_join_sessions_and_near_duplicate_texts():
    frame = _toy_frame()
    groups = leak_groups(frame)
    assert groups[frame.session_id == "s2"].nunique() == 1
    assert groups[frame.session_id.isin(["dup-a", "dup-b"])].nunique() == 1


def test_assign_splits_is_leak_free_and_complete():
    frame = _toy_frame()
    frame["split"] = assign_splits(frame)
    assert frame["split"].notna().all()
    assert set(frame["split"]) == set(SPLITS)
    report = leakage_report(frame)
    assert all(n == 0 for pairs in report.values() for n in pairs.values()), report


def test_assign_splits_is_deterministic_and_close_to_ratios():
    frame = _toy_frame(n_sessions=300)
    first, second = assign_splits(frame), assign_splits(frame)
    assert first.equals(second)
    share = first.value_counts(normalize=True)
    assert abs(share["train"] - 0.70) < 0.03
    assert abs(share["test"] - 0.15) < 0.03
