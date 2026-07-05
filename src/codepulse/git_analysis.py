"""Git history analysis for codepulse (churn, later: coupling).

We shell out to `git log` and parse it ourselves instead of using a git
library, because: zero dependencies, works anywhere git works, and parsing
--numstat teaches exactly what git records per change.

Churn = how many times a file changed. High-churn files are where bugs and
merge pain concentrate, so it's the first signal worth measuring.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# A field separator we control. %x09 in a git pretty-format emits a literal TAB.
_SEP = "\t"
_COMMIT_MARK = "COMMIT"

class NotAGitRepo(Exception):
    """Raised when a path is not inside a git working tree."""


def find_repo_root(path: str = ".") -> Path:
    """Return the top-level dir of the git repo containing `path`."""
    result = subprocess.run(
        ["git", "-C", path, "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise NotAGitRepo(path)
    return Path(result.stdout.strip())

@dataclass
class FileChange:
    path: str
    added: int
    removed: int
    binary: bool = False


@dataclass
class Commit:
    hash: str
    author: str
    date: str
    files: list[FileChange] = field(default_factory=list)


@dataclass
class ChurnStat:
    path: str
    commits: int = 0
    added: int = 0
    removed: int = 0


def _run_git_log(repo: str, since: str) -> str:
    # Header line per commit starts with COMMIT<TAB>hash<TAB>author<TAB>date,
    # then --numstat prints "<added>\t<removed>\t<path>" for each changed file.
    pretty = _SEP.join([_COMMIT_MARK, "%H", "%aN", "%aI"])
    result = subprocess.run(
        [
            "git", "-C", repo, "log",
            "--no-merges",
            f"--since={since}",
            "--numstat",
            f"--pretty=format:{pretty}",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    result.check_returncode()
    return result.stdout

def _resolve_rename(path: str) -> str:
    """Collapse git rename notation to the NEW path.

    git prints renames two ways inside --numstat:
        "old.py => new.py"
        "src/{old => new}/file.py"
    Keep the new name so churn accumulates on the file's current path.
    """
    if "=>" not in path:
        return path
    if "{" in path and "}" in path:
        prefix, rest = path.split("{", 1)
        inside, suffix = rest.split("}", 1)
        _, new = inside.split("=>")
        return (prefix + new.strip() + suffix).replace("//", "/")
    return path.split("=>")[-1].strip()

def parse_log(raw: str) -> list[Commit]:
    commits: list[Commit] = []
    current: Commit | None = None
    for line in raw.splitlines():
        if not line:
            continue
        if line.startswith(_COMMIT_MARK + _SEP):
            _, h, author, date = line.split(_SEP)
            current = Commit(hash=h, author=author, date=date)
            commits.append(current)
            continue
        # numstat line for the current commit
        added_s, removed_s, path = line.split(_SEP, 2)
        binary = added_s == "-" or removed_s == "-"
        added = 0 if binary else int(added_s)
        removed = 0 if binary else int(removed_s)
        path = _resolve_rename(path)
        current.files.append(
            FileChange(path=path, added=added, removed=removed, binary=binary)
        )
    return commits


def get_commits(repo: str = ".", since: str = "90.days") -> list[Commit]:
    return parse_log(_run_git_log(repo, since))


def compute_churn(commits: list[Commit]) -> dict[str, ChurnStat]:
    stats: dict[str, ChurnStat] = {}
    for commit in commits:
        for fc in commit.files:
            stat = stats.setdefault(fc.path, ChurnStat(path=fc.path))
            stat.commits += 1
            stat.added += fc.added
            stat.removed += fc.removed
    return stats

def file_groups(commits: list[Commit]) -> list[set[str]]:
    """One set of file paths per commit — raw material for co-change coupling.

    Files that repeatedly appear in the same set are 'temporally coupled':
    they change together, which often reveals hidden dependencies.
    """
    return [{fc.path for fc in c.files} for c in commits]