# Devpost submission draft

Copy/paste into the Devpost form. Keep the Paritok section — judging weights **Use of Paritok** hardest.

## Project name

Ragmod

## Tagline / elevator (≤1 sentence)

Compression-first codebase retrieval agent: over-retrieve through tools, let Paritok make it affordable, measure the savings.

## Project URL

https://github.com/shreshth006/Ragmod  
(Repo includes setup a judge can run in ~10 minutes; live demo is local via Paritok hosted GPU.)

## Text description

### What it does

Ragmod answers questions about a checked-out repository with `file:line` citations. It is an **agentic** loop (`search_repo`, `read_file`, `list_dir`, `run_tests`), not a single-shot RAG pack. Retrieval is intentionally generous so recall stays high.

### How we used Paritok

Paritok sits as a **mandatory proxy** between Ragmod and the upstream LLM (`use_gpu_server: true`). We never call the provider SDK directly.

Paritok compresses what its 4B model was trained on — especially `tool_result` blocks, history, and unused tool schemas. That is why Ragmod routes every file read and search hit through tools instead of stuffing a user prompt.

Integration (from [hackathon resources](https://build-with-paritok.devpost.com/resources)):

1. `paritok.yaml` with `use_gpu_server: true` + API key  
2. `paritok proxy --port 8080` (hosted GPU)  
3. Agent `OPENAI_BASE_URL=http://127.0.0.1:8080` (Groq upstream via `--openai-url`)

### Measured savings

Three views (see `docs/PARITOK.md` and `examples/savings_table.md`):

1. **Proxy `/stats`** — on Wave 2 Ragmod arms we measured **thousands of tokens saved** on the generous tool_result path (e.g. ~9k–13k across three tasks depending on run).  
2. **A/B bench** — same questions, tight baseline (direct upstream) vs generous Ragmod (through Paritok). Quality matched or beat the baseline; we also report when provider `prompt_tokens` still exceed a tiny baseline (honest: over-retrieval residual can outweigh compression vs *minimal* snippets).  
3. **Paritok dashboard** — hosted GPU traffic for verification against our account email.

We report **our** measured numbers, not Paritok’s published 74%.

### Why this shape (originality)

Most gallery entries measure compression in isolation. Ragmod makes Paritok **load-bearing**: the product policy is “retrieve more than a normal code agent would dare,” and compression is what makes that policy affordable.

### Stack

Python · OpenAI-compatible chat completions · ripgrep · Paritok hosted GPU proxy · Groq (demo upstream; model-agnostic)

### Feedback

Filed during the hackathon: https://github.com/Paritok-official/paritok-4b-v1/issues/19

## Paritok account email

<!-- paste the email used at paritok.com / API key creation -->

## Demo video

<!-- paste YouTube/Vimeo public URL after recording from docs/VIDEO_SCRIPT.md -->

## Built with

Paritok, Python, httpx, ripgrep, Groq, pytest
