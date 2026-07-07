import argparse
import json
import sys
import time
from dataclasses import asdict

from . import __version__
from .report import build_report
from .git_analysis import NotAGitRepo, find_repo_root
from .snapshot import save_snapshot, query_trend, get_run_metrics, list_runs
from .drift import compute_drift


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
    if reports:
        save_snapshot(find_repo_root(args.path), args.since, reports)
    if args.json:
        print(json.dumps([asdict(r) for r in reports[:args.top]], indent=2))
    elif not reports:
        print("No commits found in the selected window.")
    else:
        _print_table(reports, args.top)
    return 0


def cmd_trend(args):
    try:
        root = find_repo_root(args.path)
    except NotAGitRepo:
        print(f"error: {args.path!r} is not inside a git repository.", file=sys.stderr)
        return 1
    rows = query_trend(root, args.file)
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    if not rows:
        print(f"No history for {args.file!r} yet — run `codepulse scan` a few times first.")
        return 0
    print(f"{'Timestamp':>19}  {'ROI':>8} {'Score':>7} {'Chn':>4} {'Cplx':>6} {'Lnk':>3} {'Au':>3}")
    print("-" * 62)
    for row in rows:
        ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(row["timestamp"]))
        print(
            f"{ts:>19}  {row['roi']:>8.0f} {row['score']:>7} {row['commits']:>4} "
            f"{row['complexity']:>6} {row['links']:>3} {row['num_authors']:>3}"
        )
    return 0


def _print_drift(drifts):
    if not drifts:
        print("No drift between these runs.")
        return
    for d in drifts:
        if d.status == "added":
            print(f"+ {d.path}  (new, roi={d.new['roi']:.0f})")
        elif d.status == "removed":
            print(f"- {d.path}  (removed, was roi={d.old['roi']:.0f})")
        else:
            roi_old, roi_new = d.deltas.get("roi", (d.old["roi"], d.new["roi"]))
            extra = ", ".join(
                f"{field}: {old_v}->{new_v}"
                for field, (old_v, new_v) in d.deltas.items()
                if field != "roi"
            )
            line = f"~ {d.path}  roi: {roi_old:.0f} -> {roi_new:.0f}"
            if extra:
                line += f"  ({extra})"
            print(line)


def cmd_drift(args):
    try:
        root = find_repo_root(args.path)
    except NotAGitRepo:
        print(f"error: {args.path!r} is not inside a git repository.", file=sys.stderr)
        return 1
    old_rows = get_run_metrics(root, args.from_run)
    new_rows = get_run_metrics(root, args.to_run)
    if not old_rows and not new_rows:
        runs = list_runs(root)
        if not runs:
            print("No scan history yet — run `codepulse scan` a few times first.")
        else:
            available = ", ".join(str(r["run_id"]) for r in runs)
            print(
                f"error: no data for run_id {args.from_run} or {args.to_run}. "
                f"Available run_ids: {available}",
                file=sys.stderr,
            )
        return 1
    drifts = compute_drift(old_rows, new_rows)
    if args.json:
        print(json.dumps([asdict(d) for d in drifts], indent=2))
        return 0
    _print_drift(drifts)
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

    trend = sub.add_parser("trend", help="Show how a file's metrics changed across past scans")
    trend.add_argument("file", help="File path (as shown in `scan` output) to track")
    trend.add_argument("path", nargs="?", default=".", help="Path inside the repo (default: .)")
    trend.add_argument("--json", action="store_true", help="Output JSON instead of a table")
    trend.set_defaults(func=cmd_trend)

    drift = sub.add_parser("drift", help="Compare two past scans and report what changed")
    drift.add_argument("--from", dest="from_run", type=int, required=True, help="Older run_id")
    drift.add_argument("--to", dest="to_run", type=int, required=True, help="Newer run_id")
    drift.add_argument("path", nargs="?", default=".", help="Path inside the repo (default: .)")
    drift.add_argument("--json", action="store_true", help="Output JSON instead of a table")
    drift.set_defaults(func=cmd_drift)

    ver = sub.add_parser("version", help="Print version")
    ver.set_defaults(func=cmd_version)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)