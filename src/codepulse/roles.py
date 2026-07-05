"""Classify a file into a role from its path, for ROI-weighted ranking.

Two files can be equally churn-heavy but not equally important: production
code ('core') is worth more attention than tests, docs, or config. We infer
role cheaply from path conventions — no file reading needed.
"""
from __future__ import annotations

from pathlib import PurePosixPath

# Role weights used later by ROI ranking (core matters most).
ROLE_WEIGHTS = {
    "core": 1.0,
    "config": 0.6,
    "test": 0.4,
    "docs": 0.2,
}

_DOC_EXTS = {".md", ".rst", ".txt", ".adoc"}
_CONFIG_EXTS = {".json", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".lock"}


def classify(path: str) -> str:
    """Return one of: 'test', 'docs', 'config', 'core'."""
    p = PurePosixPath(path.replace("\\", "/"))
    parts = set(p.parts)
    name = p.name.lower()
    ext = p.suffix.lower()

    # test: a 'test'/'tests' directory, or test_*.py / *_test.py naming
    if "tests" in parts or "test" in parts:
        return "test"
    if name.startswith("test_") or name.endswith(("_test.py", ".test.js", ".spec.js")):
        return "test"

    # docs: a docs directory or a documentation file type
    if "docs" in parts or "doc" in parts or ext in _DOC_EXTS:
        return "docs"

    # config: known config/lock file types
    if ext in _CONFIG_EXTS:
        return "config"

    return "core"


def role_weight(role: str) -> float:
    return ROLE_WEIGHTS.get(role, 1.0)