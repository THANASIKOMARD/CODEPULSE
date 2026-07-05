"""Combine per-file metrics into a ranked hotspot report.

The core signal is `score = churn × complexity`: a file that is BOTH complex
and frequently changed is where bugs and rework concentrate. Complex-but-stable
code is fine (don't touch it); simple-but-churny code is fine (easy to change).
The product isolates the dangerous quadrant — both axes high.
"""
from __future__ import annotations

from dataclasses import dataclass

from .git_analysis import get_commits, compute_churn, find_repo_root
from .complexity import file_complexity


@dataclass
class FileReport:
    path: str
    commits: int
    added: int
    removed: int
    complexity: int
    lines: int
    score: int          # churn × complexity — the core hotspot signal


def build_report(repo: str = ".", since: str = "90.days") -> list[FileReport]:
    root = find_repo_root(repo)
    commits = get_commits(str(root), since=since)
    churn = compute_churn(commits)

    reports: list[FileReport] = []
    for path, stat in churn.items():
        result = file_complexity(root / path)      # None if deleted/binary
        complexity, lines = result if result is not None else (0, 0)
        reports.append(
            FileReport(
                path=path,
                commits=stat.commits,
                added=stat.added,
                removed=stat.removed,
                complexity=complexity,
                lines=lines,
                score=stat.commits * complexity,
            )
        )
    reports.sort(key=lambda r: r.score, reverse=True)
    return reports