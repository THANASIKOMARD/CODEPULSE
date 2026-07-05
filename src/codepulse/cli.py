import argparse
import sys

from . import __version__
from .git_analysis import get_commits, compute_churn, find_repo_root, NotAGitRepo

def _print_table(stats, top):
    ranked = sorted(stats, key=lambda s: s.commits, reverse=True)[:top]
    print(f"{'File':<50} {'Commits':>7} {'+lines':>7} {'-lines':>7}")
    print("-" * 74)
    for s in ranked:
        path = s.path if len(s.path) <= 50 else "…" + s.path[-49:]
        print(f"{path:<50} {s.commits:>7} {s.added:>7} {s.removed:>7}")

def cmd_scan(args):
    try:
        root = find_repo_root(args.path)
    except NotAGitRepo:
        print(f"error: {args.path!r} is not inside a git repository.", file=sys.stderr)
        return 1
    commits = get_commits(str(root), since=args.since)
    if not commits:
        print("No commits found in the selected window.")
        return 0
    stats = compute_churn(commits)
    _print_table(list(stats.values()), args.top)
    return 0

def cmd_version(args):
    print(f"codepulse {__version__}")
    return 0

def build_parser():
    parser = argparse.ArgumentParser(
        prog="codepulse",
        description="Find high-churn / high-risk files in a git repo.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan a repo for hotspot files")
    scan.add_argument("path", nargs="?", default=".", help="Path inside the repo (default: .)")
    scan.add_argument("--since", default="90.days", help="Git date window (default: 90.days)")
    scan.add_argument("--top", type=int, default=10, help="How many files to show (default: 10)")
    scan.set_defaults(func=cmd_scan)

    ver = sub.add_parser("version", help="Print version")
    ver.set_defaults(func=cmd_version)

    return parser

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)