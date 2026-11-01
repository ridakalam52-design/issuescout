"""Offline, rule-based triage. No model calls.

This is the baseline engine (and the fallback when no LLM gateway is
configured). It is deliberately simple: keyword classification, Jaccard
title similarity for duplicates, and a template reply.
"""
from __future__ import annotations

import re
from typing import Dict, List

from .models import Duplicate, Issue, Triage

_KEYWORDS: Dict[str, List[str]] = {
    "bug": ["bug", "error", "crash", "exception", "traceback", "fails", "failing", "broken", "regression", "500", "not working"],
    "feature": ["feature", "support for", "add ", "request", "would be nice", "enhancement", "allow", "proposal"],
    "docs": ["docs", "documentation", "readme", "typo", "example", "guide"],
    "question": ["how do i", "how to", "question", "is it possible", "?", "help"],
}

_WORD = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> set:
    return {w for w in _WORD.findall(text.lower()) if len(w) > 2}


def jaccard(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def classify(issue: Issue) -> str:
    text = f"{issue.title}\n{issue.body}".lower()
    scores = {cat: sum(text.count(k) for k in kws) for cat, kws in _KEYWORDS.items()}
    # Title words weigh more than body words.
    for cat, kws in _KEYWORDS.items():
        scores[cat] += 2 * sum(issue.title.lower().count(k) for k in kws)
    best = max(scores, key=lambda c: scores[c])
    return best if scores[best] > 0 else "question"


def priority(category: str, issue: Issue) -> str:
    text = f"{issue.title} {issue.body}".lower()
    if category == "bug" and any(k in text for k in ("crash", "data loss", "security", "production")):
        return "P1"
    if category == "bug":
        return "P2"
    return "P3"


def find_duplicates(issues: List[Issue], threshold: float = 0.5) -> Dict[int, List[Duplicate]]:
    out: Dict[int, List[Duplicate]] = {i.number: [] for i in issues}
    for i, a in enumerate(issues):
        for b in issues[i + 1:]:
            s = jaccard(a.title, b.title)
            if s >= threshold:
                out[a.number].append(Duplicate(b.number, round(s, 3), "jaccard"))
                out[b.number].append(Duplicate(a.number, round(s, 3), "jaccard"))
    return out


def template_reply(issue: Issue, category: str) -> str:
    who = f"@{issue.author}" if issue.author else "there"
    asks = {
        "bug": "Could you share the exact version, your OS, and a minimal snippet that reproduces it?",
        "feature": "Could you describe the use case this would unlock, and any API shape you have in mind?",
        "question": "A maintainer will take a look soon; in the meantime the docs may already cover this.",
        "docs": "A pull request with the suggested wording would be very welcome.",
        "duplicate": "This looks like it may duplicate an existing issue; we'll link them if so.",
    }
    return f"Hi {who}, thanks for opening this! {asks.get(category, asks['question'])}"


def triage_all(issues: List[Issue]) -> List[Triage]:
    dups = find_duplicates(issues)
    out = []
    for issue in issues:
        cat = classify(issue)
        out.append(Triage(
            issue=issue,
            category=cat,
            labels=[cat],
            priority=priority(cat, issue),
            rationale="keyword heuristics",
            duplicates=dups.get(issue.number, []),
            reply=template_reply(issue, cat),
        ))
    return out
