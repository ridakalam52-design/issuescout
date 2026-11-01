# Otari hackathon feedback (draft answers)

Everything below is friction I actually hit while building IssueScout against hosted Otari
(`api.otari.ai`, free workspace with the $2 welcome credit) on 2026-11-01.

## When were you most tempted to skip Otari and call the provider directly?

**Guardrails.** Otari already serves Llama Guard 4 and Qwen3Guard as models, but every hosted guardrail in
*Organization → Guardrails* (prompt injection, PII, toxicity, …) needs a third-party vendor key
(Lakera, Patronus, Azure, Bedrock, OpenAI, watsonx, Alinia). A request-level `guardrails` entry for
`prompt-injection` was accepted but came back `"valid": null` in `Otari-Guardrails`, with no explanation.
`POST /api/v1/moderations` with `meta/llama-guard-4-12b` answered "model not found on the provider". So I came close
to wiring Llama Guard in myself outside the gateway. In the end I kept it inside Otari as an ordinary chat completion
(its own "guard" role), but the guardrail is my code, not an Otari feature.

**Second, the first 10 minutes.** The hosted quickstart says `https://api.otari.ai/v1`, but that returns 404.
The working base URL is `https://api.otari.ai/api/v1`. (Someone else filed the same thing as mozilla-ai/otari#2741 the
same day.) When the very first curl fails, you're tempted to go back to a provider SDK you know works.

**Third, code execution with some models.** `alibaba/qwen3-coder-30b-a3b-instruct` with `otari_code_execution` was routed
to Bedrock and failed with *"The toolConfig field must be defined when using toolUse and toolResult content blocks"*
(with `tool_choice: required`). Without it, the model answered without ever calling the sandbox. `mistralai/codestral-latest`
just replied with the literal text `code_execution`. Both are listed as supporting `tools` in `/models`.
DeepSeek V4.1 Flash worked first time. I'd like `/models` to say which models actually drive gateway-run tools reliably.

## What did you build yourself that Otari should've done?

1. **A fallback chain without provider keys.** Chat Completions takes one `model`, and there's no request-level
   `models`/`fallbacks` list. The hosted guide says routing policies only route across your *own* provider keys and skip
   wallet-billed models. Yet the dashboard happily let me create `issuescout-writer` / `issuescout-classifier` from managed
   models, and they work. The docs contradict each other here, so I also built a client-side chain
   (`policy → model A → model B`) in `otari_client.py` in case the policy is missing or refused.
2. **A spend ledger.** A workspace key can't read its own budget or remaining spend (`/budgets` and `/usage` need the master
   key), so the app can't tell it's at 90% before a 402. I add up `usage.cost_usd` from every response and enforce a per-run
   cap client-side. A `Otari-Budget-Remaining` response header would remove this code.
3. **Proof that the sandbox ran.** On Chat Completions, `otari_tool_calls` lists web searches and fetches (with sources, which
   is great), but **not** code-execution calls. A model can claim "I ran it and it reproduced" without running anything.
   I check whether the request was billed the ~$0.01 sandbox fee before trusting a repro.
4. **Per-end-user budgets.** The `user` field must name an existing Otari user, and `/end-users` needs a service key.
   A workspace key can only *tag* requests (`safety_identifier`, `metadata.user`) for attribution. The per-user cap
   I could set is per workspace *member* (dashboard), not per end user of my app. (mozilla-ai/otari#2738 asks for exactly this.)
5. **An open-model guardrail** (see above).

## Smaller things worth fixing

- Web search **and** web fetch are off per workspace by default, and the errors (`web search is not enabled for this workspace`,
  `web access is not enabled for this workspace`) don't say where to turn them on (*Tools → Web search → Web access*).
- `otari_web_search` accepts `max_uses`, but `otari_web_fetch` rejects it: *"otari_web_fetch declarations may contain only the type field"*.
- MCP: an `allowed_tools` list naming a tool the server doesn't have (`ask_question` vs DeepWiki's `ask_wiki_question`)
  silently exposed **zero** tools. The model then confidently made up an answer about the repo. A warning header,
  or a 400 like the one for name collisions, would have saved me time.
- Gateway-run tools cost $0.01 per call, about 100× the tokens of a small-model request. That's fine, but with a $2
  credit it dominates the bill. `max_uses` is the right control. The free credit runs out fast for tool-heavy agents.

## What worked really well

- One request combining `otari_web_search` + `otari_web_fetch` + an MCP server (by `mcp_server_ids`) worked first try,
  with Otari running the whole tool loop.
- `Otari-Model`, `Otari-Provider`, `Otari-Fallback` and `Otari-Attempt-Count` on every response made a per-call trace trivial.
  I show them in every report.
- Routing policy names show up in `/models` and work as a drop-in `model` value.
- The docs' `?ask=` endpoint answered a routing question that the pages themselves contradicted.
- Open-weight models for every role, from a 0.6B embedding model to Llama Guard to DeepSeek, behind one key and one bill.

## Would you continue using Otari without the rule?

**Probably yes, for agent-style apps like this one.** The built-in tools (search, fetch, sandbox) and MCP behind one
OpenAI-compatible endpoint replaced three integrations I'd otherwise write and pay for separately. Per-call serving
headers and per-role cost attribution are things I'd want anyway. What would make it a clear yes: a working
open-model guardrail with no vendor key, code-execution calls in `otari_tool_calls`, a remaining-budget header for
workspace keys, and docs that agree on whether routing policies work with managed models. For a single-model chatbot
I'd still be tempted to call the provider directly.
