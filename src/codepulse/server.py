"""Local read-only HTTP API over a repo's `.codepulse/history.db`.

Every endpoint here is a thin wrapper around functions that already exist
in snapshot.py / drift.py / decay.py — the CLI commands (cmd_trend,
cmd_drift, cmd_predict) call the exact same functions, just print the
result instead of returning it as JSON. No new calculation logic lives
here on purpose: this module's only job is serialization + routing.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .decay import forecast_decay
from .drift import compute_drift
from .snapshot import get_run_metrics, list_runs, list_tracked_paths, query_trend

STATIC_DIR = Path(__file__).parent / "static"

def create_app(root: Path):
    """Build a FastAPI app bound to one repo's history.

    A factory function (not a module-level `app`) because the dashboard
    is always scoped to a single repo, and that repo path is only known
    once the CLI resolves `args.path` at runtime. Baking `root` into the
    closures below keeps every route a plain function of (root, request)
    with no global/module state to reset between runs or tests.
    """
    from fastapi import FastAPI, HTTPException

    app = FastAPI(title="codepulse dashboard")

    @app.get("/api/runs")
    def get_runs():
        return list_runs(root)

    @app.get("/api/paths")
    def get_paths():
        # Powers the frontend's file picker for the trend chart.
        return sorted(list_tracked_paths(root))

    @app.get("/api/latest")
    def get_latest():
        runs = list_runs(root)
        if not runs:
            raise HTTPException(404, "no scan history yet — run `codepulse scan` first")
        latest = runs[-1]
        rows = get_run_metrics(root, latest["run_id"])
        # get_run_metrics has no ORDER BY (see snapshot.py) — row order from
        # SQLite isn't guaranteed, so sort here rather than trust insertion
        # order. Matches the same roi-descending order build_report already
        # uses for the CLI table.
        rows.sort(key=lambda r: r["roi"], reverse=True)
        return {"run_id": latest["run_id"], "timestamp": latest["timestamp"], "files": rows}

    @app.get("/api/trend/{file_path:path}")
    def get_trend(file_path: str):
        # `:path` converter (not the default `str`) because file paths
        # contain slashes, e.g. "src/codepulse/cli.py" — the default
        # converter would stop matching at the first "/".
        rows = query_trend(root, file_path)
        if not rows:
            raise HTTPException(404, f"no history for {file_path!r}")
        return rows

    @app.get("/api/drift")
    def get_drift(from_run: int, to_run: int):
        # Param names mirror cli.py's args.from_run/args.to_run (the CLI
        # itself renames --from to from_run since "from" is a keyword) —
        # kept identical here so the two entry points read the same way.
        old_rows = get_run_metrics(root, from_run)
        new_rows = get_run_metrics(root, to_run)
        if not old_rows and not new_rows:
            raise HTTPException(404, f"no data for run_id {from_run} or {to_run}")
        return [asdict(d) for d in compute_drift(old_rows, new_rows)]

    @app.get("/api/predict")
    def get_predict(threshold: float = 500.0, within_days: float = 30.0):
        forecasts = []
        for path in list_tracked_paths(root):
            forecast = forecast_decay(query_trend(root, path), threshold)
            if forecast is None:
                continue
            if forecast.days_until_cross is not None and forecast.days_until_cross <= within_days:
                forecasts.append(forecast)
        forecasts.sort(key=lambda f: f.days_until_cross)
        return [asdict(f) for f in forecasts]
    
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")

    return app