"""Thin client for the Otari gateway (https://api.otari.ai/api/v1, OpenAI-compatible).

Everything model-related in IssueScout goes through this one class, so every
call gets the same Otari treatment:

* routing: the `model` may be an Otari routing-policy name (server-side
  fallback chain) and we also keep a short client-side chain for when the
  policy itself is missing in a fresh workspace. The serving model,
  provider and `Otari-Fallback` header are recorded per call.
* budgets: every response's `usage.cost_usd` is added to a run ledger and a
  local `max_spend_usd` cap is enforced *before* the next call; Otari's own
  402 / `budget_exceeded` answers (workspace ceiling, per-member budget) are
  turned into a clean `BudgetExceeded`.
* per-user attribution: `safety_identifier` + `metadata.user` on every
  request, so Otari's usage API / dashboard can split spend per end user.
* guardrails: optional request-level `guardrails` entries, and the
  `Otari-Guardrails` verdict header is recorded.
* built-in tools and MCP are passed straight through (`tools`,
  `mcp_servers`, `mcp_server_ids`, `max_tool_iterations`).

The API key is read from OTARI_API_KEY and is never logged or written to a
report.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

DEFAULT_BASE_URL = "https://api.otari.ai/api/v1"  # note: /api/v1, not /v1

# transport(method, url, body_bytes, headers) -> (status, response_headers, body_bytes)
Transport = Callable[[str, str, Optional[bytes], Dict[str, str]], Tuple[int, Dict[str, str], bytes]]


class OtariError(RuntimeError):
    def __init__(self, status: int, detail: str, code: str = ""):
        super().__init__(f"Otari HTTP {status}: {detail}")
        self.status, self.detail, self.code = status, detail, code


class BudgetExceeded(OtariError):
    pass


def _urllib_transport(method: str, url: str, data: Optional[bytes], headers: Dict[str, str]):
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:  # noqa: S310
            return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read()
    except urllib.error.HTTPError as e:  # surface status + body to the caller
        return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, e.read()


@dataclass
class CallRecord:
    role: str
    requested: str
    served_model: str = ""
    provider: str = ""
    fallback: str = ""
    attempts: str = ""
    cost_usd: float = 0.0
    request_id: str = ""
    guardrails: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    error: str = ""

    def as_dict(self) -> Dict[str, Any]:
        d = {k: v for k, v in self.__dict__.items() if v not in ("", [], None)}
        d["cost_usd"] = round(self.cost_usd, 6)
        return d


@dataclass
class Ledger:
    """Client-side spend guard on top of Otari's server-side budgets."""
    max_spend_usd: Optional[float] = None
    spent_usd: float = 0.0
    calls: List[CallRecord] = field(default_factory=list)

    def check(self, role: str) -> None:
        if self.max_spend_usd is not None and self.spent_usd >= self.max_spend_usd:
            raise BudgetExceeded(402, f"local run budget ${self.max_spend_usd:.4f} reached before '{role}' call", "local_budget")

    def add(self, rec: CallRecord) -> None:
        self.spent_usd += rec.cost_usd
        self.calls.append(rec)


class OtariClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None,
                 transport: Optional[Transport] = None, ledger: Optional[Ledger] = None,
                 user: Optional[str] = None, run_id: str = "", app: str = "issuescout",
                 guardrails: Optional[List[Dict[str, Any]]] = None):
        self.api_key = api_key if api_key is not None else os.environ.get("OTARI_API_KEY", "")
        self.base_url = (base_url or os.environ.get("OTARI_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.transport = transport or _urllib_transport
        self.ledger = ledger or Ledger()
        self.user = user
        self.run_id = run_id
        self.app = app
        self.guardrails = guardrails or []

    # ------------------------------------------------------------------ http
    def _headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise OtariError(401, "OTARI_API_KEY is not set")
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json",
                "User-Agent": "issuescout/0.1"}

    def _post(self, path: str, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
        status, headers, body = self.transport("POST", f"{self.base_url}{path}", json.dumps(payload).encode(), self._headers())
        try:
            data = json.loads(body.decode("utf-8") or "{}")
        except ValueError:
            data = {"detail": body[:300].decode("utf-8", "replace")}
        if status >= 400:
            detail = data.get("detail") if isinstance(data, dict) else str(data)
            if isinstance(detail, dict):
                detail = json.dumps(detail)
            code = headers.get("otari-error-code", "") or (data.get("code", "") if isinstance(data, dict) else "")
            cls = BudgetExceeded if status == 402 or "budget" in f"{code} {detail}".lower() else OtariError
            raise cls(status, str(detail), code)
        return data, headers

    def get(self, path: str) -> Any:
        status, _, body = self.transport("GET", f"{self.base_url}{path}", None, self._headers())
        if status >= 400:
            raise OtariError(status, body[:300].decode("utf-8", "replace"))
        return json.loads(body.decode("utf-8"))

    # ------------------------------------------------------------ attribution
    def _attribution(self, role: str) -> Dict[str, Any]:
        meta = {"app": self.app, "role": role}
        if self.run_id:
            meta["run"] = self.run_id
        out: Dict[str, Any] = {}
        if self.user:
            meta["user"] = self.user
            out["safety_identifier"] = self.user  # per-end-user attribution, never forwarded upstream
        out["metadata"] = meta
        return out

    # ------------------------------------------------------------------ chat
    def chat(self, role: str, models: Sequence[str], messages: List[Dict[str, Any]], **params: Any) -> Tuple[Dict[str, Any], CallRecord]:
        """Chat completion with a model chain.

        `models[0]` is normally an Otari routing policy (server-side fallback);
        later entries are only tried if the gateway answers with a non-budget
        error for the earlier ones (e.g. the policy does not exist in this
        workspace). Budget refusals are never retried on another model.
        """
        last: Optional[Exception] = None
        for model in models:
            self.ledger.check(role)
            payload = {"model": model, "messages": messages, **self._attribution(role), **params}
            if self.guardrails and "guardrails" not in payload:
                payload["guardrails"] = self.guardrails
            rec = CallRecord(role=role, requested=model)
            try:
                data, headers = self._post("/chat/completions", payload)
            except BudgetExceeded:
                raise
            except OtariError as e:
                rec.error = f"{e.status}: {e.detail[:160]}"
                self.ledger.add(rec)
                last = e
                continue
            usage = data.get("usage") or {}
            rec.cost_usd = float(usage.get("cost_usd") or usage.get("estimated_cost") or 0)
            rec.served_model = headers.get("otari-model", data.get("model", ""))
            rec.provider = headers.get("otari-provider", "")
            rec.fallback = "client" if model != models[0] else headers.get("otari-fallback", "")
            rec.attempts = headers.get("otari-attempt-count", "")
            rec.request_id = headers.get("otari-request-id", "")
            rec.guardrails = headers.get("otari-guardrails", "")
            rec.tool_calls = []
            for c in data.get("otari_tool_calls") or []:
                tc = {k: c.get(k) for k in ("type", "status", "query", "url") if c.get(k)}
                srcs = [s.get("url") for s in (c.get("sources") or []) if isinstance(s, dict) and s.get("url")]
                if srcs:
                    tc["sources"] = srcs[:8]
                rec.tool_calls.append(tc)
            self.ledger.add(rec)
            return data, rec
        raise last or OtariError(500, "no model in chain")

    # ------------------------------------------------------------ embeddings
    def embed(self, role: str, models: Sequence[str], texts: List[str]) -> Tuple[List[List[float]], CallRecord]:
        last: Optional[Exception] = None
        for model in models:
            self.ledger.check(role)
            rec = CallRecord(role=role, requested=model)
            try:
                data, headers = self._post("/embeddings", {"model": model, "input": texts, **self._attribution(role)})
            except BudgetExceeded:
                raise
            except OtariError as e:
                rec.error = f"{e.status}: {e.detail[:160]}"
                self.ledger.add(rec)
                last = e
                continue
            usage = data.get("usage") or {}
            rec.cost_usd = float(usage.get("cost_usd") or 0)
            rec.served_model = headers.get("otari-model", data.get("model", model))
            rec.provider = headers.get("otari-provider", "")
            rec.fallback = "client" if model != models[0] else headers.get("otari-fallback", "")
            self.ledger.add(rec)
            vecs = [d["embedding"] for d in sorted(data.get("data", []), key=lambda d: d.get("index", 0))]
            return vecs, rec
        raise last or OtariError(500, "no embedding model in chain")


def content_of(data: Dict[str, Any]) -> str:
    try:
        return (data["choices"][0]["message"].get("content") or "").strip()
    except (KeyError, IndexError, TypeError):
        return ""


def parse_json_block(text: str) -> Dict[str, Any]:
    """Lenient JSON extraction: plain JSON, ```json fences, or first {...} span."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.strip("`")
        t = t[4:] if t.lower().startswith("json") else t
    try:
        v = json.loads(t)
        return v if isinstance(v, dict) else {}
    except ValueError:
        pass
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end > start:
        try:
            v = json.loads(t[start:end + 1])
            return v if isinstance(v, dict) else {}
        except ValueError:
            return {}
    return {}
