"""Command line entry point: `issuescout triage owner/repo --limit 5`."""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from typing import List, Optional

from . import heuristics, report
from .github import GitHub
from .models import Report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="issuescout", description="Triage recent open GitHub issues.")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("triage", help="triage the newest open issues of a repo")
    t.add_argument("repo", help="owner/name")
    t.add_argument("--limit", type=int, default=5)
    t.add_argument("--out", default="out", help="directory for report.{md,json,html}")
    t.add_argument("--apply", action="store_true", help="write labels + reply comments to GitHub (needs GITHUB_TOKEN)")
    return p


def run(argv: Optional[List[str]] = None, gh: Optional[GitHub] = None) -> Report:
    args = build_parser().parse_args(argv)
    gh = gh or GitHub()
    issues = gh.fetch_open_issues(args.repo, args.limit)
    rep = Report(repo=args.repo, generated_at=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                 engine="heuristic", triages=heuristics.triage_all(issues))
    for p in report.write_all(rep, args.out):
        print(f"wrote {p}")
    if args.apply:
        for t in rep.triages:
            gh.apply_triage(args.repo, t.issue.number, t.labels, t.reply)
        print(f"applied triage to {len(rep.triages)} issues")
    return rep


def main() -> None:
    try:
        run()
    except Exception as exc:  # pragma: no cover - CLI surface
        print(f"issuescout: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
