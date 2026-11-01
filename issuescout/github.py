"""Minimal GitHub REST client (stdlib only).

Reads work unauthenticated (60 req/h). Set GITHUB_TOKEN for higher limits.
Writes (labels, comments) happen ONLY through `apply_triage`, which the CLI
calls only with `--apply` and a token.
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Callable, Dict, List, Optional

from .models import Issue

API = "https://api.github.com"

Transport = Callable[[str, str, Optional[bytes], Dict[str, str]], Any]


def _default_transport(method: str, url: str, data: Optional[bytes], headers: Dict[str, str]) -> Any:
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (fixed https host)
        return json.loads(resp.read().decode("utf-8") or "null")


class GitHub:
    def __init__(self, token: Optional[str] = None, transport: Optional[Transport] = None):
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN")
        self.transport = transport or _default_transport

    def _headers(self) -> Dict[str, str]:
        h = {"Accept": "application/vnd.github+json", "User-Agent": "issuescout"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def fetch_open_issues(self, repo: str, limit: int = 5) -> List[Issue]:
        """Most recently created open issues, pull requests excluded."""
        if repo.count("/") != 1:
            raise ValueError("repo must look like owner/name")
        issues: List[Issue] = []
        page = 1
        while len(issues) < limit and page <= 5:
            url = f"{API}/repos/{repo}/issues?state=open&sort=created&direction=desc&per_page=30&page={page}"
            batch = self.transport("GET", url, None, self._headers()) or []
            if not batch:
                break
            for raw in batch:
                if "pull_request" in raw:
                    continue
                issues.append(Issue.from_github(raw))
                if len(issues) >= limit:
                    break
            page += 1
        return issues

    def fetch_issue(self, repo: str, number: int) -> Issue:
        raw = self.transport("GET", f"{API}/repos/{repo}/issues/{int(number)}", None, self._headers())
        if "pull_request" in (raw or {}):
            raise ValueError(f"#{number} is a pull request")
        return Issue.from_github(raw)

    def apply_triage(self, repo: str, number: int, labels: List[str], comment: str) -> None:
        if not self.token:
            raise RuntimeError("--apply needs GITHUB_TOKEN")
        h = dict(self._headers(), **{"Content-Type": "application/json"})
        if labels:
            self.transport("POST", f"{API}/repos/{repo}/issues/{number}/labels",
                           json.dumps({"labels": labels}).encode(), h)
        if comment:
            self.transport("POST", f"{API}/repos/{repo}/issues/{number}/comments",
                           json.dumps({"body": comment}).encode(), h)
