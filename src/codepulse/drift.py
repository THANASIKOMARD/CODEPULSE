"""Compare two saved runs and report what changed between them.

A run is the flat list of `file_metrics` rows `snapshot.get_run_metrics`
returns for one run_id. Drift only looks at scalar metrics already stored
by Phase 2 — no re-scanning, no git access.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Fields compared for drift on files present in both runs.
DRIFT_FIELDS = [
    "commits", "added", "removed", "complexity", "lines",
    "score", "role", "links", "num_authors", "bus_factor_risk", "roi",
]


@dataclass
class FileDrift:
    path: str
    status: str  # "added" | "removed" | "changed"
    old: dict | None = None
    new: dict | None = None
    deltas: dict = field(default_factory=dict)  # field -> (old_value, new_value)


def _impact(d: FileDrift) -> float:
    """Rank by how much a file's roi moved (or its roi, for added/removed)."""
    if d.status == "changed":
        return abs(d.new["roi"] - d.old["roi"])
    if d.status == "added":
        return d.new["roi"]
    return d.old["roi"]


def compute_drift(old_rows: list[dict], new_rows: list[dict]) -> list[FileDrift]:
    """Diff two runs' file_metrics by path. Sorted by impact, descending."""
    old_by_path = {r["path"]: r for r in old_rows}
    new_by_path = {r["path"]: r for r in new_rows}

    drifts: list[FileDrift] = []
    for path in old_by_path.keys() | new_by_path.keys():
        old = old_by_path.get(path)
        new = new_by_path.get(path)
        if old is None:
            drifts.append(FileDrift(path, "added", new=new))
        elif new is None:
            drifts.append(FileDrift(path, "removed", old=old))
        else:
            deltas = {f: (old[f], new[f]) for f in DRIFT_FIELDS if old[f] != new[f]}
            if deltas:
                drifts.append(FileDrift(path, "changed", old=old, new=new, deltas=deltas))

    drifts.sort(key=_impact, reverse=True)
    return drifts
