# Findings & Decisions

## Requirements
- Do not agree that the product is ready merely because automated work finished.
- Require a genuine first time human test using normal, unscripted behavior.
- Tell Drew plainly when the exact tested version is safe to push.
- Keep work local until Drew passes the candidate and separately approves GitHub.
- Use GPT 5.6 Terra only with no fallback if the preparation is run as a loop.
- Stay cost effective and make no paid model calls during preparation.

## Research Findings
- The completed chat data work is on `gowork/plan-chat-data-20260915-090124` at `d289171`.
- The Under the Hood and primary source research work is on the current session branch at `034a2ef`.
- The recruiter evidence packet is in the completed shipcheck worktree, not yet shipped into this site.
- The standard local command uses `docker-compose.dev.yml`, which sets `WEBUI_AUTH=False`; it cannot prove sign up or sign in.
- The scorecard's 46 of 46 result covers isolated signed in browser checks, not a new person's end to end understanding.
- The safety report is historical and contains real failures: 7 of 20 off topic answers and 2 of 60 factual answers.
- Two verified medium severity container root findings remain open.
- The Under the Hood builder still records absolute source directories, which is unsuitable for one reproducible release candidate.
- A real human pass must allow natural wording and exploratory mistakes; exact scripted clicks would repeat automation rather than test usability.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Integrate before testing | The publish decision must apply to one exact commit. |
| Add a separate human-test launcher | It preserves the fast no-auth developer path while giving Drew isolated production-like sign in. |
| Fix historical safety failures with deterministic rules and fixtures | This reduces repeat risk without spending on model calls. |
| Keep the final human questions unscripted | The goal is reasonable use, not test memorization. |
| Treat the browser dry run as preparation only | An automated agent cannot supply a genuine human usability verdict. |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| Earlier completion estimates treated recruiter evidence as release readiness | Replaced the estimate with explicit automated and human gates. |

## Resources
- `PLAN-human-release-gate.md`
- `site/under-the-hood.html`
- `site/data/build_evals.py`
- `tooling/dev.sh`
- `chatbot/docker-compose.local.yml`
- Completed recruiter scorecard dated 2026-09-15
