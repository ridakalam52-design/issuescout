"""Which open-weight model serves which role, and how each role falls back.

Every chain starts with an Otari routing policy name where one makes sense
(created once in the dashboard: Routing -> Create policy -> Fallback). The
policy does the server-side failover; the concrete models after it are a
client-side safety net for workspaces that have not created the policy.
Override any chain with env vars, e.g.
ISSUESCOUT_MODELS_WRITER="mistralai/mistral-small-4,deepseek/deepseek-v4.1-flash-1017".
"""
from __future__ import annotations

import os
from typing import Dict, List

DEFAULT_CHAINS: Dict[str, List[str]] = {
    # Untrusted issue text and drafted replies are screened by open safety models.
    "guard": ["meta/llama-guard-4-12b", "alibaba/qwen3guard-gen-0.6b"],
    # Small, cheap, JSON-mode classifier (policy: Qwen3-30B-A3B -> Ministral 8B).
    "classifier": ["issuescout-classifier", "alibaba/qwen3-30b-a3b-instruct-2507", "mistralai/ministral-3-8b"],
    # Embeddings for duplicate detection.
    "embedder": ["alibaba/qwen3-embedding-0.6b", "bge-m3"],
    # Tool-using researcher: Otari web search/fetch + MCP (DeepWiki).
    "researcher": ["deepseek/deepseek-v4.1-flash-1017", "alibaba/qwen3-235b-a22b-instruct-2507"],
    # Drives Otari's sandboxed code execution for repros. (Qwen3-Coder via its Bedrock
    # route and Codestral did not reliably call otari_code_execution in testing.)
    "reproducer": ["deepseek/deepseek-v4.1-flash-1017", "alibaba/qwen3-235b-a22b-instruct-2507"],
    # Reply writer (policy: DeepSeek V4.1 Flash -> Qwen3-235B).
    "writer": ["issuescout-writer", "deepseek/deepseek-v4.1-flash-1017", "alibaba/qwen3-235b-a22b-instruct-2507"],
}


def chain(role: str) -> List[str]:
    env = os.environ.get(f"ISSUESCOUT_MODELS_{role.upper()}")
    if env:
        return [m.strip() for m in env.split(",") if m.strip()]
    return list(DEFAULT_CHAINS[role])


# Public MCP server used for repo-aware research. If the workspace has
# registered it (Tools -> MCP servers), set ISSUESCOUT_MCP_SERVER_IDS to its
# UUID(s) and the request references it by id instead of inlining the URL.
DEEPWIKI_MCP = {
    "name": "deepwiki",
    "url": "https://mcp.deepwiki.com/mcp",
    "purpose_hint": "Ask questions about a public GitHub repository's code and docs (repoName is owner/name).",
    "allowed_tools": ["ask_wiki_question", "read_wiki_structure", "read_wiki_contents"],
}


def mcp_fields() -> Dict[str, object]:
    ids = [s.strip() for s in os.environ.get("ISSUESCOUT_MCP_SERVER_IDS", "").split(",") if s.strip()]
    if ids:
        return {"mcp_server_ids": ids}
    if os.environ.get("ISSUESCOUT_DISABLE_MCP"):
        return {}
    return {"mcp_servers": [DEEPWIKI_MCP]}


def guardrail_entries() -> List[Dict[str, object]]:
    """Request-level Otari guardrails, e.g. ISSUESCOUT_GUARDRAIL_PROFILES=prompt-injection.

    Sent in monitor mode so a missing guardrail service never blocks triage;
    the verdict comes back in the Otari-Guardrails header and is recorded.
    """
    profiles = [p.strip() for p in os.environ.get("ISSUESCOUT_GUARDRAIL_PROFILES", "").split(",") if p.strip()]
    return [{"profile": p, "mode": "monitor", "on": ["input"], "on_unavailable": "monitor"} for p in profiles]
