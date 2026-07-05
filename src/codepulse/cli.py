import argparse
import json
import sys
from dataclasses import asdict

from . import __version__
from .report import build_report
from .git_analysis import NotAGitRepo


def _print_table(reports, top):
    print(f"{'ROI':>8} {'Score':>7} {'Chn':>4} {'Cplx':>6} {'Role':>6} {'Lnk':>3} {'Au':>3}  File")
    print("-" * 88)
    for r in reports[:top]:
        risk = "!" if r.bus_factor_risk else " "
        path = r.path if len(r.path) <= 44 else "…" + r.path[-43:]
        print(
            f"{r.roi:>8.0f} {r.score:>7} {r.commits:>4} {r.complexity:>6} "
            f"{r.role:>6} {r.links:>3} {r.num_authors:>3}{risk} {path}"
        )


def cmd_scan(args):
    try:
        reports = build_report(args.path, since=args.since)
    except NotAGitRepo:
        print(f"error: {args.path!r} is not inside a git repository.", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps([asdict(r) for r in reports[:args.top]], indent=2))
    elif not reports:
        print("No commits found in the selected window.")
    else:
        _print_table(reports, args.top)
    return 0


def cmd_version(args):
    print(f"codepulse {__version__}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="codepulse",
        description="Find high-churn / high-risk hotspot files in a git repo.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan a repo for hotspot files")
    scan.add_argument("path", nargs="?", default=".", help="Path inside the repo (default: .)")
    scan.add_argument("--since", default="90.days", help="Git date window (default: 90.days)")
    scan.add_argument("--top", type=int, default=10, help="How many files to show (default: 10)")
    scan.add_argument("--json", action="store_true", help="Output JSON instead of a table")
    scan.set_defaults(func=cmd_scan)

    ver = sub.add_parser("version", help="Print version")
    ver.set_defaults(func=cmd_version)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)