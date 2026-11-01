"""Command line entry point: `issuescout triage owner/repo --limit 5`."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import uuid
from typing import List, Optional

from . import config, heuristics, report
from .github import GitHub
from .models import Report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="issuescout", description="Triage recent open GitHub issues.")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("triage", help="triage the newest open issues of a repo")
    t.add_argument("repo", help="owner/name")
    t.add_argument("--limit", type=int, default=5)
    t.add_argument("--issue", type=int, action="append", default=[],
                   help="triage specific issue number(s) instead of the newest ones (repeatable)")
    t.add_argument("--out", default="out", help="directory for report.{md,json,html}")
    t.add_argument("--engine", choices=["auto", "otari", "heuristic"], default="auto",
                   help="auto = Otari when OTARI_API_KEY is set, else heuristics")
    t.add_argument("--max-spend", type=float, default=float(os.environ.get("ISSUESCOUT_MAX_SPEND", "0.10")),
                   help="client-side USD cap for this run (Otari budgets still apply server-side)")
    t.add_argument("--user", default=os.environ.get("ISSUESCOUT_USER"),
                   help="end-user id for per-user cost attribution (sent as safety_identifier + metadata.user)")
    t.add_argument("--no-repro", action="store_true", help="skip sandboxed code-execution repros")
    t.add_argument("--no-research", action="store_true", help="skip web search / MCP research")
    t.add_argument("--apply", action="store_true", help="write labels + reply comments to GitHub (needs GITHUB_TOKEN)")
    sub.add_parser("doctor", help="check Otari connectivity, built-in tools and role models")
    return p


def doctor() -> int:
    from .otari_client import OtariClient
    c = OtariClient()
    tools = c.get("/tools").get("data", [])
    print("Otari built-in tools:", ", ".join(f"{t['id']}={'ok' if t.get('available') else 'off'}" for t in tools))
    ids = {m["id"] for m in c.get("/models").get("data", [])}
    for role in config.DEFAULT_CHAINS:
        ch = config.chain(role)
        print(f"{role:11s}", " -> ".join(f"{m}{'' if m in ids else ' (policy/unknown)'}" for m in ch))
    return 0


def run(argv: Optional[List[str]] = None, gh: Optional[GitHub] = None, otari=None) -> Report:
    args = build_parser().parse_args(argv)
    if args.cmd == "doctor":
        doctor()
        return Report("", "", "doctor")
    gh = gh or GitHub()
    if args.issue:
        issues = [gh.fetch_issue(args.repo, n) for n in args.issue]
    else:
        issues = gh.fetch_open_issues(args.repo, args.limit)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    use_otari = args.engine == "otari" or (args.engine == "auto" and (otari is not None or os.environ.get("OTARI_API_KEY")))
    if use_otari:
        from .agent import OtariTriager
        from .otari_client import Ledger, OtariClient
        client = otari or OtariClient(ledger=Ledger(max_spend_usd=args.max_spend), user=args.user,
                                      run_id=uuid.uuid4().hex[:8], guardrails=config.guardrail_entries())
        triager = OtariTriager(client, args.repo, repro=not args.no_repro, research=not args.no_research)
        triages = triager.triage_all(issues)
        rep = Report(repo=args.repo, generated_at=now, engine="otari", triages=triages,
                     spend_usd=client.ledger.spent_usd, notes=triager.notes,
                     batch_trace=[r.as_dict() for r in client.ledger.calls if r.role == "embedder"])
    else:
        rep = Report(repo=args.repo, generated_at=now, engine="heuristic", triages=heuristics.triage_all(issues))
    for p in report.write_all(rep, args.out):
        print(f"wrote {p}")
    if rep.engine == "otari":
        print(f"Otari spend this run: ${rep.spend_usd:.4f} across {len(client.ledger.calls)} calls")
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
