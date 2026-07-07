from codepulse.report import FileReport
from codepulse.snapshot import db_path, query_trend, save_snapshot

def _report(path="src/app.py", roi=100.0, commits=5):
    return FileReport(
        path=path,
        commits=commits,
        added=10,
        removed=2,
        complexity=50,
        lines=200,
        score=commits * 50,
        role="core",
        links=3,
        num_authors=2,
        bus_factor_risk=False,
        roi=roi,
    )

def test_save_snapshot_creates_db(tmp_path):
    save_snapshot(tmp_path, "90.days", [_report()])
    assert db_path(tmp_path).exists()

def test_query_trend_returns_saved_row(tmp_path):
    save_snapshot(tmp_path, "90.days", [_report(roi=100.0)])
    rows = query_trend(tmp_path, "src/app.py")
    assert len(rows) == 1
    assert rows[0]["roi"] == 100.0
    assert rows[0]["since_window"] == "90.days"

def test_query_trend_orders_chronologically(tmp_path):
    save_snapshot(tmp_path, "90.days", [_report(roi=100.0)])
    save_snapshot(tmp_path, "90.days", [_report(roi=150.0)])
    rows = query_trend(tmp_path, "src/app.py")
    assert [r["roi"] for r in rows] == [100.0, 150.0]

def test_query_trend_ignores_other_files(tmp_path):
    save_snapshot(tmp_path, "90.days", [_report(path="src/app.py"), _report(path="src/other.py")])
    rows = query_trend(tmp_path, "src/app.py")
    assert len(rows) == 1
    assert rows[0]["path"] == "src/app.py"

def test_query_trend_no_history_returns_empty(tmp_path):
    assert query_trend(tmp_path, "src/app.py") == []
