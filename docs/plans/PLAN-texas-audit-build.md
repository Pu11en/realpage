# Plan: prove every Texas source, and make a silent failure impossible (2026-09-20)

One plan, one loop. This replaces `PLAN-texas-source-audit.md` as the thing to run; that file
stays as the written record of why. `PLAN-tx-agenda-sources.md` is deliberately **not** in here —
it is gated on a go/no-go and starts only when Drew says so.

Read first: `handoffs/2026-09-20-texas-only-scrape-audit.md`.

## The one question every task answers

**Can someone selling software to apartment buildings call this lead today?**
That needs a real building name, a real street address, a unit count, and a date that is
genuinely recent. A finding that touches none of those is not worth the task.

## Already done, do not redo

- Dallas County's broken download link, Houston's glued address and unit count, Albuquerque
  recorded as frozen, the hero line's real "last 180 days" count, Arizona's month-only sale dates.
- **The routine refresh is Texas only.** `tooling/new-run.sh` with no state runs `tx`; AZ, NM and
  NY keep their site data and refresh only when named. Done 2026-09-20, 609 tests pass.

## The method for auditing one source

1. Ask the endpoint for the **true total it holds** (ArcGIS: `&returnCountOnly=true`).
2. Ask for the **newest date it holds** (ArcGIS: `outStatistics` with `max` on the date field).
3. Compare both to what the recipe returns. **A large gap is the finding.**
4. Read the source's **real column list**; name every field we drop that a seller needs.
5. Verify **2 rows against an independent public listing** — name and unit count must match.
6. Write the evidence into `propertystack/runs/`. Fix it only if the fix is contained.
   **A frozen feed is a finding, not a bug** — never "fix" the runner for one.

Any URL built by hand must be percent-encoded. A literal space in a URL is what kept Dallas
County broken for months; `_safe_url` in `tooling/run_area.py` already handles it.

Check: python3 -m pytest -q tooling/qa/fixes_tests/ propertystack/skills && python3 tooling/qa/check_lead_data.py
Try: bash tooling/dev.sh
Open: http://localhost:8765/index.html

## Quality gates (run after every task; a task is not done until they pass)
- The Check command passes.
- No state loses more than 20% of its leads versus the previous build without the task saying why.
- Any recipe whose written claim turns out wrong is corrected in the recipe file, with evidence.
- Every finding is written into `propertystack/runs/`, even when nothing is fixed.

## Stage 1 — the alarm (run alone, first; it touches the shared runner)

- [x] S1 Record what each source **actually holds**. For every recipe, the run stores the
  endpoint's true total and its newest date next to the lead count it kept, in
  `propertystack/runs/source-health.json`. Sources that cannot be counted cheaply (the county zip
  files) record why instead of a fake number. Tests.
- [x] S2 Make it shout. A source that keeps **under 25%** of what its endpoint holds is flagged
  `suspect` with both numbers, and the run prints a loud line naming it. A source whose newest
  record is **over 12 months old** is flagged `stale` the same way. The run still finishes — one
  bad source never blocks a refresh. Tests, including one that proves Fort Worth's real numbers
  trip it.
- [x] S3 Put the alarm where it is seen. The weekly Discord notice names every `suspect` and
  `stale` source, or says "all sources healthy". Tests.

## Stage 2 — the four suspects (independent of each other; safe to run side by side)

- [ ] S4 **Fort Worth returned 1 lead.** Its own recipe note records 2,227 matching rows from a
  live `returnCountOnly` check, and the note says ArcGIS paging was added for exactly this layer.
  Find why 2,227 became 1, fix it if the fix is contained, and record the evidence. Tests.
- [ ] S5 **San Antonio returned 2 leads** for a city of 1.4 million. Its note records 156 real
  rows found live across two CKAN resources. Same audit, same decision, same evidence. Tests.
- [ ] S6 **San Marcos returned 4 and Austin 47.** Audit both together — neighbouring Central Texas
  permit feeds. Record each one's true total and newest date, and fix whichever under-reads.
- [ ] S7 **Houston's city permit feed returned 18** while the Harris County file gave 383. Is it
  duplicating the county, reading a stale layer, or missing a filter? Record what it uniquely
  adds. If it adds nothing a seller can use, disable it **with the reason written in the recipe**
  rather than leaving it looking healthy.

## Stage 3 — prove the healthy ones (independent of each other)

- [ ] S8 Audit the two Tarrant County sources (`tarrant-tad` 177, `tarrant-tad-sales` 24) and
  `arlington` (178). They look fine — prove it. True totals, newest dates, 2 rows each verified
  against an independent listing. Record anything they drop that a seller needs.
- [ ] S9 Audit `tabs` (126) and `tdhca` (212) the same way. TDHCA awards are planned projects:
  confirm they are not shown as if construction has started, and that each has a date a seller
  can act on.
- [ ] S10 Mine the Dallas and Harris bulk files. List every column in both that maps to a seller
  need — owner name, contact, building name, valuation, year built — and add the contained wins.
  Houston still has 13 leads with no size; Dallas has 3 phones out of 481. Say exactly what these
  files can and cannot supply.

## Stage 4 — the numbers a buyer sees (independent of each other)

- [ ] S11 **Settle the count mismatch.** `source-health.json` says Dallas returned 501; the
  2026-09-20 run table says 481. Find which is right, make one of them the single source of truth,
  and add a test that fails if the site total, the state files and the health file ever disagree
  again.
- [ ] S12 Clean the **62 Dallas building names** carrying county shorthand — "(N/C 89%) SOLTRA
  FIREWHEEL", "(91% COMPLETE) FLYNN @ LIVE OAK", "AMLI TREE HOUSE (ECU 2 ACCTS)". Strip only the
  county's own bracketed codes and percentages, never a real word. Prove it with a test over
  all 62.
- [ ] S13 Fix the leads a seller cannot use. **318 leads have no date at all and 41 have no
  stage.** Say where each came from, fill what can be filled from the source, and hide or clearly
  mark the rest. Tests.
- [ ] S14 Kill the meaningless number. `newLast7Days` in `summary.json` equals every lead (1,876).
  Either make it true or remove it. Tests.

## Stage 5 — the page that makes the next failure obvious (run last)

- [ ] S15 Write the **Texas source scorecard**: one page in `propertystack/runs/` listing every
  Texas source with its true total, what we keep, its newest date, its suspect/stale flag, and a
  yes/no on whether a seller can call its leads. This is the page that makes the next silent
  failure visible in ten seconds.

## Running order

- **S1, S2, S3 run first and alone** — they change `tooling/run_area.py`, which every other task
  depends on.
- **S4 to S14 are independent of each other.** Each touches its own recipe and its own evidence
  file. Any of them can run side by side.
- **S15 runs last**, because it reports what the others found.

## How to try it

1. Run `bash tooling/dev.sh` and open http://localhost:8765/index.html — the list loads, the
   header still shows a building count and a separate "last 6 months" number, and the totals have
   not dropped.
2. Click any Texas building: real street address, a unit count, and a date. If a lead has none of
   those, an audit missed something.
3. The run's own output should now name any source that returned far less than its endpoint holds
   — or say every source is healthy.
