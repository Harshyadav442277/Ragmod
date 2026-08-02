# Ragmod

[![Built with Paritok](https://img.shields.io/badge/Built%20with-Paritok-1f2d3d)](https://github.com/Paritok-official/paritok-4b-v1)

A retrieval agent for codebases. Ask a question about a repository, get an answer with `file:line` citations.

Retrieval runs through **tools**, so every chunk of code arrives as a `tool_result` — the content [Paritok](https://github.com/Paritok-official/paritok-4b-v1)'s 4B compressor is trained on. Ragmod retrieves generously on purpose; Paritok keeps that affordable.

> Built for **[Build with Paritok: The Token-Efficiency Hackathon](https://build-with-paritok.devpost.com/)**.

Built with [Paritok](https://github.com/Paritok-official/paritok-4b-v1).

## Judge path (~10 minutes)

**Need:** Python 3.11+, a [Paritok](https://paritok.com) API key (`use_gpu_server`), and a free [Groq](https://console.groq.com/keys) key (or any OpenAI-compatible upstream).

```bash
git clone https://github.com/shreshth006/Ragmod.git
cd Ragmod
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e ".[paritok]"

cp .env.example .env
# set PARITOK_API_KEY=pk_live_...
# set OPENAI_API_KEY=gsk_...          # Groq
# RAGMOD_OPENAI_URL + RAGMOD_MODEL already set for Groq in .env.example
```

**Terminal 1** (keep open):

```bash
source .venv/bin/activate
./scripts/start_proxy.sh
# expect: Hosted GPU server OK — API key accepted
```

If you see `address already in use`, something is already on `:8080`:

```bash
curl -s http://127.0.0.1:8080/health   # if ok, skip starting again
# or: fuser -k 8080/tcp && ./scripts/start_proxy.sh
```

**Terminal 2:**

```bash
source .venv/bin/activate
pytest -q                                          # 7 passed
python scripts/wave0_smoke.py                      # WAVE 0 PASS — tokens_saved=...
ragmod ask "How does the proxy turn raw stats into savings?" --repo .
ragmod stats                                       # tokens_saved > 0
ragmod bench --repo . --out examples/savings_table.md   # optional; ~3–5 min
```

Confirm the same traffic on the [Paritok dashboard](https://paritok.com).

### Expected ask shape

```
… stats_to_savings …

Sources:
- ragmod/gateway/proxy.py:…

Turns: 2
```

Saved samples: [`examples/wave1_ask.txt`](examples/wave1_ask.txt), [`examples/savings_table.md`](examples/savings_table.md).

## What Ragmod is

| Piece | Role |
|---|---|
| `tools/` | `search_repo`, `read_file`, `list_dir`, `run_tests` — generous by default |
| `agent/` | Multi-turn tool loop; citations from tool metadata |
| `gateway/` | Paritok proxy helpers + `/stats` → `SavingsStats` |
| `bench/` | A/B: tight baseline (direct) vs generous Ragmod (proxy) |

Every LLM call goes through the local Paritok proxy with **hosted GPU** (`use_gpu_server: true`). No direct provider SDK calls in the runtime path.

Docs: [Architecture](docs/ARCHITECTURE.md) · [Paritok measurement](docs/PARITOK.md) · [Plan](docs/PLAN.md) · [Devpost text](docs/DEVPOST.md) · [Video script](docs/VIDEO_SCRIPT.md)

## Submission extras

- Hackathon feedback: https://github.com/Paritok-official/paritok-4b-v1/issues/19
- Social draft: [docs/SOCIAL.md](docs/SOCIAL.md)

## License

Apache License 2.0 — see [LICENSE](LICENSE).
