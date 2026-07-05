"""Co-change coupling analysis for codepulse.

Files that repeatedly change together in the same commit are 'temporally
coupled' — a hidden dependency the folder structure doesn't show. A file
coupled to many others is central: touching it ripples across the codebase.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations

MAX_GROUP = 30    # skip commits touching more files than this (bulk moves = noise)
MIN_SHARED = 2    # a pair must co-change at least this often to count as coupled


@dataclass
class Coupling:
    pair_counts: dict[frozenset, int]   # {a, b} -> times they changed together
    links: dict[str, int]               # file -> how many files it's coupled to


def compute_coupling(groups, max_group=MAX_GROUP, min_shared=MIN_SHARED) -> Coupling:
    pair_counts: Counter = Counter()
    for files in groups:
        # need >= 2 files to form a pair; skip giant commits (vendoring, bulk rename)
        if not (2 <= len(files) <= max_group):
            continue
        for a, b in combinations(sorted(files), 2):
            pair_counts[frozenset((a, b))] += 1

    links: dict[str, int] = {}
    for pair, count in pair_counts.items():
        if count < min_shared:
            continue
        for f in pair:
            links[f] = links.get(f, 0) + 1
    return Coupling(pair_counts=dict(pair_counts), links=links)


def top_pairs(coupling: Coupling, n=10, min_shared=MIN_SHARED):
    """Strongest couplings, for display: [((a, b), count), ...] sorted desc."""
    pairs = [(tuple(sorted(p)), c) for p, c in coupling.pair_counts.items() if c >= min_shared]
    pairs.sort(key=lambda x: x[1], reverse=True)
    return pairs[:n]