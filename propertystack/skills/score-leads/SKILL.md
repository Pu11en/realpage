---
name: score-leads
description: Skill 7 of PropertyStack. Score sold and upcoming apartment communities as software-sales leads and write a one-sentence, facts-only reason for each. Use after find-sales and find-upcoming to produce the ranked lead list.
---

# score-leads

Two isolated phases: a script that **gathers + scores** (pure arithmetic, no prose), and an
agent step that **writes the WHY sentence** (the only judgment call, and it's fact-constrained).

## Phase 1 — GATHER + SCORE (script)

**Reads:** `data/<area>/master.csv`, `data/<area>/5-sales.csv`, `data/<area>/6-upcoming.csv`
**Writes:** `data/<area>/leads.csv` (columns in `CONTRACTS.md`, `why` left empty) and
`data/<area>/leads-facts.jsonl` (one JSON object per lead: the facts its `why` line may draw
on — nothing else) + a run log in `runs/`.

### Run
`python3 skills/score-leads/run.py --area plano-richardson`

### Scoring (0-100 integers, all parts kept as separate columns)
- `score_size = round(min(units,400)/400*40)`; unknown units -> 15.
- `score_timing`:
  - sold: `<=90 days` since `sale_date` -> 30, `<=180` -> 20, `<=365` -> 12, `<=730` -> 5,
    older -> 0.
  - upcoming: `zoning-filed` 30, `zoning-approved` 28, `site-plan-approved` 26, `permit` 22,
    `under-construction` 18, `leasing` 10.
- `score_signal = 15` (constant).
- `score_open`: software unknown/blank/"not checked"/"not chosen yet" -> 15; a known vendor ->
  5.
- `software`: upcoming leads are always `"not chosen yet"`; sold leads use `master.csv`
  `software` (or `"unknown"` if blank).
- One lead per row of `5-sales.csv` (`signal=sold`, `ref_id=apt_id`) and per row of
  `6-upcoming.csv` (`signal=upcoming`, `ref_id=project_id`). Ranked by total score, ties
  broken by input order.
- `sources`: sold = `5-sales.csv source_url` + `master.csv proof_url` (";"-joined, blanks
  dropped); upcoming = `6-upcoming.csv source_url`.

## Phase 2 — WHY (agent, cheap model is fine)

Read `data/<area>/leads-facts.jsonl` and `data/<area>/leads.csv`. For every lead, write one
sentence into the `why` column: **<=25 words, using only facts present in that lead's
leads-facts.jsonl record** (no numbers, dates, or names you didn't get from there — not from
memory, not from the CSV's other rows, not invented).

Format examples:
- `"Sold Jun 2026 to X · 420 units · on Yardi → new owner may re-pick software."`
- `"Zoning approved Mar 2026 · 360 units · opens ~2027 → software not chosen yet."`

If a fact is missing (e.g. units blank), just omit that clause rather than guessing a number.

### Check
`python3 skills/score-leads/why_check.py --area <area>`
Flags any `why` line containing a number, 4-digit year, or capitalized name-like token not
traceable to that lead's facts record. Fix every flag (rewrite the sentence using only
available facts, or drop the unsupported clause) before calling the WHY step done.

## Limits
- `score_timing` for sold leads decays with the tool's fixed `TODAY` constant, not the actual
  run date — re-running later without bumping `TODAY` will over-value old sales.
- The WHY step is inherently the one place editorial judgment/prose enters this skill; that's
  why `why_check.py` exists — treat every flag as a real problem, not a false positive, unless
  you've checked the fact is genuinely present under a different phrasing.
