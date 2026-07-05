from codepulse.coupling import compute_coupling


def test_pairs_counted_across_commits():
    groups = [{"a", "b"}, {"a", "b"}, {"a", "c"}]
    cp = compute_coupling(groups, min_shared=2)
    assert cp.links["a"] == 1        # a-b together twice -> counts
    assert cp.links["b"] == 1
    assert "c" not in cp.links       # a-c only once -> below min_shared


def test_giant_commits_skipped():
    big = {str(i) for i in range(100)}     # > max_group
    cp = compute_coupling([big, big], max_group=30, min_shared=1)
    assert cp.links == {}


def test_single_file_commit_has_no_pairs():
    cp = compute_coupling([{"solo"}], min_shared=1)
    assert cp.links == {}