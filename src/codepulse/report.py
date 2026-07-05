"""Combine per-file metrics into a ranked hotspot report.

Core signal: score = churn × complexity (the dangerous quadrant).
Final ranking: roi = score × role_weight × centrality_boost — because a complex,
churny *core* file coupled to many others deserves attention before an equally
churny changelog or lock file.
"""
from __future__ import annotations

from dataclasses import dataclass

from .git_analysis import get_commits, compute_churn, find_repo_root, file_groups
from .complexity import file_complexity
from .coupling import compute_coupling
from .knowledge import compute_knowledge
from .roles import classify, role_weight

CENTRALITY_K = 10   # bounds the coupling boost to < 2x (diminishing returns)


@dataclass
class FileReport:
    path: str
    commits: int
    added: int
    removed: int
    complexity: int
    lines: int
    score: int          # churn × complexity
    role: str
    links: int
    num_authors: int
    bus_factor_risk: bool
    roi: float          # score × role_weight × centrality_boost


def _centrality_boost(links: int) -> float:
    # 1.0 when isolated, approaching 2.0 as links grow — refines, never dominates.
    return 1 + links / (links + CENTRALITY_K)


def build_report(repo: str = ".", since: str = "90.days") -> list[FileReport]:
    root = find_repo_root(repo)
    commits = get_commits(str(root), since=since)

    churn = compute_churn(commits)
    coupling = compute_coupling(file_groups(commits))
    knowledge = compute_knowledge(commits)

    reports: list[FileReport] = []
    for path, stat in churn.items():
        result = file_complexity(root / path)
        complexity, lines = result if result is not None else (0, 0)
        score = stat.commits * complexity
        role = classify(path)
        links = coupling.links.get(path, 0)
        roi = score * role_weight(role) * _centrality_boost(links)
        reports.append(
            FileReport(
                path=path,
                commits=stat.commits,
                added=stat.added,
                removed=stat.removed,
                complexity=complexity,
                lines=lines,
                score=score,
                role=role,
                links=links,
                num_authors=knowledge.num_authors(path),
                bus_factor_risk=knowledge.is_bus_factor_risk(path),
                roi=roi,
            )
        )
    reports.sort(key=lambda r: r.roi, reverse=True)
    return reports