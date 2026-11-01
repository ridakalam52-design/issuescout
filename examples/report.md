# IssueScout triage report: `mozilla-ai/otari`

Generated 2026-11-01 09:17 UTC · engine: **otari** · dry run (nothing was written to GitHub)

Model + tool spend for this run: **$0.0434**

Batch step `embedder`: alibaba/qwen3-embedding-0.6b served by alibaba/qwen3-embedding-0.6b (-), $1.2e-05

| # | Title | Category | Priority | Labels | Possible duplicates |
|---|---|---|---|---|---|
| [#2742](https://github.com/mozilla-ai/otari/issues/2742) | [BUG] Sign-in on otari.ai says "wrong email or password" in private/incognito windows, works in a normal window | bug | P1 | signin, private-mode, authentication | - |
| [#2741](https://github.com/mozilla-ai/otari/issues/2741) | [BUG] Hosted quickstart base URL (api.otari.ai/v1) doesn’t match the API (/api/v1, region-specific host) | bug | P2 | api, docs, quickstart | - |
| [#2740](https://github.com/mozilla-ai/otari/issues/2740) | [FEATURE] Faster transcript parsing in the Stop hook command collector | feature | P2 | performance, optimization, cli | - |
| [#2738](https://github.com/mozilla-ai/otari/issues/2738) | [FEATURE] feat(gateway): Support X-Otari-End-User-Id header for multi-tenant per-end-user budget caps and guardrail telemetry headers | feature | P1 | feature, multi-tenant, budgeting, telemetry | - |

## #2742: [BUG] Sign-in on otari.ai says "wrong email or password" in private/incognito windows, works in a normal window

- **Category:** bug  ·  **Priority:** P1  ·  **Labels:** signin, private-mode, authentication
- **Why:** Sign-in fails in private/incognito mode despite working in normal mode, indicating a core authentication flow issue.
- **Guardrail:** safe (meta-llama/Llama-Guard-4-12B)
- **Related docs / known fixes:**
  - [Signup, email verification, and password reset · Issue #650 · mozilla-ai/otari](https://github.com/mozilla-ai/otari/issues/650): Related auth/sign-in work in the same repo (closed via PR #708); may touch the sign-in path. _(via otari_web_search/fetch)_

**Draft maintainer reply:**

> Thanks for the detailed report, @orjinameh — the steps and the cross-browser, two-account reproduction are genuinely helpful.
> 
> Triage: we're treating this as a **bug** (P1) affecting sign-in in private/incognito windows. The pattern — correct credentials rejected only in private mode, across three browsers including Safari — points at something in the sign-in path behaving differently when storage/cookies are restricted, but that's a hypothesis, not a confirmed cause. No known fix yet, and I can't promise a timeline.
> 
> I didn't run a repro (none was provided), so nothing has been verified in IssueScout's sandbox.
> 
> Possibly related: #650 (signup, email verification, and password reset — https://github.com/mozilla-ai/otari/issues/650), which touches the auth/sign-in path.
> 
> To narrow it down, could you share:
> 1. The exact browser versions you tested.
> 2. Whether the private window shows any console errors or failed network requests on submit (redact anything sensitive).
> 3. Whether the failure also happens if you first load the sign-in page in a normal window, then switch to private.

<details><summary>Otari gateway trace</summary>

| role | requested (model or routing policy) | served by | provider | fallback | Otari tools | cost USD |
|---|---|---|---|---|---|---|
| guard | meta/llama-guard-4-12b | meta-llama/Llama-Guard-4-12B | deepinfra | false | - | 8.2e-05 |
| classifier | issuescout-classifier | Qwen/Qwen3-30B-A3B-Instruct-2507 | nebius | false | - | 5.9e-05 |
| researcher | deepseek/deepseek-v4.1-flash-1017 | deepseek-ai/DeepSeek-V4.1-Flash-1017 | deepinfra | false | web_search: otari.ai sign-in fails in incognito private window wrong email or password | 0.010358 |
| writer | issuescout-writer | deepseek-ai/DeepSeek-V4.1-Flash-1017 | deepinfra | false | - | 0.000123 |
| guard | meta/llama-guard-4-12b | meta-llama/Llama-Guard-4-12B | deepinfra | false | - | 8.1e-05 |

</details>

## #2741: [BUG] Hosted quickstart base URL (api.otari.ai/v1) doesn’t match the API (/api/v1, region-specific host)

- **Category:** bug  ·  **Priority:** P2  ·  **Labels:** api, docs, quickstart
- **Why:** The quickstart documentation provides an incorrect base URL that leads to immediate errors, requiring users to debug region-specific routing.
- **Guardrail:** safe (meta-llama/Llama-Guard-4-12B)
- **Related docs / known fixes:**
  - [OtariChatGenerator | Haystack Documentation](https://docs.haystack.deepset.ai/docs/otarichatgenerator): Third-party integration docs already state the hosted default is https://api.otari.ai/api/v1, confirming the /api/v1 prefix. _(via otari_web_search/fetch)_
  - [Use the Otari Gateway with OpenCode (mozilla.ai blog)](https://blog.mozilla.ai/use-the-otari-gateway-with-opencode): Official mozilla.ai post showing how the hosted gateway base URL is configured for a client. _(via otari_web_search/fetch)_
  - [DeepWiki: base URL / region handling in mozilla-ai/otari](https://deepwiki.com/search/what-base-url-does-the-hosted_3c746c37-6376-4559-af36-cbe8f36943a1): Explains /v1 is the self-hosted gateway prefix while /api/v1 is the platform prefix, with PLATFORM_BASE_URL for region hosts. _(via model/MCP)_

**Draft maintainer reply:**

> Thanks for the detailed report, @orjinameh — the curl transcripts make the failure mode very clear.
> 
> Triage: this is a **docs bug** (P2, labels: api/docs/quickstart). The quickstart conflates two different base URLs: the self-hosted gateway prefix (`/v1`, e.g. `http://localhost:8000/v1`) and the hosted platform API (`/api/v1`, default `https://api.otari.ai/api/v1`, with region hosts like `eu.api.otari.ai` via `PLATFORM_BASE_URL`). The fix is to document `https://<region>.api.otari.ai/api/v1` in the quickstart and show the full region-specific URL when a key is created. No duplicate issues found. No repro was run in IssueScout's sandbox, since none was attached.
> 
> Useful references:
> - [OtariChatGenerator docs](https://docs.haystack.deepset.ai/docs/otarichatgenerator) — confirms the hosted default includes `/api/v1`
> - [mozilla.ai blog: Otari Gateway with OpenCode](https://blog.mozilla.ai/use-the-otari-gateway-with-opencode)
> - [DeepWiki: base URL / region handling](https://deepwiki.com/search/what-base-url-does-the-hosted_3c746c37-6376-4559-af36-cbe8f36943a1)
> 
> To scope the fix, could you share the exact quickstart page/section you followed (URL or heading)?

<details><summary>Otari gateway trace</summary>

| role | requested (model or routing policy) | served by | provider | fallback | Otari tools | cost USD |
|---|---|---|---|---|---|---|
| guard | meta/llama-guard-4-12b | meta-llama/Llama-Guard-4-12B | deepinfra | false | - | 0.000103 |
| classifier | issuescout-classifier | Qwen/Qwen3-30B-A3B-Instruct-2507 | nebius | false | - | 7.2e-05 |
| researcher | deepseek/deepseek-v4.1-flash-1017 | deepseek-ai/DeepSeek-V4.1-Flash-1017 | deepinfra | false | web_search: otari.ai API base URL /api/v1 quickstart | 0.010443 |
| writer | issuescout-writer | deepseek-ai/DeepSeek-V4.1-Flash-1017 | deepinfra | false | - | 0.000188 |
| guard | meta/llama-guard-4-12b | meta-llama/Llama-Guard-4-12B | deepinfra | false | - | 9.6e-05 |

</details>

## #2740: [FEATURE] Faster transcript parsing in the Stop hook command collector

- **Category:** feature  ·  **Priority:** P2  ·  **Labels:** performance, optimization, cli
- **Why:** Improves parsing speed of transcript lines without changing behavior, with measurable performance gains on large transcripts.
- **Guardrail:** safe (meta-llama/Llama-Guard-4-12B)
- **Related docs / known fixes:**
  - [json — JSON encoder and decoder — Python documentation](https://docs.python.org/3/library/json.html): Documents JSONDecoder.raw_decode/decode semantics the proposal relies on (raw_decode returns value plus end index, doesn't require whole-string consumption). _(via otari_web_search/fetch)_
  - [Python 2.6 JSON decoding performance (Stack Overflow)](https://stackoverflow.com/questions/706101/python-2-6-json-decoding-performance): Prior discussion of reusing a decoder / avoiding per-call overhead in json.loads, relevant to the proposed micro-optimization. _(via otari_web_search/fetch)_

**Draft maintainer reply:**

> Thanks for the detailed write-up and the profiling numbers — this is a well-scoped performance proposal.
> 
> Triage outcome: I'm treating this as a **feature/optimization request (P2)** with `performance`, `optimization`, and `cli` labels. No duplicates found so far. There's no upstream fix, so the approach you describe is the one on the table. Two references that back the design: the [`json` module docs](https://docs.python.org/3/library/json.html) (on `raw_decode` returning value + end index without requiring full-string consumption) and this [prior discussion of JSON decoding overhead](https://stackoverflow.com/questions/706101/python-2-6-json-decoding-performance).
> 
> One caveat: I couldn't verify the code path — the indexed source doesn't appear to include `cli/src/otari_agent/hook.py`, and there's no repro to run in the sandbox.
> 
> To move this forward, could you share:
> 1. A minimal repro or the exact command/transcript fixture used for the timings.
> 2. Confirmation of the Python version(s) you'd want this validated against.
> 
> No timeline promised, but this looks reasonable.

<details><summary>Otari gateway trace</summary>

| role | requested (model or routing policy) | served by | provider | fallback | Otari tools | cost USD |
|---|---|---|---|---|---|---|
| guard | meta/llama-guard-4-12b | meta-llama/Llama-Guard-4-12B | deepinfra | false | - | 0.000124 |
| classifier | issuescout-classifier | Qwen/Qwen3-30B-A3B-Instruct-2507 | nebius | false | - | 8.4e-05 |
| researcher | deepseek/deepseek-v4.1-flash-1017 | deepseek-ai/DeepSeek-V4.1-Flash-1017 | deepinfra | false | web_search: Python json raw_decode faster than loads per line JSONDecoder reuse performance | 0.010352 |
| writer | issuescout-writer | deepseek-ai/DeepSeek-V4.1-Flash-1017 | deepinfra | false | - | 0.000155 |
| guard | meta/llama-guard-4-12b | meta-llama/Llama-Guard-4-12B | deepinfra | false | - | 8.2e-05 |

</details>

## #2738: [FEATURE] feat(gateway): Support X-Otari-End-User-Id header for multi-tenant per-end-user budget caps and guardrail telemetry headers

- **Category:** feature  ·  **Priority:** P1  ·  **Labels:** feature, multi-tenant, budgeting, telemetry
- **Why:** Enables critical multi-tenant support and observability for production-grade AI applications.
- **Guardrail:** safe (meta-llama/Llama-Guard-4-12B)
- **Related docs / known fixes:**
  - [Otari: Own Your AI Stack (blog)](https://blog.mozilla.ai/otari-own-your-ai-stack): Official announcement describing Otari's usage tracking, budget controls and routing policies — relevant to the per-user budget part of the request. _(via otari_web_search/fetch)_
  - [Cloudflare AI Gateway spend limits](https://developers.cloudflare.com/ai-gateway/features/spend-limits): Prior art: cost-based spend limits scoped by custom metadata like user ID, returning 429 when exceeded. _(via otari_web_search/fetch)_
  - [LangChain LLM Gateway spend policies](https://docs.langchain.com/langsmith/llm-gateway-spend-policies): Prior art: per-user/API-key spend caps over time windows with blocked-request errors. _(via otari_web_search/fetch)_

**Draft maintainer reply:**

> Thanks for the detailed write-up, @sanjaysah101 — the TinyFlow AI context and the glue-code list make the request easy to follow.
> 
> Triage outcome: we're treating this as a **feature request** (P1) covering two parts — per-end-user budget caps and response telemetry headers. No duplicate issues were found.
> 
> Some of this may already be partly covered: Otari's budget system (Reserve-Reconcile-Refund) supports per-user `max_budget`/`budget_duration_sec`, and the OpenAI `user` field is used for spend tracking (with `reject_user_mismatch` controlling whether a non-master key may bill another user). What doesn't exist yet is the `X-Otari-End-User-Id` header and the `x-otari-cost-usd` / `x-otari-provider-used` / `x-otari-guardrail-triggered` response headers. Related prior art worth a look:
> - [Otari: Own Your AI Stack](https://blog.mozilla.ai/otari-own-your-ai-stack)
> - [Cloudflare AI Gateway spend limits](https://developers.cloudflare.com/ai-gateway/features/spend-limits)
> - [LangChain LLM Gateway spend policies](https://docs.langchain.com/langsmith/llm-gateway-spend-policies)
> 
> To scope this, could you share: (1) the exact middleware/request shape you use today, and (2) whether the OpenAI `user` field alone would meet your needs, or the dedicated header is required?

<details><summary>Otari gateway trace</summary>

| role | requested (model or routing policy) | served by | provider | fallback | Otari tools | cost USD |
|---|---|---|---|---|---|---|
| guard | meta/llama-guard-4-12b | meta-llama/Llama-Guard-4-12B | deepinfra | false | - | 0.000116 |
| classifier | issuescout-classifier | Qwen/Qwen3-30B-A3B-Instruct-2507 | nebius | false | - | 8.1e-05 |
| researcher | deepseek/deepseek-v4.1-flash-1017 | deepseek-ai/DeepSeek-V4.1-Flash-1017 | deepinfra | false | web_search: mozilla-ai otari gateway budget per-user spend cap headers | 0.010501 |
| writer | issuescout-writer | deepseek-ai/DeepSeek-V4.1-Flash-1017 | deepinfra | false | - | 0.000195 |
| guard | meta/llama-guard-4-12b | meta-llama/Llama-Guard-4-12B | deepinfra | false | - | 9.5e-05 |

</details>
