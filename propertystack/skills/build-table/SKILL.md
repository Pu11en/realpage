---
name: build-table
description: Skill 4 of PropertyStack. Left-join apartments, websites, and software into master.csv, with a coverage funnel in the run log. Use after detect-software to produce the pipeline's combined table.
---

# build-table

**Reads:** `data/<area>/1-apartments.csv`, `2-websites.csv`, `3-software.csv`
**Writes:** `data/<area>/master.csv` (columns in `CONTRACTS.md`) + a run log in `runs/`

## Run
`python3 skills/build-table/run.py --area plano-richardson`

## What it does
1. Left-joins the three files on `apt_id` (every apartment stays, even with no
   website/software match).
2. Writes all `1-apartments.csv` columns plus `website`, `website_confidence`,
   `software`, `signal`, `proof_url`, `checked_at`, `unknown_reason`.
3. Logs a coverage funnel in `counts`: `in_area` (total communities),
   `website_found` (high/medium confidence websites), `checked` (rows Skill 3
   actually fetched), `identified` (software resolved), `unknown` broken down
   by `unknown_by_reason`, and a `software` vendor count.

## Check after running
- The funnel should be monotonic: `in_area` ≥ `website_found` ≥ `checked` ≥
  `identified`. If not, something upstream wrote a row out of order.
- `unknown_by_reason` tells you where coverage is leaking (no-website vs.
  no-portal-link vs. error) — that's the punch list for improving Skills 2/3.

## Limits
- Pure join — does no new detection or scoring. Garbage in Skills 1–3 (wrong
  website, missed vendor) passes straight through.
- One row per `apt_id`; if Skills 2/3 ever produce more than one row for the
  same `apt_id`, only the last one wins (dict overwrite).
