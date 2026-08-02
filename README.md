# Ragmod

[![Built with Paritok](https://img.shields.io/badge/Built%20with-Paritok-1f2d3d)](https://github.com/Paritok-official/paritok-4b-v1)

A retrieval agent for codebases. Ask a question about a repository, get an answer with `file:line` citations.

Retrieval runs through tools, so every chunk of code arrives as a `tool_result` — the content [Paritok](https://github.com/Paritok-official/paritok-4b-v1)'s 4B compressor is trained on. That lets Ragmod retrieve generously and stay cheap: recall goes up, the bill does not.

> Built for **[Build with Paritok: The Token-Efficiency Hackathon](https://build-with-paritok.devpost.com/)**.

## Status

**Wave 2 done** — A/B bench + savings table. Ask sample: [`examples/wave1_ask.txt`](examples/wave1_ask.txt). Table: [`examples/savings_table.md`](examples/savings_table.md).

- [Architecture](docs/ARCHITECTURE.md)
- [Paritok integration](docs/PARITOK.md)
- [Build plan](docs/PLAN.md)
- [Critique](docs/CRITIQUE.md)

## Quick start

```bash
git clone https://github.com/shreshth006/Ragmod.git
cd Ragmod
python3 -m venv .venv
source .venv/bin/activate

# CPU torch first (avoids huge CUDA wheels)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e ".[paritok]"

cp .env.example .env
# edit .env: PARITOK_API_KEY + OPENAI_API_KEY
```

Terminal 1 — start the proxy ([hackathon resources](https://build-with-paritok.devpost.com/resources)):

```bash
source .venv/bin/activate
./scripts/start_proxy.sh
# keep this terminal open
```

On Windows Git Bash, the script falls back to the `py -3` launcher. If your
Python install is not on `PATH`, set `RAGMOD_PYTHON` to its executable first.

Terminal 2 — smoke call with a fat `tool_result`:

```bash
source .venv/bin/activate
python scripts/wave0_smoke.py
# expect: WAVE 0 PASS — tokens_saved=...
ragmod stats
```

Confirm the same traffic on the [Paritok dashboard](https://paritok.com).

Ask Ragmod about the current checkout while that proxy remains running:

```bash
ragmod ask "How does the proxy turn raw stats into savings?" --repo .
```

Ragmod searches and reads through tool calls, sends those `tool_result` blocks to
the proxy, then prints the answer and source ranges. The default tool-turn limit
is eight; use `--max-turns` to lower it during a quick demo.

### A/B bench (Wave 2)

With the proxy still running:

```bash
ragmod bench --repo . --out examples/savings_table.md
```

Compares tight baseline (direct upstream) vs generous Ragmod (Paritok proxy).
Writes `examples/savings_table.md` + `.json`.

## Paritok

Built with [Paritok](https://github.com/Paritok-official/paritok-4b-v1). Every LLM call leaves through the Paritok proxy with **hosted GPU** (`use_gpu_server: true`). See [docs/PARITOK.md](docs/PARITOK.md).

## Layout

| Path | Owner wave | Role |
|---|---|---|
| `ragmod/contracts.py` | 0 | Frozen shared types |
| `ragmod/gateway/` | 0 | Proxy helpers + `/stats` → `SavingsStats` |
| `ragmod/tools/` | 1 | `search_repo` / `read_file` / `list_dir` / `run_tests` |
| `ragmod/agent/` | 1 | Tool-calling loop |
| `ragmod/bench/` | 2 | A/B harness |
| `paritok.yaml` | 0 | Hosted GPU config |
| `scripts/wave0_smoke.py` | 0 | Gate: non-zero `tokens_saved` |

## Contributing

Harsh: fork → PR into `main`. `main` stays the runnable demo path.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
