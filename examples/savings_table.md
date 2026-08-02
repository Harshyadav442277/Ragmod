# Ragmod savings table

Regenerate with: `ragmod bench --repo . --out examples/savings_table.md`

Arms:
- **baseline** — direct upstream (`RAGMOD_OPENAI_URL`), tight retrieval
- **ragmod** — Paritok hosted-GPU proxy, generous retrieval

Token counts are provider `usage.prompt_tokens` (what the upstream billed).
For ragmod that is post-compression. `proxy_saved` is the Paritok `/stats` delta.

| task | baseline prompt toks | ragmod prompt toks | Δ tokens | baseline quality | ragmod quality | baseline latency (s) | ragmod latency (s) | proxy_saved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| stats_to_savings | 2955 | 3440 | -485 | 2/2 | 2/2 | 0.683 | 4.53 | 5086 |
| search_excludes | 2131 | 2841 | -710 | 1/2 | 2/2 | 0.665 | 5.415 | 2669 |
| bootstrap_search | 3309 | 3938 | -629 | 2/2 | 2/2 | 0.628 | 5.636 | 1709 |

**Provider totals (usage.prompt_tokens):** baseline/tight `8395` · ragmod/generous+proxy `10219` · Δ vs tight `-1824` · ratio `1.217` (ragmod/baseline; lower means Ragmod billed less).

**Paritok `/stats` on Ragmod arms only:** `tokens_saved` delta sum = `9464`. This is the compression win on the generous tool_result path (original − compressed), independent of the tight baseline.

Note: Δ vs tight can be negative. Over-retrieval + compression can still bill more than a deliberately tiny baseline, while improving recall/quality and showing large `/stats` savings against the uncompressed generous prompt.

## Per-arm notes

- `stats_to_savings`/baseline: turns=2, cites=ragmod/gateway/proxy.py:1-105
  - answer: The proxy turns raw stats into savings by using the `stats_to_savings` function, which is not shown in the provided code snippet. However, based on the context,
- `stats_to_savings`/ragmod: turns=2, cites=ragmod/gateway/proxy.py:63-125
  - answer: The proxy turns raw stats into savings by calculating the difference between the original and compressed token counts, and then using this difference to determi
- `search_excludes`/baseline: turns=2, cites=tests/test_tools.py:12-24
  - answer: The `search_repo` function keeps ripgrep out of `.venv` and `__pycache__` by rejecting paths outside the repository in `test_tools_reject_paths_outside_reposito
- `search_excludes`/ragmod: turns=2, cites=ragmod/tools/repo.py:1-62
  - answer: Ripgrep is kept out of `.venv` and `__pycache__` by the `_RG_EXCLUDE_GLOBS` tuple in the `repo.py` file. This tuple contains a list of directories and files tha
- `bootstrap_search`/baseline: turns=2, cites=ragmod/agent/loop.py:118-247
  - answer: The agent bootsraps its first search_repo tool result from the file `./ragmod/agent/loop.py` at line 123.
- `bootstrap_search`/ragmod: turns=2, cites=ragmod/agent/loop.py:87-170
  - answer: The agent bootsraps its first search_repo tool result in the file `./ragmod/agent/loop.py`.
