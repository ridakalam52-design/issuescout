"""Plain data types shared by the fetcher, the triage engine and the reports."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


CATEGORIES = ("bug", "feature", "question", "docs", "duplicate")
PRIORITIES = ("P0", "P1", "P2", "P3")


@dataclass
class Issue:
    number: int
    title: str
    body: str
    url: str
    author: str = ""
    labels: List[str] = field(default_factory=list)
    created_at: str = ""
    comments: int = 0

    @classmethod
    def from_github(cls, raw: Dict[str, Any]) -> "Issue":
        return cls(
            number=int(raw["number"]),
            title=raw.get("title") or "",
            body=raw.get("body") or "",
            url=raw.get("html_url") or "",
            author=(raw.get("user") or {}).get("login", ""),
            labels=[l["name"] if isinstance(l, dict) else str(l) for l in raw.get("labels") or []],
            created_at=raw.get("created_at") or "",
            comments=int(raw.get("comments") or 0),
        )


@dataclass
class Duplicate:
    number: int
    score: float
    method: str = "jaccard"


@dataclass
class Triage:
    issue: Issue
    category: str = "question"
    labels: List[str] = field(default_factory=list)
    priority: str = "P3"
    rationale: str = ""
    duplicates: List[Duplicate] = field(default_factory=list)
    repro: Optional[Dict[str, Any]] = None
    related: List[Dict[str, str]] = field(default_factory=list)
    reply: str = ""
    guard: Optional[Dict[str, Any]] = None
    trace: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Report:
    repo: str
    generated_at: str
    engine: str
    triages: List[Triage] = field(default_factory=list)
    spend_usd: float = 0.0
    notes: List[str] = field(default_factory=list)
    batch_trace: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo": self.repo,
            "generated_at": self.generated_at,
            "engine": self.engine,
            "spend_usd": round(self.spend_usd, 6),
            "notes": self.notes,
            "batch_trace": self.batch_trace,
            "issues": [t.to_dict() for t in self.triages],
        }
