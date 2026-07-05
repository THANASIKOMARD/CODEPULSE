"""Knowledge-risk (bus factor) analysis for codepulse.

A file changed almost entirely by one person is fragile: if they leave, nobody
understands it. We measure how many distinct authors touch each file and how
concentrated the changes are in the top contributor.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass
class Knowledge:
    authors: dict[str, Counter]   # file -> Counter(author -> commits touching it)

    def num_authors(self, path: str) -> int:
        return len(self.authors.get(path, ()))

    def primary_share(self, path: str) -> float:
        """Fraction of changes made by the single top contributor (0.0-1.0)."""
        counter = self.authors.get(path)
        if not counter:
            return 0.0
        total = sum(counter.values())
        return counter.most_common(1)[0][1] / total

    def is_bus_factor_risk(self, path: str, threshold: float = 0.8) -> bool:
        n = self.num_authors(path)
        return n == 1 or (n > 0 and self.primary_share(path) >= threshold)


def compute_knowledge(commits) -> Knowledge:
    authors: dict[str, Counter] = {}
    for commit in commits:
        for fc in commit.files:
            authors.setdefault(fc.path, Counter())[commit.author] += 1
    return Knowledge(authors=authors)