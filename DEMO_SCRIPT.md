# IssueScout: demo video script (about 4 minutes)

**Setup before recording:** terminal in the repo on branch `otari-hackathon`, `OTARI_API_KEY` exported (never shown on
screen), `ISSUESCOUT_MCP_SERVER_IDS` set to the workspace's DeepWiki server, the otari.ai dashboard open in a browser tab,
and `examples/report.html` ready in another tab.

---

### 0:00–0:25 · The problem
**Screen:** github.com/mozilla-ai/otari/issues (a busy issue list).

> "Maintainers of popular repos spend hours a week just triaging: is it a bug, is it a duplicate, can I reproduce it,
> is there already a doc for this? IssueScout is an open-source agent that does that first pass for you. It does it
> entirely on open-weight models through Mozilla's Otari gateway, and it never touches your repo unless you tell it to."

### 0:25–0:55 · Architecture in one picture
**Screen:** README mermaid diagram.

> "Six roles, six model choices. Llama Guard 4 screens untrusted issue text. Qwen3 embeddings find duplicates.
> A small Qwen3-30B classifier picks category, labels and priority. DeepSeek drives Otari's sandbox to reproduce bugs,
> and researches with Otari web search, web fetch and a DeepWiki MCP server. Then a writer drafts the reply,
> and the guard checks it again. Every call goes through one Otari key."

### 0:55–1:20 · Doctor
**Run:** `issuescout doctor`

> "Doctor asks Otari which built-in tools this workspace has. Web search, fetch and code execution are all on.
> It also lists each role's model chain. The first entries for classifier and writer are Otari routing policies,
> not raw models."

**Cut to dashboard → Routing:** show `issuescout-writer` (DeepSeek V4.1 Flash → Qwen3-235B) and `issuescout-classifier`.

### 1:20–2:20 · Live run
**Run:** `issuescout triage mozilla-ai/otari --limit 3 --user rida --max-spend 0.10 --out out`

> "Three live issues from Otari's own repo. It's a dry run: GitHub is only read. `--max-spend` is a client-side
> cap, and `--user` tags every request so Otari can attribute spend per user."

While it runs (about a minute), **switch to dashboard → Spend & Budgets:** show the `issuescout-hackathon` workspace ceiling
($1.50/month) and the per-member `issuescout-per-user` budget ($1/day).

> "On the server side Otari enforces a workspace spend ceiling and a per-member daily budget. If either runs out,
> IssueScout catches the 402 and stops cleanly, keeping rule-based results for the rest."

**Back to terminal:** point at `Otari spend this run: $0.03…`.

### 2:20–3:20 · The report
**Screen:** `out/report.html` (or `examples/report.html`).

- Issue #2741 (wrong quickstart base URL): category bug, P2, labels. Scroll to **Related docs**: links found by
  Otari web search and a DeepWiki MCP answer about the codebase. Read one sentence of the drafted reply.
- Open **Otari gateway trace**: requested `issuescout-classifier` → served by Qwen3-30B on Nebius; `issuescout-writer`
  → DeepSeek on DeepInfra; the `web_search` query; the cost of each call.

> "Every step is visible: which policy I asked for, which open model and provider actually served it, whether Otari fell
> back, which tools ran, and what it cost. That's under five cents for the whole batch."

### 3:20–3:50 · Sandbox repro
**Screen:** `examples/repro-colorlog/report.html` (borntyping/python-colorlog#143).

> "When a bug report includes a Python snippet, IssueScout runs it in Otari's code-execution sandbox. Here it installed
> colorlog, ran the reporter's snippet, and confirmed the ANSI-leak bug really reproduces. And because Chat Completions
> doesn't list sandbox calls, IssueScout checks the billing to make sure the model didn't just claim it ran."

### 3:50–4:10 · Guardrail + close
**Run:** `python -m unittest discover tests` (16 passing), and show the test where a prompt-injection issue gets
`needs-human-review` and nothing past the guard runs.

> "Prompt-injected issues never reach the other models. IssueScout is MIT-licensed, dry-run by default, and `--apply`
> writes labels and replies only with your token. Thanks for watching."

---

**Optional 15-second fallback demo:**
`ISSUESCOUT_MODELS_WRITER="nope/not-a-model,issuescout-writer" issuescout triage mozilla-ai/otari --limit 1 --no-research --no-repro`.
The trace shows the failed first entry and the fallback that served the reply.
