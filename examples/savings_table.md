# Ragmod savings table

Regenerate with: `ragmod bench --repo . --out examples/savings_table.md`

Arms:
- **baseline** — direct upstream (`RAGMOD_OPENAI_URL`), tight retrieval
- **ragmod** — Paritok hosted-GPU proxy, generous retrieval

Token counts are provider `usage.prompt_tokens` (what the upstream billed).
For ragmod that is post-compression. `proxy_saved` is the Paritok `/stats` delta.

| task | baseline prompt toks | ragmod prompt toks | Δ tokens | baseline quality | ragmod quality | baseline latency (s) | ragmod latency (s) | proxy_saved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| stats_to_savings | 2047 | 3190 | -1143 | 2/2 | 2/2 | 0.669 | 6.711 | 5630 |
| search_excludes | 2162 | 6472 | -4310 | 1/2 | 0/2 | 1.082 | 2.838 | 6280 |
| bootstrap_search | 2212 | 2901 | -689 | 2/2 | 2/2 | 0.486 | 2.141 | 1719 |

**Provider totals (usage.prompt_tokens):** baseline/tight `6421` · ragmod/generous+proxy `12563` · Δ vs tight `-6142` · ratio `1.957` (ragmod/baseline; lower means Ragmod billed less).

**Paritok `/stats` on Ragmod arms only:** `tokens_saved` delta sum = `13629`. This is the compression win on the generous tool_result path (original − compressed), independent of the tight baseline.

Note: Δ vs tight can be negative. Over-retrieval + compression can still bill more than a deliberately tiny baseline, while improving recall/quality and showing large `/stats` savings against the uncompressed generous prompt.

## Per-arm notes

- `stats_to_savings`/baseline: turns=2, cites=ragmod/gateway/proxy.py:1-7
  - answer: The proxy turns raw stats into savings by calling the `stats_to_savings` function, which is implemented in the `proxy.py` file. This function is responsible for
- `stats_to_savings`/ragmod: turns=2, cites=ragmod/gateway/proxy.py:70-125
  - answer: The proxy turns raw stats into savings by calling the `stats_to_savings` function, which is defined in `ragmod/gateway/proxy.py`. This function takes a dictiona
- `search_excludes`/baseline: turns=2, cites=tests/test_tools.py:12-25
  - answer: The `search_repo` function keeps ripgrep out of `.venv` and `__pycache__` by rejecting paths outside the repository in `test_tools_reject_paths_outside_reposito
- `search_excludes`/ragmod: turns=5, cites=—
  - answer: Stopped after 5 tool turns before reaching a final answer.
- `bootstrap_search`/baseline: turns=2, cites=ragmod/agent/loop.py:118-133
  - answer: The agent bootsraps its first search_repo tool result from the file `./ragmod/agent/loop.py` at lines 123-128.
- `bootstrap_search`/ragmod: turns=2, cites=ragmod/agent/loop.py:87-170
  - answer: The agent bootsraps its first search_repo tool result in the file `./ragmod/agent/loop.py` at line 127.
