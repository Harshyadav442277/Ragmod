# Demo video script (< 3 minutes)

Record with OBS / phone screen + mic. Public upload to YouTube or Vimeo. No copyrighted music.

**Target length:** 2:00–2:30.

| Time | Visual | Say |
|---|---|---|
| 0:00–0:15 | README + badge | “Ragmod is a codebase retrieval agent built for the Paritok token-efficiency hackathon. It asks questions about a repo and answers with file:line citations.” |
| 0:15–0:35 | Architecture diagram in `docs/ARCHITECTURE.md` or draw: Agent → tools → Paritok → LLM | “Retrieval is tool-based on purpose. Paritok compresses tool results — so we retrieve generously and stay cheap. Every LLM call goes through Paritok’s **hosted GPU** proxy.” |
| 0:35–0:55 | Terminal 1: `./scripts/start_proxy.sh` showing `Hosted GPU server OK` | “Here’s the proxy. Hosted GPU key accepted — that’s what the dashboard tracks.” |
| 0:55–1:25 | Terminal 2: `ragmod ask "How does the proxy turn raw stats into savings?" --repo .` | “Same question a judge can run. Watch it search and read through tools, then answer with a citation into `proxy.py`.” |
| 1:25–1:45 | `ragmod stats` or `curl …/stats` + Paritok dashboard tab | “`/stats` shows tokens saved this session. Same traffic on the Paritok dashboard.” |
| 1:45–2:15 | `examples/savings_table.md` | “Wave 2 A/B: tight baseline vs generous Ragmod. We report provider tokens **and** Paritok’s `/stats` savings — and we’re honest when over-retrieval still bills more than tiny snippets.” |
| 2:15–2:30 | Repo URL + Apache badge | “Open source Apache 2.0 — github.com/shreshth006/Ragmod. Built with Paritok.” |

## Shot checklist

- [ ] Face or voice clear; terminal font large  
- [ ] Do **not** show `.env` or API keys  
- [ ] Show hosted GPU accepted line  
- [ ] Show non-zero `tokens_saved`  
- [ ] Show citation line in ask output  
- [ ] End card with repo URL  

## Record command (optional)

```bash
# Terminal fonts: bump size first. Then:
# 1) start proxy  2) run ask  3) ragmod stats  4) open examples/savings_table.md
```
