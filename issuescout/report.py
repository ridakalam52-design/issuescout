"""Render a triage Report as JSON, Markdown, and a self-contained static HTML page."""
from __future__ import annotations

import html
import json
import os
from typing import List

from .models import Report


def to_json(report: Report) -> str:
    return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)


def _quote(text: str) -> str:
    return "\n".join("> " + line for line in (text or "").strip().splitlines()) or "> (empty)"


def to_markdown(report: Report) -> str:
    lines: List[str] = [
        f"# IssueScout triage report: `{report.repo}`",
        "",
        f"Generated {report.generated_at} · engine: **{report.engine}** · dry run (nothing was written to GitHub)",
    ]
    if report.spend_usd:
        lines.append(f"\nModel + tool spend for this run: **${report.spend_usd:.4f}**")
    for n in report.notes:
        lines.append(f"\n_Note: {n}_")
    lines += ["", "| # | Title | Category | Priority | Labels | Possible duplicates |", "|---|---|---|---|---|---|"]
    for t in report.triages:
        d = ", ".join(f"#{x.number} ({x.score:.2f})" for x in t.duplicates) or "-"
        title = t.issue.title.replace("|", "\\|")
        lines.append(f"| [#{t.issue.number}]({t.issue.url}) | {title} | {t.category} | {t.priority} | {', '.join(t.labels)} | {d} |")
    for t in report.triages:
        lines += ["", f"## #{t.issue.number}: {t.issue.title}", "",
                  f"- **Category:** {t.category}  ·  **Priority:** {t.priority}  ·  **Labels:** {', '.join(t.labels) or '-'}",
                  f"- **Why:** {t.rationale or '-'}"]
        if t.duplicates:
            lines.append("- **Possible duplicates:** " + ", ".join(f"#{d.number} (score {d.score:.2f}, {d.method})" for d in t.duplicates))
        if t.guard:
            lines.append(f"- **Guardrail:** {t.guard.get('verdict', '-')} ({t.guard.get('model', '')})")
        if t.repro:
            lines.append(f"- **Repro (sandbox):** {t.repro.get('summary', '-')}")
        if t.related:
            lines.append("- **Related docs / known fixes:**")
            for r in t.related:
                lines.append(f"  - [{r.get('title') or r.get('url')}]({r.get('url')}): {r.get('why', '')}")
        lines += ["", "**Draft maintainer reply:**", "", _quote(t.reply)]
        if t.trace:
            lines += ["", "<details><summary>Gateway trace</summary>", "", "| role | requested | served by | provider | fallback | cost USD |", "|---|---|---|---|---|---|"]
            for s in t.trace:
                lines.append(f"| {s.get('role')} | {s.get('requested')} | {s.get('served_model', '')} | {s.get('provider', '')} | {s.get('fallback', '')} | {s.get('cost_usd', '')} |")
            lines += ["", "</details>"]
    return "\n".join(lines) + "\n"


_CSS = """
body{font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;color:#1b1b1f;background:#fafafa}
h1{font-size:1.5rem}h2{font-size:1.15rem;margin:0 0 .4rem}
.meta{color:#555}.card{background:#fff;border:1px solid #e3e3e8;border-radius:10px;padding:1rem 1.2rem;margin:1rem 0}
.pill{display:inline-block;border-radius:999px;padding:.05rem .6rem;font-size:.8rem;margin-right:.3rem;background:#eef}
.bug{background:#fde2e2}.feature{background:#e1f5e8}.question{background:#e6eefc}.docs{background:#fff4d6}.duplicate{background:#eee}
.P0,.P1{background:#d93636;color:#fff}.P2{background:#f0a020;color:#fff}.P3{background:#9aa}
blockquote{margin:.5rem 0;padding:.6rem .9rem;background:#f4f4f8;border-left:3px solid #7a7aff;white-space:pre-wrap}
table{border-collapse:collapse;font-size:.8rem}td,th{border:1px solid #ddd;padding:.2rem .4rem}
"""


def to_html(report: Report) -> str:
    e = html.escape
    parts = [f"<!doctype html><html><head><meta charset='utf-8'><title>IssueScout: {e(report.repo)}</title><style>{_CSS}</style></head><body>",
             f"<h1>IssueScout triage report: {e(report.repo)}</h1>",
             f"<p class='meta'>Generated {e(report.generated_at)} · engine: <b>{e(report.engine)}</b> · dry run"
             + (f" · spend ${report.spend_usd:.4f}" if report.spend_usd else "") + "</p>"]
    for n in report.notes:
        parts.append(f"<p class='meta'><i>{e(n)}</i></p>")
    for t in report.triages:
        parts.append("<div class='card'>")
        parts.append(f"<h2><a href='{e(t.issue.url)}'>#{t.issue.number}</a> {e(t.issue.title)}</h2>")
        parts.append(f"<span class='pill {e(t.category)}'>{e(t.category)}</span><span class='pill {e(t.priority)}'>{e(t.priority)}</span>"
                     + "".join(f"<span class='pill'>{e(l)}</span>" for l in t.labels))
        parts.append(f"<p><b>Why:</b> {e(t.rationale)}</p>")
        if t.duplicates:
            parts.append("<p><b>Possible duplicates:</b> " + ", ".join(f"#{d.number} ({d.score:.2f})" for d in t.duplicates) + "</p>")
        if t.guard:
            parts.append(f"<p><b>Guardrail:</b> {e(str(t.guard.get('verdict')))} <span class='meta'>({e(str(t.guard.get('model', '')))})</span></p>")
        if t.repro:
            parts.append(f"<p><b>Repro (sandbox):</b> {e(str(t.repro.get('summary', '')))}</p>")
        if t.related:
            parts.append("<p><b>Related docs / known fixes:</b></p><ul>" + "".join(
                f"<li><a href='{e(r.get('url', ''))}'>{e(r.get('title') or r.get('url', ''))}</a> {e(r.get('why', ''))}</li>" for r in t.related) + "</ul>")
        parts.append(f"<p><b>Draft reply</b></p><blockquote>{e(t.reply)}</blockquote>")
        if t.trace:
            parts.append("<details><summary>Gateway trace</summary><table><tr><th>role</th><th>requested</th><th>served by</th><th>provider</th><th>fallback</th><th>cost</th></tr>"
                         + "".join(f"<tr><td>{e(str(s.get('role')))}</td><td>{e(str(s.get('requested')))}</td><td>{e(str(s.get('served_model', '')))}</td><td>{e(str(s.get('provider', '')))}</td><td>{e(str(s.get('fallback', '')))}</td><td>{e(str(s.get('cost_usd', '')))}</td></tr>" for s in t.trace)
                         + "</table></details>")
        parts.append("</div>")
    parts.append("<p class='meta'>Made with IssueScout · drafts only, a human maintainer decides.</p></body></html>")
    return "\n".join(parts)


def write_all(report: Report, out_dir: str) -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for name, fn in (("report.json", to_json), ("report.md", to_markdown), ("report.html", to_html)):
        p = os.path.join(out_dir, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(fn(report))
        paths.append(p)
    return paths
