"""Predict when a file's roi will cross into a risk zone.

Fits a simple linear regression (roi vs. time) over a file's saved history
from Phase 2 (`snapshot.py`). No git access, no re-scanning — same
retrospective-data contract as `drift.py`, just prospective instead.
"""
from __future__ import annotations

from dataclasses import dataclass

MIN_DATA_POINTS = 3
SECONDS_PER_DAY = 86400.0


@dataclass
class DecayForecast:
    path: str
    data_points: int
    slope: float                       # roi change per day
    current_roi: float
    days_until_cross: float | None     # None = not trending toward the zone
    predicted_cross_timestamp: float | None


def _linreg(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Least-squares fit. Returns (slope, intercept) for y = slope*x + intercept."""
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)
    if den == 0:
        return 0.0, mean_y
    slope = num / den
    intercept = mean_y - slope * mean_x
    return slope, intercept


def forecast_decay(rows: list[dict], threshold: float) -> DecayForecast | None:
    """Fit roi-over-time for one file's history rows (oldest first, as returned
    by `snapshot.query_trend`). Returns None if there isn't enough history.
    """
    if len(rows) < MIN_DATA_POINTS:
        return None

    xs = [r["timestamp"] for r in rows]
    ys = [r["roi"] for r in rows]
    slope, intercept = _linreg(xs, ys)
    current_roi = ys[-1]

    if slope <= 0 or current_roi >= threshold:
        return DecayForecast(
            path=rows[-1]["path"],
            data_points=len(rows),
            slope=slope,
            current_roi=current_roi,
            days_until_cross=None,
            predicted_cross_timestamp=None,
        )

    cross_ts = (threshold - intercept) / slope
    days_until = (cross_ts - xs[-1]) / SECONDS_PER_DAY

    return DecayForecast(
        path=rows[-1]["path"],
        data_points=len(rows),
        slope=slope,
        current_roi=current_roi,
        days_until_cross=days_until,
        predicted_cross_timestamp=cross_ts,
    )
