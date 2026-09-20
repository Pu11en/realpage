# Plan: one-command lead runs — New Mexico + fresh Texas and Arizona (2026-09-19)

Goal: Drew triggers one run; everything downstream updates by itself and goes live.
Speed matters: sources are pulled in parallel inside the runner (the bot runs one build at a time,
so parallelism belongs in the script, not in extra builds).

Decisions (Drew, 2026-09-19):
- Cover: New Mexico (Albuquerque, Rio Rancho, Santa Fe, Las Cruces + Bernalillo County sales), plus fresh runs of Texas and Arizona using their existing sources.
- Publish live automatically when the checks pass. No waiting for Drew.
- Never advertise which states we cover, anywhere. The product is "U.S. apartment leads".
- Hero element (site + landing), filled from data after every run:
  "Last check <date>: <N> buildings just filed permits, <M> just sold. <TOTAL> tracked."
- Say "check" or "run", never "scrape", in anything a visitor sees.
- **The run never stops to ask Drew anything.** Rules decide; a source that fails is retried once, then skipped with a note; the run carries on and reports at the end.
- **Cheap by design:** the pulls are plain downloads with no AI. AI is used only to find a replacement source for a city that has none, capped at **20 searches per city** and **100 per run**; when the cap is hit the city is listed as "needs a source" and the run continues.
- Keep a copy of each state's data before a run (instant undo), and record each source's health (worked / empty / failed) in propertystack/runs/source-health.json.

Check: python3 -m pytest -q tooling/qa/fixes_tests/ propertystack -x -q
Try: bash tooling/dev.sh
Open: http://localhost:8765/index.html

## Quality gates (run after every task; a task is not done until they pass)
- The Check command above passes.
- `python3 tooling/qa/check_lead_data.py` passes: every lead has a source URL, no duplicate address inside a state,
  every lead has a stable id, and no state loses more than 20% of its leads versus the previous build (that means a broken source).

## Tasks
- [x] T1 Stable ids + honest "new": give every lead a content id (state + normalised address + name), keep it across runs, and stamp `firstSeen` by that id in site/data/build_data.py (today it matches by list position, so a re-run mislabels new leads). Migrate existing tx/az leads so today's rows keep their first-seen date. Tests.
- [x] T2 `tooling/qa/check_lead_data.py`: the data sanity check above, runnable on any state folder, exits non-zero with a plain-English list of problems.
- [x] T3 `tooling/run-area.sh <state...>`: one command per state that runs every recipe source for that state **in parallel** (max 6 at once), retries a failed source once, skips a source that is down and says so, writes propertystack/data/<state>/leads.json, and prints counts (total, new since last run, permits, sales). Resumable: re-running skips sources already finished today. Dry-run flag for testing without network.
- [x] T3b "Find a source" skill (propertystack/skills/find-source/): given a city and state, try the usual homes for permit data in order -- the city open-data portal, Socrata, ArcGIS, Accela/Citizen Access, then the county -- test each candidate for real apartment rows, and write a working recipe JSON when one passes. Capped: 20 searches per city, 100 per run. Never invents a URL; if nothing passes it writes the city to propertystack/runs/needs-a-source.md and returns cleanly. Offline test with recorded responses.
  Guardrails (Drew was unsure about this skill, 2026-09-19): a candidate source is only accepted if it returns at least 5 rows that look like real apartment projects -- a street address, a date, and either a unit count or a project description -- and the rows must survive tooling/qa/check_lead_data.py. Anything it writes is marked `"source": "auto-found"` in the recipe so it can be reviewed or deleted, and the Discord summary names every auto-found source.
- [x] T4 New Mexico recipes — **start from docs/plans/nm-sources-research.md** (verified live endpoints: Albuquerque and Las Cruces ArcGIS permit layers with owner names and apartment filters; Bernalillo / Doña Ana / Santa Fe county parcel layers with owners but no sale price; NM MFA LIHTC award spreadsheets statewide. Santa Fe and Rio Rancho have NO machine-readable permit feed — use the MFA awards and county parcels for them, and list them in needs-a-source.md) in propertystack/recipes/nm/: albuquerque.json, rio-rancho.json, santa-fe.json, las-cruces.json (city permit feeds, ArcGIS/Socrata style, copy the shape of recipes/az/phoenix.json) and bernalillo-county-sales.json (county assessor sales, shape of recipes/az/maricopa-county-sales.json). Find each feed's real URL from the city/county open-data portal; if a city has no usable feed, say so in the file and skip it rather than inventing one.
- [ ] T5 Run New Mexico for real with T3. Verify with T2. Expect a few hundred buildings; if under 50, stop and report which sources came back empty.
- [ ] T6 Refresh Texas with T3 (all existing tx recipes). Report how many are genuinely new.
- [ ] T7 Refresh Arizona with T3 (all existing az recipes). Report how many are genuinely new.
- [ ] T8 Site data: build_data.py writes site/data/summary.json (total tracked, new in last 7 days, permits filed, sold, last check date) and hides any area with under 25 leads automatically. The Leads page shows the hero line from summary.json and no longer names covered states anywhere (drop the "Covered: Texas, Arizona" chip and sidebar line). Tests.
- [ ] T9 Landing page hero element: business/marketing/landing/server.py fetches https://app.cranesignal.com/data/summary.json at startup and every hour (cached, falls back to the last good copy) and injects the same line into the hero. No state names on the landing page either. Test with a fake summary.
- [ ] T10 Chat agent: rebuild its baked data so it knows the new buildings, and redeploy the chat service. Ask it 3 questions about New Mexico buildings locally and check the answers cite sources.
- [ ] T11 `tooling/new-run.sh <state...>`: the whole chain in one command — run-area (parallel) → build site data → Check + quality gates → commit → push (auto-deploys) → post one Discord line to the sign-ups webhook: "Last check <date>: N permits, M sales, TOTAL tracked (<state list>)". Any failed gate stops before publishing and says what broke.
- [ ] T11b Undo and health: `tooling/new-run.sh --undo <state>` restores the pre-run copy and republishes; the Discord summary line adds "sources: X worked, Y empty, Z failed" and links needs-a-source.md.
- [ ] T12 End to end: `bash tooling/new-run.sh nm tx az`, confirm the live site shows the new hero line and the new leads, and post the summary here.

## How to try it
1. The Leads page hero says "Last check <date>: N buildings just filed permits, M just sold. TOTAL tracked."
2. No page names which states are covered.
3. "Get only the new ones" downloads only buildings added since your last download.
