"""Leak-free, stratified train / validation / test split.

1. **Leak groups.** Rows that share a `session_id` or a normalised transcript are joined into
   one group (union-find). A group is never divided between splits.
2. **Stratification.** Each group belongs to the stratum of its most common recording context.
3. **Assignment.** Within a stratum, groups are placed largest first (ties in random order,
   fixed seed) into the split that is furthest below its target share.
"""

from __future__ import annotations

import random
import re
from collections.abc import Iterable

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from medibridge.config import SPLIT_RATIOS, SPLIT_SEED, SPLITS


def normalise_for_matching(text: str) -> str:
    """Lower-case and drop punctuation, so near-identical transcripts compare equal."""
    return re.sub(r"\W+", " ", text.lower()).strip()


def leak_groups(frame: pd.DataFrame) -> pd.Series:
    """Group id per row: connected components over shared session_id or normalised text."""
    groups = _UnionFind(len(frame))
    for keys in (frame["session_id"], frame["text"].map(normalise_for_matching)):
        groups.union_equal_keys(keys)
    return pd.Series([groups.find(i) for i in range(len(frame))], index=frame.index, name="group")


def assign_splits(
    frame: pd.DataFrame, ratios: dict[str, float] = SPLIT_RATIOS, seed: int = SPLIT_SEED
) -> pd.Series:
    """Split name for every row of `frame` (needs `session_id`, `text` and `context` columns)."""
    group = leak_groups(frame)
    groups = pd.DataFrame({"group": group, "context": frame["context"]}).groupby("group")
    group_info = groups.agg(size=("context", "size"), context=("context", _most_common))

    rng = random.Random(seed)
    split_of_group: dict[int, str] = {}
    for _, stratum in group_info.groupby("context"):
        order = list(stratum.index)
        rng.shuffle(order)  # random order among groups of equal size...
        order.sort(key=lambda gid: -stratum.at[gid, "size"])  # ...largest first (stable sort)

        target_size = {s: ratios[s] * stratum["size"].sum() for s in SPLITS}
        filled = dict.fromkeys(SPLITS, 0)
        for gid in order:
            split = max(SPLITS, key=lambda s: target_size[s] - filled[s])
            split_of_group[gid] = split
            filled[split] += stratum.at[gid, "size"]
    return group.map(split_of_group).rename("split")


def leakage_report(frame: pd.DataFrame, split_col: str = "split") -> dict[str, dict[str, int]]:
    """Number of shared sessions / exact texts / normalised texts for every pair of splits."""
    keys = {
        "session_id": frame["session_id"],
        "exact_text": frame["text"],
        "normalised_text": frame["text"].map(normalise_for_matching),
    }
    report = {}
    for name, key in keys.items():
        values = {s: set(key[frame[split_col] == s]) for s in SPLITS}
        report[name] = {f"{a}-{b}": len(values[a] & values[b]) for a, b in _pairs(SPLITS)}
    return report


def type_distribution_test(
    frame: pd.DataFrame, split_col: str = "split"
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Chi-square test that entity-type proportions are the same in every split.

    Returns:
        (split x type contingency table, {"chi2", "dof", "p_value", "cramers_v"})
    """
    pairs = [(row[split_col], s["type"]) for _, row in frame.iterrows() for s in row["entities"]]
    split_names, types = zip(*pairs)
    table = pd.crosstab(pd.Series(split_names, name="split"), pd.Series(types, name="type"))
    chi2, p_value, dof, _ = chi2_contingency(table)
    return table, {
        "chi2": round(float(chi2), 3),
        "dof": int(dof),
        "p_value": round(float(p_value), 4),
        "cramers_v": round(cramers_v(table), 4),
    }


def cramers_v(table: pd.DataFrame) -> float:
    """Effect size for a contingency table: 0 = no association, 1 = perfect association."""
    chi2 = chi2_contingency(table)[0]
    return float(np.sqrt(chi2 / (table.to_numpy().sum() * (min(table.shape) - 1))))


def _most_common(values: pd.Series) -> str:
    return values.mode().iloc[0]


def _pairs(items: Iterable[str]) -> list[tuple[str, str]]:
    items = list(items)
    return [(a, b) for i, a in enumerate(items) for b in items[i + 1 :]]


class _UnionFind:
    """Disjoint sets over row positions 0..n-1."""

    def __init__(self, n: int) -> None:
        self._parent = list(range(n))

    def find(self, i: int) -> int:
        while self._parent[i] != i:
            self._parent[i] = self._parent[self._parent[i]]  # path halving
            i = self._parent[i]
        return i

    def union_equal_keys(self, keys: Iterable[object]) -> None:
        """Join every row with the first earlier row that has the same key."""
        first_row_with_key: dict[object, int] = {}
        for i, key in enumerate(keys):
            if key in first_row_with_key:
                self._parent[self.find(i)] = self.find(first_row_with_key[key])
            else:
                first_row_with_key[key] = i
