"""Complexity metrics for codepulse (design stub — implementation TODO).

Goal: give each file a size/complexity number to multiply with churn.

Planned approach (simple first, refine later):
  * v1: non-blank, non-comment lines of code (LOC) — language-agnostic, cheap.
  * v2: indentation-based complexity (avg/max indent depth) as a proxy for
        nesting — correlates with cyclomatic complexity without a full parser.
  * v3 (optional): real cyclomatic complexity per language via a parser.

Hotspot score (next milestone):
    hotspot = churn_commits * complexity
  High on BOTH axes = the file worth refactoring first.
"""


def loc(path: str) -> int:
    """TODO: count non-blank, non-comment lines of code in `path`."""
    raise NotImplementedError