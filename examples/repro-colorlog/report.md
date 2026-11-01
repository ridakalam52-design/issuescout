# IssueScout triage report: `borntyping/python-colorlog`

Generated 2026-11-01 09:17 UTC · engine: **otari** · dry run (nothing was written to GitHub)

Model + tool spend for this run: **$0.0210**

| # | Title | Category | Priority | Labels | Possible duplicates |
|---|---|---|---|---|---|
| [#143](https://github.com/borntyping/python-colorlog/issues/143) | Cached exception colors leak into no_color and standard formatters | bug | P1 | colorlog, exception, formatter, bug | - |

## #143: Cached exception colors leak into no_color and standard formatters

- **Category:** bug  ·  **Priority:** P1  ·  **Labels:** colorlog, exception, formatter, bug
- **Why:** The issue breaks core logging functionality by leaking colored exception formatting into non-color contexts due to shared caching of exception text.
- **Guardrail:** safe (meta-llama/Llama-Guard-4-12B)
- **Repro (Otari sandbox, deepseek-ai/DeepSeek-V4.1-Flash-1017):** reproduced: After formatting with force_color, the no_color formatter's output still contains ANSI escapes (e.g. '\x1b[35m' in the traceback), so the assertion fails with AssertionError.
- **Related docs / known fixes:**
  - [logging — Logging facility for Python (Formatter.format / exc_text caching)](https://docs.python.org/3/library/logging.html): Documents that Formatter.format caches formatException output in record.exc_text, the shared cache behind this bug. _(via otari_web_search/fetch)_
  - [borntyping/python-colorlog](https://github.com/borntyping/python-colorlog): Upstream repo where ColoredFormatter.formatException/_colorize live; place to check for a fix or PR. _(via otari_web_search/fetch)_

**Draft maintainer reply:**

> Thanks for the detailed report and the minimal repro — very helpful.
> 
> I ran the repro in IssueScout's sandbox (not on a maintainer's machine), and it reproduces: after the `force_color` formatter runs, the `no_color` formatter's output still contains ANSI escapes (e.g. `\x1b[35m` in the traceback), so the assertion fails with `AssertionError`. I've triaged this as a P1 bug under the `colorlog`/`exception`/`formatter` labels.
> 
> Your diagnosis matches what I see: `logging.Formatter.format` caches `formatException` output in `record.exc_text`, and that cache is shared across handlers even though traceback coloring is per-formatter. The usual workaround is to clear the cache per formatter (e.g. `record.exc_text = None` before formatting, or override `format` to avoid reusing `exc_text`). No upstream fix is confirmed yet.
> 
> Useful references: the Python logging docs on `Formatter.format`/`exc_text` caching (https://docs.python.org/3/library/logging.html) and the upstream repo (https://github.com/borntyping/python-colorlog).
> 
> To confirm scope: does this also occur when the two formatters are attached to separate handlers on the same logger, and on Python 3.12 or earlier?

<details><summary>Otari gateway trace</summary>

| role | requested (model or routing policy) | served by | provider | fallback | Otari tools | cost USD |
|---|---|---|---|---|---|---|
| guard | meta/llama-guard-4-12b | meta-llama/Llama-Guard-4-12B | deepinfra | false | - | 9.8e-05 |
| classifier | issuescout-classifier | Qwen/Qwen3-30B-A3B-Instruct-2507 | nebius | false | - | 7e-05 |
| reproducer | deepseek/deepseek-v4.1-flash-1017 | deepseek-ai/DeepSeek-V4.1-Flash-1017 | deepinfra | false | - | 0.010192 |
| researcher | deepseek/deepseek-v4.1-flash-1017 | deepseek-ai/DeepSeek-V4.1-Flash-1017 | deepinfra | false | web_search: python logging Formatter exc_text cache shared handlers colorlog traceback color leak | 0.010425 |
| writer | issuescout-writer | deepseek-ai/DeepSeek-V4.1-Flash-1017 | deepinfra | false | - | 0.000168 |
| guard | meta/llama-guard-4-12b | meta-llama/Llama-Guard-4-12B | deepinfra | false | - | 8.8e-05 |

</details>
