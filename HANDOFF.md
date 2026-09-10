# HANDOFF — start here

One-file bootstrap for any agent or session picking up this repo with **no prior
context**. If you read only one file, read this one; it points at everything else.
`task_plan.md` is the live plan and wins over this file on any conflict.

Repo (public): https://github.com/Pu11en/realpage

## Lowest-cost ways to get the repo

- If a clone of this repo already exists on the machine, use it — do not re-clone.
  It lives at `/home/drewp/main-projects/realpage` (remote already configured,
  push-ready) on Drew's main machine.
- One-command clone (needs git, no auth for read):
  `git clone https://github.com/Pu11en/realpage.git`
- Git-free, single request (if git is unavailable):
  `curl -fsSL https://github.com/Pu11en/realpage/archive/refs/heads/main.tar.gz | tar xz`
- Read-only, one file at a time (raw URL pattern):
  `https://raw.githubusercontent.com/Pu11en/realpage/main/<path>`
- Zero-disk, zero-network, one paste/attach: `RESUME-PACK.md` (repo root) —
  HANDOFF + README + planning trio + the Reddit pack, verbatim in one file,
  for sessions where both the local disk and GitHub are unreachable.

## What this is

A cited-evidence knowledge base about **RealPage** (property management software,
realpage.com). **Constraint: outside-in only** — no insiders, no product access,
nobody at RealPage to ask; everything is public-source. **Goal:** build a
finished MVP from this evidence that RealPage (or a business like theirs) would
actually use, prove from outside they don't have it, and pitch it. Drew decides;
RealPage is who we can't ask.

Conventions (full version in `README.md`): every file opens with
`Source / Fetched / Method / Confidence` headers; `raw/` captures are verbatim
and never edited; exact quotes are preserved; distilled analysis lives in
`01-company/` … `09-build-ideas/`.

## Read first, in order

1. `README.md` — conventions, how to use the KB
2. `task_plan.md` — live plan: phases, statuses, next step, decisions, errors
3. `findings.md` — distilled evidence so far
4. `progress.md` — session log, newest first
5. `04-reddit/index.md` — completed Reddit evidence pack

## Where things stand (2026-09-10)

- **Phase 2 (Reddit) COMPLETE:** 25 queries, 142 unique posts, 25 subreddits,
  2020–2026. Raw JSON in `raw/reddit/`; distilled pack in `04-reddit/index.md`.
- **Phase 1 (reviews) PARTIAL:** Software Advice captured in full
  (`raw/reviews/software-advice-realpage-2026-09-10.md`); Capterra indirect only
  (`raw/reviews/capterra-search-summary-2026-09-10.md`); **G2, Capterra,
  TrustRadius block headless crawling** (DataDome / Cloudflare) — need a real
  browser session, read-only.
- **Phases 3–7 PENDING:** DOJ primary docs (justice.gov is open — no blocker),
  realpage.com crawl (products/pricing/case studies), competitor stubs,
  social, synthesis.
- **Direction (planning session 2026-09-10):** the old five directions were
  re-scored against "pitchable to RealPage"; four are hostile or competing and
  were killed. Recommended: **C1 PMS Switch Radar** (which software each
  apartment community runs, read from its public website, plus dated switches
  via the Wayback Machine), one metro. Fallback: C3 affordable-housing
  compliance copilot. See `09-build-ideas/brainstorm-2026-09-10-pitch-to-realpage.md`.
- Open-ended collection (G2 pass, app stores, X, LinkedIn, DOJ docs, site
  crawl) is **paused** — collect only what a plan needs.

## Next actions, in order

1. Drew confirms C1 (or picks otherwise) and answers the open decisions in
   `09-build-ideas/mvp-plan-switch-radar.md` §8.
2. Run `09-build-ideas/research-run-01-verify.md` (≈3.5 h, cheap model OK).
   R1 is a kill gate.
3. Apply results to the MVP plan, re-run `/mvp-plan-review`, then build.

## Constraints

- **The repo is PUBLIC.** Never commit credentials, cookies, tokens, or session
  data. `tooling/reddit_search.py` reads its Reddit cookie from a local machine
  path at runtime — that file (and any cookie value) must never be added.
- Reddit collection: `tooling/reddit_search.py` with the cookie saved at
  `~/.dsh/.credentials.yaml` (Drew's machine only). Pacing: 100 requests /
  ~3 min → ≤8 posts with 2 comments per query, ~20 s between queries.
- Read-only toward third parties: no posting, voting, or account actions.
- Show every markdown file created or updated in the session reply, in full
  (fenced, labeled with the filename), so Drew can read files without opening them.
- Update `task_plan.md`, `progress.md`, and `findings.md` as you work.

## Copy-paste prompts

### Research run 01 (next session)

```text
Run the research spec in 09-build-ideas/research-run-01-verify.md in the
realpage repo (/home/drewp/main-projects/realpage). Read HANDOFF.md and the
brainstorm-2026-09-10-pitch-to-realpage.md first. Follow the spec exactly:
order, time budgets, pass/kill rules, output paths. Read-only toward third
parties. Fill in the results table, update task_plan.md / findings.md /
progress.md, commit locally, don't push.
```

### Brainstorm / planning session (original — superseded by the session above)

```text
Planning session: RealPage knowledge base → what we build from it.

Repo (public): https://github.com/Pu11en/realpage
Start with HANDOFF.md, then task_plan.md, findings.md, 04-reddit/index.md.

The evidence is collected; the direction isn't chosen. Five candidates are
sketched: public evidence library, investigation/content series, a tool for
50–500-unit property managers, migration/switch tooling, renter-side watch.

Brainstorm with me — bring observations from the repo's evidence and go back
and forth on them — pressure-test those five, help me pick one, then turn the
winner into a concrete plan: what it is, who it's for, what "working" looks
like, and ordered first steps. Planning only this session; no building yet.
```

### Collection continuation

```text
You are resuming work on a RealPage knowledge base.
Repo (public): https://github.com/Pu11en/realpage
Read HANDOFF.md first, then README.md, task_plan.md, findings.md, progress.md,
and 04-reddit/index.md. Work read-only toward third parties; never commit
credentials (the repo is public). Ask Drew which of the five build directions
he leans toward, record it in task_plan.md, then continue collection with
Phase 3 (DOJ primary docs → raw/legal/) and Phase 4 (realpage.com crawl →
raw/site/). Show every markdown file you create or update in full in your
reply. Keep the planning files updated, commit, and push when done.
```
