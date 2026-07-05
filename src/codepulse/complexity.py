"""Complexity metrics for codepulse.

We approximate complexity with *indentation depth* instead of a real parser:
deeply nested code (many indent levels) is harder to read and change, and this
works for any language with zero dependencies (Tornhill's whitespace complexity).
"""
from __future__ import annotations

from pathlib import Path


def indentation_complexity(text: str) -> tuple[int, int]:
    """Return (complexity, lines) for a blob of source text.

    complexity = sum of indent *levels* over non-blank lines (nesting depth)
    lines      = number of non-blank lines (a size proxy)
    """
    complexity = 0
    lines = 0
    for raw_line in text.splitlines():
        line = raw_line.expandtabs(4)
        if line.strip() == "":
            continue
        lines += 1
        indent = len(line) - len(line.lstrip(" "))
        complexity += indent // 4
    return complexity, lines


def file_complexity(abs_path: str | Path) -> tuple[int, int] | None:
    """Return (complexity, lines) for a file, or None if missing/binary/unreadable."""
    try:
        text = Path(abs_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    if "\x00" in text:            # crude binary check: real source has no NUL byte
        return None
    return indentation_complexity(text)