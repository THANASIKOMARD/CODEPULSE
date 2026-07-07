"""Persist scan results over time so trends can be tracked across runs.

Each `scan` writes one row to `runs` and one row per file to `file_metrics`.
Stored at <repo>/.codepulse/history.db — local to the repo being scanned,
same as `.git`, so history travels with clones only if the user opts in.
"""
from __future__ import annotations

import sqlite3
import time
from dataclasses import fields
from pathlib import Path

from .report import FileReport

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    since_window TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS file_metrics (
    run_id INTEGER NOT NULL REFERENCES runs(run_id),
    path TEXT NOT NULL,
    commits INTEGER NOT NULL,
    added INTEGER NOT NULL,
    removed INTEGER NOT NULL,
    complexity INTEGER NOT NULL,
    lines INTEGER NOT NULL,
    score INTEGER NOT NULL,
    role TEXT NOT NULL,
    links INTEGER NOT NULL,
    num_authors INTEGER NOT NULL,
    bus_factor_risk INTEGER NOT NULL,
    roi REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_file_metrics_path ON file_metrics(path);
"""

_REPORT_FIELDS = [f.name for f in fields(FileReport)]


def db_path(root: Path) -> Path:
    return Path(root) / ".codepulse" / "history.db"

def _connect(root: Path) -> sqlite3.Connection:
    path = db_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(_SCHEMA)
    return conn

def save_snapshot(root: Path, since: str, reports: list[FileReport]) -> int:
    """Write one run + its per-file metrics. Returns the run_id."""
    with _connect(root) as conn:
        cur = conn.execute(
            "INSERT INTO runs (timestamp, since_window) VALUES (?, ?)",
            (time.time(), since),
        )
        run_id = cur.lastrowid
        conn.executemany(
            f"""INSERT INTO file_metrics
                ({', '.join(_REPORT_FIELDS)}, run_id)
                VALUES ({', '.join('?' for _ in _REPORT_FIELDS)}, ?)""",
            [
                tuple(getattr(r, name) for name in _REPORT_FIELDS) + (run_id,)
                for r in reports
            ],
        )
        return run_id

def query_trend(root: Path, path: str) -> list[dict]:
    """Return this file's metrics across all past runs, oldest first."""
    db = db_path(root)
    if not db.exists():
        return []
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT r.timestamp, r.since_window, m.*
               FROM file_metrics m
               JOIN runs r ON r.run_id = m.run_id
               WHERE m.path = ?
               ORDER BY r.timestamp ASC""",
            (path,),
        ).fetchall()
        return [dict(row) for row in rows]

def list_runs(root: Path) -> list[dict]:
    """Return all runs, oldest first — used to show what run_ids exist."""
    db = db_path(root)
    if not db.exists():
        return []
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT run_id, timestamp, since_window FROM runs ORDER BY run_id ASC"
        ).fetchall()
        return [dict(row) for row in rows]

def get_run_metrics(root: Path, run_id: int) -> list[dict]:
    """Return every file's metrics for a single run."""
    db = db_path(root)
    if not db.exists():
        return []
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM file_metrics WHERE run_id = ?", (run_id,)
        ).fetchall()
        return [dict(row) for row in rows]
