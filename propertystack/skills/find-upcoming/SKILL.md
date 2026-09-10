---
name: find-upcoming
description: Skill 6 of PropertyStack. Find apartment projects in the pipeline (zoning filed through leasing) in an area, from Plano's Legistar API, TDLR TABS registrations (via zabalist.com), and local news. Use when refreshing the upcoming-supply picture for an area.
---

# find-upcoming

Two isolated phases: a script that **gathers** raw candidate documents (no judgment calls),
and an agent step that **extracts** real projects from them (all the judgment calls). Don't
skip straight to writing `6-upcoming.csv` by hand — run GATHER, then do EXTRACT exactly as
below.

## Phase 1 — GATHER (script)

**Reads:** three public sources, no key required for any of them:
1. Plano Legistar Web API — `https://webapi.legistar.com/v1/plano/matters`
2. TDLR TABS registrations, found via Jina search and read from `zabalist.com` (TDLR's own
   site has no bulk export and no reusable per-project page structure to parse)
3. News — Community Impact, Dallas Morning News, Dallas Business Journal, Candysdirt, plus
   city-site P&Z/council queries — found via Jina search and read

**Writes:** `data/<area>/6-upcoming-candidates.jsonl`, one JSON object per source document:
`{source_type, source_url, title, fetched_at, text}` where `text` is the Jina-read markdown
(or, for Legistar, the matter fields), trimmed to ~4000 relevant chars. + a run log in `runs/`.

### Run
`python3 skills/find-upcoming/run.py --area plano-richardson`

Takes several minutes — ~26 Jina searches and 50-90 Jina reads. Needs `JINA_API_KEY` in a
gitignored `.env` (checked in this repo's parent dir too).

This script makes **no relevance or dedup decisions**. It does not filter Legistar matters
by keyword, does not decide which zabalist/news pages are real projects, and does not merge
anything. It writes every candidate document it fetched (Legistar: every P&Z matter in the
window; TDLR/news: every URL a search query surfaced that matched the domain allowlist) —
recall over precision. Check `runs/…json` `counts.by_source_type` after running.

## Phase 2 — EXTRACT (agent, cheap model is fine)

Read `data/<area>/6-upcoming-candidates.jsonl` (every line) and produce
`data/<area>/6-upcoming.csv` with the exact columns in `CONTRACTS.md`:
`project_id, project, address, city, units, developer, stage, stage_date, expected_open,
source_type, source_url, first_seen`.

Rules:
- **project** = the development's actual name (e.g. "Haggard Farm Townhomes", "Collin Creek
  Multifamily"), never a news headline. If no real name is stated anywhere, use
  `"<units>-unit project at <address>"`. Never write a headline sentence as the project name.
- **One row per real project.** Merge candidates that are the same project across sources by
  matching address or name (normalize: lowercase, strip punctuation, strip "apartments",
  phase/building suffixes). When merging, keep the **most advanced stage** seen
  (`zoning-filed < zoning-approved < site-plan-approved < permit < under-construction <
  leasing`) and its `stage_date`; backfill blank fields (units, developer, address,
  expected_open) from other matching candidates; pick the single **best source_url** for that
  row — prefer the source that most directly states the project name + unit count (a Legistar
  filing or the news article that named the development, over a bare zabalist stub, if both
  exist and say the same thing).
- **units**: only fill in if a candidate's text actually states a number (e.g. "261-unit",
  "350 units", "NNN dwelling units"). Never guess or infer from square footage/value.
- **Exclude**: projects opened/fully leased before 2025; single-family; hotels/motels;
  assisted-living / memory-care / skilled-nursing (55+ **independent-living apartments** are
  OK — those are still multifamily rentals); anything outside Plano or Richardson.
- **stage** values are exactly: `zoning-filed | zoning-approved | site-plan-approved | permit |
  under-construction | leasing`. Infer from what the candidate's own text says (a Legistar
  "passed" status, a zabalist milestone heading, or a news article's own stage language) — do
  not default to a stage the text doesn't support.
- `project_id` = slug of `<city>-<project>` (lowercase, non-alnum → `-`).
- `first_seen` = today's date (ISO).

Also write `data/<area>/6-upcoming-extract-notes.md`: a bullet per merge ("X merged from
these N candidate URLs, kept most-advanced stage Y") and a bullet per excluded candidate with
the exclusion reason (pre-2025, single-family, hotel, senior-care, outside area, no real
project identifiable, duplicate of already-excluded candidate, etc). This is the audit trail —
don't skip it.

### Validate
`python3 skills/find-upcoming/extract_check.py --area <area>`
Run this after writing the CSV and fix everything it flags before calling EXTRACT done.

### Verify (do this, don't skip it)
Jina-read 8 random rows' `source_url` and confirm the project name (or address) and unit count
in `6-upcoming.csv` actually appear on that page. Note pass/fail per row.

Recall check: compare your project list (by name/address, not by copying rows) against
`/home/drewp/main-projects/realpage/raw/research-01/R5-upcoming-projects.csv` — for any project
there you didn't find, check whether it's still in the candidates jsonl (extraction miss) or
never surfaced by GATHER (recall gap, note it for a future query addition).

## Limits
- Recall depends on what Jina search surfaces that day; re-running can find a different subset.
- Richardson has no Legistar instance — Richardson zoning cases only come from TDLR/news.
- TDLR/zabalist pages rarely state a unit count (only project value/sq ft), so `units` is often
  blank for `tabs`-sourced rows unless a merged news candidate supplies it.
- Legistar candidates carry no address/units by themselves (just a matter title) — EXTRACT must
  rely on news/TDLR candidates to fill those in when merging, or leave them blank.
