import pytest

from codepulse.roles import classify


@pytest.mark.parametrize("path,expected", [
    ("src/flask/app.py", "core"),
    ("tests/test_cli.py", "test"),
    ("src/pkg/foo_test.py", "test"),
    ("docs/index.rst", "docs"),
    ("README.md", "docs"),
    ("pyproject.toml", "config"),
    ("uv.lock", "config"),
])
def test_classify(path, expected):
    assert classify(path) == expected