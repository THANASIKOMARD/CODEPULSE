from codepulse.decay import forecast_decay, MIN_DATA_POINTS


def _row(ts, roi, path="src/app.py"):
    return {"path": path, "timestamp": ts, "roi": roi}


DAY = 86400.0


def test_not_enough_data_returns_none():
    rows = [_row(0, 100.0), _row(DAY, 110.0)]
    assert len(rows) < MIN_DATA_POINTS
    assert forecast_decay(rows, threshold=500.0) is None


def test_flat_or_declining_trend_has_no_cross():
    rows = [_row(0, 200.0), _row(DAY, 200.0), _row(2 * DAY, 150.0)]
    forecast = forecast_decay(rows, threshold=500.0)
    assert forecast is not None
    assert forecast.days_until_cross is None
    assert forecast.predicted_cross_timestamp is None


def test_already_past_threshold_has_no_cross():
    rows = [_row(0, 600.0), _row(DAY, 650.0), _row(2 * DAY, 700.0)]
    forecast = forecast_decay(rows, threshold=500.0)
    assert forecast.days_until_cross is None
    assert forecast.current_roi == 700.0


def test_growing_trend_predicts_cross_date():
    # roi grows by 100 per day, starting at 100 -> hits 500 in 4 more days
    rows = [_row(0, 100.0), _row(DAY, 200.0), _row(2 * DAY, 300.0)]
    forecast = forecast_decay(rows, threshold=500.0)
    assert forecast.slope == 100.0 / DAY
    assert forecast.days_until_cross is not None
    assert round(forecast.days_until_cross, 2) == 2.0


def test_forecast_reports_data_points_and_latest_path():
    rows = [_row(0, 100.0, "a.py"), _row(DAY, 200.0, "a.py"), _row(2 * DAY, 300.0, "a.py")]
    forecast = forecast_decay(rows, threshold=500.0)
    assert forecast.path == "a.py"
    assert forecast.data_points == 3
    assert forecast.current_roi == 300.0
