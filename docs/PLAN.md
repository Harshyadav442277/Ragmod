# Build plan

## Deadline, converted

Submissions close **Aug 5, 12:00am PDT**, which is **Wednesday Aug 5, 12:30 PM
IST**. Not Wednesday night. The working window is Saturday afternoon through
Tuesday, with Wednesday morning as buffer only.

Target: **submit Tuesday night IST.**

## What the competition actually requires

Everything below is mandatory. Nothing else is.

- [ ] Project URL — repo with clear setup instructions is explicitly acceptable
- [ ] Public repo, Apache 2.0 visible in the About section — done
- [ ] Paritok credited with a link in the README — done
- [ ] Paritok account email, matching the API key used, on the submission form
- [ ] Text description covering how Paritok was used
- [ ] Demo video under 3 minutes, public on YouTube or Vimeo
- [ ] `examples/` folder with sample outputs — optional but cheap and judged
- [ ] `hackathon-feedback` GitHub issue — separate $50 prize lane
- [ ] Social post tagged `#BuiltWithParitok` — separate $50 prize lane

## Agents

| Role | Model slug | Job |
|---|---|---|
| Orchestrator | `cursor-grok-4.5-medium-fast` | Freeze contracts, split work, review diffs, own the narrative |
| Workers | `composer-2.5-fast` | One workstream each, PR-sized diffs |

"Grok 4.5 high fast" is not an available slug; `cursor-grok-4.5-medium-fast` is
the Grok 4.5 option we have.

Three workstreams, not seven. With two humans reviewing, wider parallelism costs
more in integration than it saves in build time.

1. **Agent + tools** — the loop, the four tools, citations
2. **Gateway + bench** — proxy lifecycle, `/stats` reader, A/B harness
3. **Submission** — README, examples, video script, Devpost text

Rules for workers: one workstream, one acceptance check, no cross-module
refactors, stub at the contracts in `ARCHITECTURE.md` rather than inventing
shared types.

## Waves

**Wave 0 — Saturday (today)**
Repo skeleton, frozen contracts, `paritok.yaml` with the hosted GPU key, proxy
running, one real compressed call.
*Done when:* `/stats` shows non-zero `tokens_saved` and the call appears on the
Paritok dashboard.

**Wave 1 — Sunday**
Agent loop with `search_repo`, `read_file`, `list_dir`, `run_tests`. Multi-turn.
Answers carry `file:line` citations.
*Done when:* a real question against a real repo is answered correctly, end to
end, through the proxy.

**Wave 2 — Monday**
`ragmod bench`: the same task set through the baseline and through Ragmod, with
input tokens, answer quality, and latency recorded. Fixed question set chosen
and committed.
*Done when:* a savings table can be regenerated with one command.

**Wave 3 — Tuesday**
README with setup instructions a judge can follow in under ten minutes,
`examples/` with saved transcripts and the savings table, demo video, Devpost
text, feedback issue, social post. Submit.

Wednesday morning is buffer for a failed upload or a broken link, nothing else.

## Risks

| Risk | Mitigation |
|---|---|
| Savings come out near zero | Wave 0 gate catches it on day one, while there is still time to change shape |
| `expand_context` double-POST inflates cost | Measure it explicitly; if real, it becomes the feedback issue |
| Hosted GPU rate limits or downtime | Keep the self-host path working as a fallback for development only |
| Scope creep into embeddings or a web UI | Not in the requirement list; deferred until after submission |
| Video left to the last hour | Script written during Wave 2, recorded Tuesday |

## Working agreement

Harsh works on his fork and opens PRs into `main`. `main` stays runnable at all
times — it is the demo path and the thing judges clone.
