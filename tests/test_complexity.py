from codepulse.complexity import indentation_complexity


def test_skips_blank_lines():
    complexity, lines = indentation_complexity("a\n\n  b\n")
    assert lines == 2


def test_indentation_levels_sum():
    text = "def f():\n    x = 1\n        y = 2\n"
    complexity, lines = indentation_complexity(text)
    assert complexity == 3
    assert lines == 3


def test_tab_equals_four_spaces():
    complexity, lines = indentation_complexity("\tx = 1\n")
    assert complexity == 1
    assert lines == 1