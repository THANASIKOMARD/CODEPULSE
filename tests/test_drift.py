from codepulse.drift import compute_drift
from codepulse.report import FileReport
from codepulse.snapshot import save_snapshot, get_run_metrics


def _row(path="src/app.py", roi=100.0, commits=5, role="core", bus_factor_risk=False):
    return {
        "path": path,
        "commits": commits,
        "added": 10,
        "removed": 2,
        "complexity": 50,
        "lines": 200,
        "score": commits * 50,
        "role": role,
        "links": 3,
        "num_authors": 2,
        "bus_factor_risk": bus_factor_risk,
        "roi": roi,
    }


def test_added_file_has_no_old_side():
    drifts = compute_drift([], [_row(path="src/new.py")])
    assert len(drifts) == 1
    assert drifts[0].status == "added"
    assert drifts[0].old is None
    assert drifts[0].new["path"] == "src/new.py"


def test_removed_file_has_no_new_side():
    drifts = compute_drift([_row(path="src/gone.py")], [])
    assert len(drifts) == 1
    assert drifts[0].status == "removed"
    assert drifts[0].new is None


def test_changed_file_reports_only_differing_fields():
    old = _row(roi=100.0, commits=5)
    new = _row(roi=150.0, commits=8)
    drifts = compute_drift([old], [new])
    assert len(drifts) == 1
    d = drifts[0]
    assert d.status == "changed"
    assert d.deltas["roi"] == (100.0, 150.0)
    assert d.deltas["commits"] == (5, 8)
    assert d.deltas["score"] == (250, 400)
    assert "added" not in d.deltas  # unchanged field stays out of the delta dict


def test_unchanged_file_produces_no_drift_entry():
    row = _row()
    assert compute_drift([row], [row]) == []


def test_role_change_is_treated_as_drift():
    old = _row(role="core")
    new = _row(role="test")
    drifts = compute_drift([old], [new])
    assert len(drifts) == 1
    assert drifts[0].deltas["role"] == ("core", "test")


def test_bus_factor_flip_is_treated_as_drift():
    old = _row(bus_factor_risk=False)
    new = _row(bus_factor_risk=True)
    drifts = compute_drift([old], [new])
    assert drifts[0].deltas["bus_factor_risk"] == (False, True)


def test_sorted_by_impact_descending():
    old_rows = [_row(path="a.py", roi=100.0), _row(path="b.py", roi=100.0)]
    new_rows = [_row(path="a.py", roi=110.0), _row(path="b.py", roi=500.0)]
    drifts = compute_drift(old_rows, new_rows)
    assert [d.path for d in drifts] == ["b.py", "a.py"]


def test_integration_with_saved_snapshots(tmp_path):
    old_report = FileReport(
        path="src/app.py", commits=5, added=10, removed=2, complexity=50,
        lines=200, score=250, role="core", links=3, num_authors=2,
        bus_factor_risk=False, roi=100.0,
    )
    new_report = FileReport(
        path="src/app.py", commits=9, added=10, removed=2, complexity=50,
        lines=200, score=450, role="core", links=3, num_authors=2,
        bus_factor_risk=False, roi=180.0,
    )
    run_a = save_snapshot(tmp_path, "90.days", [old_report])
    run_b = save_snapshot(tmp_path, "90.days", [new_report])

    drifts = compute_drift(get_run_metrics(tmp_path, run_a), get_run_metrics(tmp_path, run_b))

    assert len(drifts) == 1
    assert drifts[0].deltas["roi"] == (100.0, 180.0)
