# Plan: Texas-only lead runs — audit every source for the problems we found by luck (2026-09-20)

Goal: every Texas source proves what it really holds, and a seller can call any lead on the list.
Runs narrow to Texas only. Arizona and New Mexico keep the data they already have on the site;
they simply stop being re-run.

Read first: `handoffs/2026-09-20-texas-only-scrape-audit.md` — it has today's findings, the method,
and what must not be redone.

## Why this plan exists

On 2026-09-20 five separate data problems were found, all by accident, none by any check:
1. Dallas County had been **failing on every run** for months and contributed nothing.
2. Houston addresses carried the unit count glued on the end, while every one said "size unknown".
3. Albuquerque's feed was live but **frozen since Jan 2025** — and looked identical to a broken one.
4. The hero line called all 1,876 buildings recent news; only 175 were.
5. Arizona sale dates showed an exact day the county never recorded.

Today's Texas run, per source: dallas-dcad 481, houston-hcad 383, tdhca 212, arlington 178,
tarrant-tad 177, tabs 126, austin 47, tarrant-tad-sales 24, **houston 18, san-marcos 4,
san-antonio 2, fort-worth 1**. The last four are the same shape Dallas had. "worked" in
source-health proves nothing.

## The one question every task answers

**Can someone selling software to apartment buildings call this lead today?**
That needs a real building name, a real address, a unit count, a date that is genuinely recent,
and a reason to call. A finding that does not touch one of those is not worth the task.

## The method for auditing one source

1. Call the endpoint by hand and get the **true total it holds** (ArcGIS: `&returnCountOnly=true`).
2. Get the **newest date it holds** (ArcGIS: `outStatistics` with `max` on the date field).
3. Compare both against what the recipe returns. A large gap is the finding.
4. Read the source's **real column list** and name every field we drop that a seller needs:
   building name, unit count, owner, contact, valuation.
5. Verify **2 rows against an independent public listing** — the name and unit count must match.
6. Write the finding into `propertystack/runs/` and fix it only if the fix is contained.
   A frozen feed is a finding, not a bug: never "fix" the runner for it.

Check: python3 -m pytest -q tooling/qa/fixes_tests/ propertystack/skills && python3 tooling/qa/check_lead_data.py
Try: bash tooling/dev.sh
Open: http://localhost:8765/index.html

## Quality gates (run after every task; a task is not done until they pass)
- The Check command above passes.
- No state loses more than 20% of its leads versus the previous build without the task saying why.
- Any recipe whose claim turns out wrong is corrected in the recipe file itself, with the evidence.

## Tasks

- [ ] T1 Fort Worth returned **1 lead**. Audit `propertystack/recipes/tx/fort-worth.json` by the method above: true row count, newest date, real columns. Decide and record which it is — broken query, frozen feed, or a genuinely tiny result — and fix it if the fix is contained. Write the evidence into `propertystack/runs/`. Tests for any code change.
- [ ] T2 San Antonio returned **2 leads**, for a city of 1.4 million. Same audit, same decision, same evidence, on `propertystack/recipes/tx/san-antonio.json`.
- [ ] T3 San Marcos returned **4 leads** and Austin returned **47**. Audit both recipes together (they are neighbouring Central Texas permit feeds); record the true totals and newest dates for each, and fix whichever is under-reading.
- [ ] T4 The Houston **city permit feed** (`houston.json`) returned 18 while the Harris County bulk file gave 383. Audit it: is it duplicating the county file, reading a stale layer, or missing a filter? Record what it uniquely adds, and if it adds nothing a seller can use, disable it with the reason in the recipe rather than leaving it looking healthy.
- [ ] T5 Audit the two Tarrant County sources (`tarrant-tad.json` 177, `tarrant-tad-sales.json` 24) and `arlington.json` (178). These look healthy — prove it: true totals, newest dates, and 2 rows each verified against an independent listing. Record anything they drop that a seller needs.
- [ ] T6 Audit `tabs.json` (126) and `tdhca.json` (212) the same way. TDHCA awards are planned projects; confirm they are not being shown as if construction has started, and that each one has a date a seller can act on.
- [ ] T7 The Dallas and Harris bulk files hold columns we never read. List every field in both that maps to a seller need — owner name, contact, building name, valuation, year built — and add the ones that are contained wins to the recipes. Houston still has 13 leads with no size and Dallas has 3 phones out of 481; say exactly what the files can and cannot supply.
- [ ] T8 Make a silent under-read impossible. Add a size-and-freshness guard to the run: each source records the true total the endpoint holds and its newest date alongside its lead count, and the run reports loudly when a source returns a tiny fraction of what its endpoint holds. This is the check that would have caught Dallas, Albuquerque and Fort Worth on day one. Tests.
- [x] T9 Narrow the routine run to Texas. `tooling/new-run.sh` with no argument runs Texas only; Arizona and New Mexico keep their existing site data and are re-run only when named explicitly. Make sure the site still shows Arizona and that the totals do not drop. Tests.
- [ ] T10 Clean the 62 Dallas building names carrying county shorthand — "(N/C 89%) SOLTRA FIREWHEEL", "(91% COMPLETE) FLYNN @ LIVE OAK", "AMLI TREE HOUSE (ECU 2 ACCTS)". Strip only the county's own bracketed codes and percentages, never a real word, and prove it with a test over all 62.
- [ ] T11 Write the Texas source scorecard: one page in `propertystack/runs/` listing every Texas source with its true total, what we take from it, its newest date, and whether a seller can call its leads. This is the page that makes the next silent failure obvious in ten seconds.

## How to try it

1. Run `bash tooling/dev.sh` and open http://localhost:8765/index.html — the list should still load, and the header should still show a building count with a separate "last 6 months" number.
2. Click any Texas building: it should have a real street address, a unit count, and a date. If a lead has none of those, the audit missed something.
3. Open `propertystack/runs/source-health.json` — after T8 every Texas source should show what it returned **and** what its endpoint actually holds.
