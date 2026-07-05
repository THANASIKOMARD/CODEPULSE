from codepulse.git_analysis import parse_log, compute_churn

RAW = "\n".join([
    "COMMIT\tabc123\tAlice\t2024-01-01T00:00:00+00:00",
    "10\t2\tsrc/app.py",
    "5\t0\tREADME.md",
    "COMMIT\tdef456\tBob\t2024-01-02T00:00:00+00:00",
    "3\t1\tsrc/app.py",
    "-\t-\tlogo.png",
    "4\t0\tsrc/{old => new}/mod.py",
])


def test_parses_two_commits():
    commits = parse_log(RAW)
    assert len(commits) == 2
    assert commits[0].author == "Alice"


def test_binary_counts_as_zero():
    logo = [f for c in parse_log(RAW) for f in c.files if f.path == "logo.png"][0]
    assert logo.binary is True
    assert (logo.added, logo.removed) == (0, 0)


def test_rename_resolves_to_new_path():
    paths = [f.path for c in parse_log(RAW) for f in c.files]
    assert "src/new/mod.py" in paths


def test_churn_aggregates_across_commits():
    churn = compute_churn(parse_log(RAW))
    assert churn["src/app.py"].commits == 2
    assert churn["src/app.py"].added == 13