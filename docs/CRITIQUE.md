# Critique of the v1 architecture

Written after reading Paritok's actual README and proxy behaviour. The v1 plan
was built on an assumption about *where* Paritok compresses. That assumption was
wrong, and it invalidated the central mechanism.

## Fatal: Paritok does not compress the prompt we were planning to build

v1 said: retrieve aggressively → assemble a "fat context bus" → send it through
the proxy → Paritok compresses it.

Paritok's middleware runs four steps, and none of them touch a large user
message:

1. Tool discovery — stubs tool schemas beyond the top-K relevant ones
2. Compress **tool outputs** — each `tool_result` block, via the 4B model
3. Compress **old history** — turns beyond the recent window
4. Inject `expand_context` / `gateway_search_tools` for recall

Its own `/stats` documentation is explicit that measurement is "scoped to what
Paritok actually intervenes in — the content it compresses (tool results / file
reads / old history) plus the tool schemas it stubs. Everything it can't affect
(your system prompt, the model's output) is deliberately excluded."

A RAG app that stuffs retrieved chunks into one user message would show
**near-zero savings**. We would have shipped a project whose headline metric was
zero on the criterion worth the most points.

## Fatal: single-turn Q&A is a documented poor fit

Paritok's README lists, under "less useful when": *"Your workflow is single-turn
Q&A (context doesn't accumulate)."* Classic RAG is exactly single-turn Q&A. Two
of the four compression stages (history, tool discovery) only pay off across
turns.

## Wrong corpus

The model is trained on 45K coding-agent trajectories — `file_read`,
`bash_command`, `log_output` — and is described as Python-heavy. It "protects
function names, paths, and error strings." Compressing lecture PDFs and prose
notes runs it off-distribution, so both compression ratio and retention would be
worse than the published numbers, and we would have no explanation for judges.

## Reinvented measurement

v1's "Savings Lab" designed its own token accounting. The proxy already exposes
`/stats` with original tokens, compressed tokens, ratio, tokens saved, and a
cache-aware cost estimate, and the hosted dashboard reports on the same basis.
Building a parallel counter creates a number that disagrees with the judges'
verification surface. We should read `/stats` and compare against it, not
replace it.

## Scope and process bloat for a 4-day, 2-person build

- **7 parallel Composer workers** across ingest, retrieve, Paritok, API, UI,
  eval, and submission. With two humans reviewing, integration cost would exceed
  the build cost. Cut to three sequential-ish workstreams.
- **Hybrid BM25 + dense retrieval, embeddings, PDF ingest, multi-hop planner,
  chat UI** is roughly a month of work. None of it is required by the rules.
- **Wave gates and an orchestrator charter** are process theatre at this size.
  Keep the orchestrator, drop the ceremony.

## Overclaiming the metric

v1 set "~74%" as a target to prove. That number is Paritok's benchmark on its
own workload; ours will be whatever our workflow produces. Judges reward a real
measured reduction, and at least one existing gallery entry documents a case
where naive use made the bill go *up* (the `expand_context` double-POST issue).
Reporting our own honest number, with the method shown, is both safer and more
persuasive.

## Demo hosting risk

v1 listed "public demo URL" as an exit criterion. A hosted demo would run our
Paritok key and our provider key against arbitrary input from the internet. The
rules accept "your repo with clear setup instructions" as the project URL. Ship
a one-command local demo plus recorded artifacts instead.

## What survives

- Paritok as a mandatory, load-bearing stage rather than a bolt-on
- The over-retrieval wedge — but expressed as generous **tool results**, which
  is the thing Paritok actually compresses
- Grok orchestrator with Composer workers, at reduced width
- Measurement as the centrepiece of the submission

The corrected design is in [ARCHITECTURE.md](ARCHITECTURE.md); the mechanism and
measurement method are in [PARITOK.md](PARITOK.md).
