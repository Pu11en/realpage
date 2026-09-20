# Handoff: Texas-only lead-run audit (next session)

Written 2026-09-20 at the end of the "realpage · part 3" thread. Everything below is
committed locally on `main`. **Nothing has been pushed to GitHub.** Five commits are waiting:
`ae13da0`, `401e1e6`, `0cb59da`, `e88ae18`, `15c6cbd`, plus one in the nested `business/` repo.

## What the next session is for

Drew's decision, in his words: stop running every state, hone the path down to **Texas only**,
and give the Texas run a session whose whole job is to **find the class of problem that this
session hit by accident**.

That class, concretely, is:
1. a source that "works" but quietly returns almost nothing,
2. two fields glued into one and published wrong,
3. a field the source already has that we throw away,
4. a feed that is live but frozen years ago,
5. a count on the site that does not match the files behind it.

All five happened today, and all five were found by chance, not by any check.

## The smoking gun already visible

Today's Texas run, per-source (`propertystack/runs/source-health.json`):

| source | leads |
| --- | --- |
| dallas-dcad | 481 |
| houston-hcad | 383 |
| tdhca | 212 |
| arlington | 178 |
| tarrant-tad | 177 |
| tabs | 126 |
| austin | 47 |
| tarrant-tad-sales | 24 |
| houston (permits) | 18 |
| san-marcos | 4 |
| san-antonio | 2 |
| fort-worth | 1 |

**Fort Worth returned 1. San Antonio returned 2. San Marcos 4. Houston's permit feed 18.**
Those are enormous cities. Dallas looked exactly like that right up until it turned out to be
completely broken. Every one of those is a suspect until proven otherwise, and "worked" in
source-health means nothing -- Dallas reported `failed` for months and nobody noticed either.

## What was fixed today (do not redo)

- **New Mexico** was not a runner bug. Albuquerque's city feed is live but frozen: the whole
  layer stops 2025-01-16 and its newest apartment permit is 2024-09-19, 731 days old, so all
  191 apartment rows fall outside the 24-month window. Las Cruces holds 13 apartment NEW
  permits in total, 2 recent. NM is genuinely 12 leads and stays hidden. Every empty source
  now explains itself in the run log and in source-health.
- **Houston addresses** carried HCAD's `str_unit` on the end ("9757 WINDWATER DR 150"). It is
  the unit count -- verified 875/875 on B1 rows. `appraisal_zip` gained
  `address_unit_suffix_field`; 365 of 378 Houston leads now have a real size, and a street
  that genuinely ends in a number (NASA RD 1, HIGHWAY 3) keeps it.
- **Dallas County** had been failing every run: its download link holds a literal Windows path,
  and the runner's shared fetcher did not percent-encode it. `_safe_url` in `tooling/run_area.py`
  encodes only URLs that actually contain a space, backslash or non-printable character.
  Dallas sold leads then arrived with no address; `find_sold_apartments` now falls back to
  `ACCOUNT_INFO.CSV`. 481 Dallas leads, all with name, units and address.
- **The hero line** no longer says "just". It reads size plus a real
  `recentLast180Days` count (175 of 1,876). Both sites.
- **Arizona sale dates** now carry `sale_date_precision: "month"` and display as "Sold Aug 2026",
  because Maricopa's column is SALEDATE_MMYYYY and the day was ours, not the county's.

A one-time migration, `tooling/migrations/2026-09-20-houston-address-unit-suffix.py`, preserved
`firstSeen` for 365 Houston buildings across the address change. It is already run; it is
safe to re-run and will find nothing.

## Known, deliberately not fixed

- **62 Dallas building names carry county shorthand**: "(N/C 89%) SOLTRA FIREWHEEL",
  "(91% COMPLETE) FLYNN @ LIVE OAK", "AMLI TREE HOUSE (ECU 2 ACCTS)". Cosmetic, but it reads
  as sloppy. Not auto-stripped because a blind rule would cut real names.
- **`newLast7Days` in summary.json equals every lead** (1,876). It is not displayed anywhere,
  so it was left alone, but it is meaningless as written.
- **318 site leads have no date at all**, and 41 have no `stage`.
- **Phones are almost entirely missing** on county-sourced leads: 3 of 481 in Dallas, 1 of 378
  in Houston, 0 of 139 in Arizona.
- **summary.json counts 1,876 while the area files hold 1,878** -- the 2-lead NY area is
  excluded as manually hidden. Correct, but worth stating if anyone compares the numbers.

## What a good audit task looks like

One source per task. For each Texas source, in its own fresh session:

1. Call the endpoint by hand and get the true total the source holds (for ArcGIS,
   `&returnCountOnly=true`, or `outStatistics` with `max` on the date field for freshness).
2. Compare that to what the recipe returns. A large gap is the finding.
3. Check the newest date the source holds. Frozen feed -> say so, do not "fix" the runner.
4. Read the source's real column list and name every field we drop that a seller needs:
   unit count, owner, contact, building name.
5. Verify 2 rows against an independent public listing -- names and unit counts must match.
6. Write the finding into `propertystack/runs/` and fix it only if the fix is contained.

Judge everything against one question: **can someone selling software to apartment buildings
call this lead today?** That needs a real building name, a real address, a size, a date that
is actually recent, and a reason to call.

## Key files

- `tooling/run_area.py` -- the parallel runner, `_safe_url`, `_empty_note`
- `propertystack/recipes/tx/` -- the 12 Texas recipes
- `propertystack/runs/source-health.json` -- per-source status and counts
- `propertystack/runs/data-spot-check-2026-09-20.md` -- today's evidence, with the method
- `propertystack/runs/needs-a-source.md` -- areas with no usable feed, and why
- `propertystack/skills/lead-finder-permits/appraisal_zip.py` -- county bulk-file adapter
- `propertystack/skills/lead-finder-permits/find_upcoming.py` -- permit adapter, freshness window
- `site/data/build_data.py` -- `build_summary`, `_area_signal_text`, `_moved_since`
- `tooling/qa/check_lead_data.py` -- the data check
- Tests: `tooling/qa/fixes_tests/` (284) and `propertystack/skills/*/tests/` (144)

## Open question for Drew

He has not yet answered how to run it: `/gowork` (one source per fresh session, on a safe
copy) or a normal session. Ask that before writing the plan -- it changes the plan's shape.
