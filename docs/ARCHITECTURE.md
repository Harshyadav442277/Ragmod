# Ragmod architecture

## What it is

Ragmod is a **retrieval agent for codebases**. You point it at a repository and
ask a question in plain language; it searches, reads files, and answers with
`file:line` citations.

It is agentic rather than single-shot on purpose. Retrieval happens through
**tools**, so every chunk of retrieved code arrives as a `tool_result` — which is
exactly the content Paritok's 4B model was trained to compress. The compression
stage is not decoration; it is what makes the retrieval policy affordable.

## Why this shape

Paritok compresses tool results, accumulated history, and tool schemas. It does
not compress a system prompt or a hand-assembled user message. Three design
consequences follow, and they define the product:

| Paritok behaviour | What Ragmod does about it |
|---|---|
| Compresses `tool_result` blocks | Retrieval is a tool, never inlined into the prompt |
| Compresses history past a window | The agent is multi-turn and iterative, not one-shot |
| Stubs unused tool schemas | We declare a real toolset, not one function |
| Trained on `file_read` / `bash_command` / `log_output` | The corpus is source code, not prose |

## Request path

```
User question
  → Ragmod agent loop
      → tool call: search_repo / read_file / list_dir / run_tests
      → tool_result (large, generous spans of real code)
  ★ Paritok proxy compresses tool results + old history, stubs unused schemas ★
      → Anthropic / OpenAI  (billed on compressed input)
  ← answer, or another tool call
  → cited answer + savings report from /stats
```

Every LLM call leaves through the proxy. There are no direct calls to a provider
SDK endpoint anywhere in the runtime.

## The over-retrieval policy

This is the part that is ours rather than Paritok's.

A normal code-RAG tool returns tight snippets — a few dozen lines — because
context is expensive. Ragmod does the opposite: `read_file` returns whole
functions with surrounding context, and `search_repo` returns many hits rather
than the top three. Recall goes up, and the cost of that recall is absorbed by
compression instead of by the bill.

The claim we then measure is: **higher recall per turn at lower token cost than
the tight-snippet baseline.**

## Modules

Deliberately small. Each is one file or one small package.

| Module | Responsibility |
|---|---|
| `tools/` | `search_repo` (ripgrep), `read_file`, `list_dir`, `run_tests` |
| `agent/` | Tool-calling loop, turn management, citation extraction |
| `gateway/` | Paritok proxy lifecycle, `paritok.yaml`, base-URL wiring |
| `bench/` | A/B harness: same task set with and without the proxy |
| `cli/` | `ragmod ask`, `ragmod bench` |

No vector database, no embedding index, no document ingestion pipeline, no web
UI. Ripgrep over a checked-out repo is both sufficient and on-distribution for
the compressor. If time remains after the submission is complete, a semantic
index is the first thing to add — not before.

## Interfaces to freeze before any code

These are the only shared contracts; workers stub against them and never
redefine them.

```python
ToolResult   = { "name": str, "content": str, "meta": dict }
Citation     = { "path": str, "start": int, "end": int }
AgentAnswer  = { "text": str, "citations": list[Citation], "turns": int }
SavingsStats = { "original": int, "compressed": int, "ratio": float,
                 "saved": int, "cost_saved_usd": str }
```

## Non-goals

- Hosting a public instance that spends our API keys on anonymous traffic
- Beating Paritok's published 74% figure; we report our own measured number
- Supporting non-code corpora in v1
- Any feature that does not appear in the demo video or the measurement
