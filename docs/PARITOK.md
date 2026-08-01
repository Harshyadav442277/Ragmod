# Paritok integration and measurement

This is the file to read if you want to verify that Paritok is doing real work
in Ragmod and that our reported savings are honest. It is also the basis of the
Devpost write-up.

Built with [Paritok](https://github.com/Paritok-official/paritok-4b-v1).

## How Paritok actually works

Paritok is a middleware proxy between the agent and the LLM provider. On every
request it runs four steps before forwarding upstream:

1. **Tool discovery** — keeps the top-K relevant tool schemas in full and stubs
   the rest. The selection is frozen per conversation so it stays prompt-cache
   friendly. Stubbed tools are recoverable via `gateway_search_tools`.
2. **Compress tool outputs** — every `tool_result` block is compressed by the 4B
   model.
3. **Compress old history** — turns beyond the recent window are summarised once
   context fills up.
4. **Inject virtual tools** — `expand_context` lets the model pull back the exact
   original of anything compressed.

Compression is non-destructive: compressed content is tagged `[REF:id]` and the
original is recoverable. Overhead is roughly 300 ms per request.

**What it does not compress:** the system prompt, and the model's output. This
is why Ragmod routes retrieval through tools instead of stuffing a prompt.

## Wiring in Ragmod

We use the **hosted GPU server**, which is what the hackathon requires and what
makes savings appear on the Paritok dashboard for verification.

`paritok.yaml`:

```yaml
use_gpu_server: true
gpu_server:
  api_key: "pk_live_..."   # or export PARITOK_API_KEY
tool_discovery:
  strategy: embedding
```

Install and run:

```bash
pip install "paritok[proxy]" "paritok[toolselect]"
paritok proxy --port 8080 --config-file paritok.yaml
```

The proxy is a foreground server and must stay running for the whole session.
Ragmod runs in a second shell with the base URL pointed at it:

```bash
export OPENAI_BASE_URL=http://127.0.0.1:8080      # or ANTHROPIC_BASE_URL
export OPENAI_API_KEY=sk-...                      # real provider key, forwarded
```

The API key never changes hands — the proxy rewrites the request body and
forwards our provider headers upstream.

Note: the first request with `strategy: embedding` downloads `bge-small`
(~130MB) and takes 10–15 seconds. Every request after that is about 15 ms. Warm
the proxy before recording the demo.

## How we measure

Three independent sources, reported side by side. If they disagree, we say so.

**1. The proxy's own counter.** `GET /stats` returns cumulative totals for the
session:

```json
{
  "total_requests": 42,
  "input_tokens_original": 512340,
  "input_tokens_compressed": 138221,
  "compression_ratio": 0.27,
  "tokens_saved": 374119,
  "estimated_cost_saved_usd": "$1.01"
}
```

These are scoped to what Paritok intervenes in — tool results, file reads, old
history, and stubbed tool schemas. System prompt and model output are excluded
by design. The cost figure is cache-aware rather than a flat list-price
multiply, because frozen tool schemas would have been cache hits anyway.

**2. Our own A/B run.** `ragmod bench` runs an identical task set twice against
the same repository and the same questions:

- **Baseline** — agent talks directly to the provider, tight-snippet retrieval
- **Ragmod** — agent talks through the Paritok proxy, generous retrieval

We record input tokens per turn from the provider's own usage field on both
sides, plus answer quality on a fixed rubric, plus wall-clock latency. The
baseline is a *fair* baseline: it is the retrieval policy a sensible engineer
would use without a compressor, not an artificially bloated prompt.

**3. The Paritok dashboard.** Since all traffic runs through the hosted GPU
server, the dashboard independently reports the same content-plus-tool basis.
Screenshot goes in the submission.

## Honesty rules for the write-up

- Report our measured number, not Paritok's published 74%.
- Report token counts *and* answer quality. A compressor that saves tokens by
  losing the answer has not helped.
- Count `expand_context` round-trips. When the model expands a reference, the
  proxy issues a second upstream POST, so an expand-heavy workload can cost more
  than it saves. If we see that, we report it — and it becomes our
  `hackathon-feedback` issue.
- State clearly which numbers come from `/stats`, which from provider usage
  fields, and which from the dashboard.

## Failure modes to watch

| Symptom | Likely cause |
|---|---|
| `/stats` shows ~0 savings | Context is going in as prompt text, not `tool_result` |
| Savings only on turn 1 | Session is single-turn; history compression never engages |
| Cost went up | `expand_context` round-trips doubling upstream POSTs |
| Ratio far worse than 25.7% | Corpus is prose, not code — off-distribution |
| Nothing on the dashboard | `use_gpu_server` is false, or the key is not loaded |
