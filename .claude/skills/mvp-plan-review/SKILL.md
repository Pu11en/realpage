---
name: mvp-plan-review
description: Review a build or research plan in the RealPage repo for feasibility and MVP-readiness before any building starts. Use when Drew asks to review, pressure-test, or sanity-check a plan, or before handing a plan to a build/research session. Checks the outside-in constraint, the named buyer, proof they lack it, MVP scope, feasibility of every dependency, and whether a cheaper model could execute it without asking questions.
---

# MVP plan review

You are reviewing a plan, not writing one. Be the skeptic who has to sign off
before money and time get spent. Read the plan file, then check every gate
below against the plan's own text and the repo's evidence files. Don't take the
plan's word for anything it doesn't cite.

## Context you must load first

- `09-build-ideas/brainstorm-2026-09-10-pitch-to-realpage.md` §1 — the mission
  and the eight scoring criteria
- `findings.md` and `04-reddit/index.md` — the evidence a plan may cite
- The plan under review (and any research-run file it depends on)

## The mission in one line

Build a finished, working MVP that RealPage (or a business like theirs) would
actually use, using **only public information** — we have no insiders, no
product access, no customer data — and show from outside that they don't
already have it.

## Gates (each gets PASS / FIX / FAIL)

### G1. Outside-in (hard gate — any FAIL here fails the plan)
- List every input the product needs. For each: is it public, and where
  exactly does it come from? Anything that needs RealPage's login, data, docs,
  or staff is a FAIL.
- Collection stays read-only toward third parties (no posting, voting, account
  actions). Crawling is polite and rate-limited.

### G2. Named buyer
- A specific role (e.g. "VP Market Intelligence", not "RealPage") owns the pain.
- The pain is cited to a repo file with an exact quote or number.
- The plan says what that person does with the product *in a normal week*.

### G3. Absence / benefit is provable
- The plan names what would prove RealPage already has this, and how the
  research run checks it.
- There's a written **kill criterion**: "if we find X, we stop or pivot to Y."
- Existing third-party products that do the same thing are named and
  differentiated, or checking for them is scheduled.

### G4. MVP scope
- One buyer, one job, one slice (one metro / one product line / one workflow).
- **Definition of done is measurable** (counts, accuracy %, a URL that loads),
  not "works well."
- There's an explicit **cut list** — things deliberately left out.
- A timebox is stated and believable for one person plus cheap models.
- Viable, not just minimal: the output is useful on its own, not a mockup.

### G5. Feasibility
- Every technical dependency is either already proven in this repo
  (`tooling/LOCAL-ASSETS.md`, `task_plan.md` test results) or has a spike in
  the research run with a pass threshold.
- Known blockers are handled (DataDome/Cloudflare sites, Reddit's 100 req/3 min
  limit, auth walls). Paid APIs or accounts are flagged as Drew decisions.
- Legal/ToS exposure is named, with a mitigation.

### G6. Executable by a cheaper model
- Steps are ordered, each with an output file path and an acceptance check.
- No step says "figure out", "decide", "as appropriate" without the decision
  rule spelled out.
- Tools, file paths, and conventions (README header block, `raw/` never
  edited) are named.

### G7. Pitch
- The plan names the pitch artifact (report, live link, one-pager) and what it
  shows on real data.
- The path to a human at the buyer is stated (partner program, role + channel,
  event), even if it's a hypothesis to verify.
- Fallback buyers are named.
- The framing wouldn't read as hostile to the buyer.

## Output format

Write the review to `09-build-ideas/review-<plan-slug>.md` with the repo header
block (`Source / Fetched / Method / Confidence`), then:

```
Verdict: GO | GO WITH FIXES | NO-GO

| Gate | Result | Why (one line, cite plan section or repo file) |
|---|---|---|

Required fixes (numbered, each one concrete enough to apply as an edit)
Risks accepted (things we're knowingly not fixing, and why)
Open decisions for Drew (at most three, each with a recommended default)
```

Rules:
- Any G1 FAIL → NO-GO. More than two FIXes in G3–G5 → GO WITH FIXES at best.
- Don't pad. If a gate passes, one line is enough.
- Don't rewrite the plan inside the review — list fixes; apply them only if
  asked (or if the session's task is "review and fix").
- If the plan is sound, say GO plainly.
