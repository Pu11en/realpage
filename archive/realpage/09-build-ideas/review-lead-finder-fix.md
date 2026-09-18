Source: PLAN-lead-finder-fix.md (461479d); docs/2026-09-14-lead-finder-tools-v2-research.md; PLAN-lead-finder-build.progress.md (6.2-6.8); Maricopa Sales Affidavits item metadata (arcgis.com, fetched 2026-09-14)
Fetched: 2026-09-14
Method: mvp-plan-review gates G1-G7 against the plan text and repo evidence; one live metadata check
Confidence: medium-high (endpoints were live-tested by the research run; sales-file fields not yet opened)

# Review: lead finder fix plan

Verdict: GO WITH FIXES

| Gate | Result | Why |
|---|---|---|
| G1 Outside-in | PASS | Every input is public: city permit layers, county sales file, building websites, Jina/Brave search; read-only, polite fetching kept from 1.3. |
| G2 Named buyer | PASS | Buyer and weekly use already set in sell-plan-2026-09-12.md / PLAN-lead-finder.md (RealPage sales reps: "who to call and why now"); the fix plan doesn't change it. |
| G3 Absence / benefit | PASS | Absence was settled for PropertyStack earlier (brainstorm-2026-09-10-pitch-to-realpage.md §4 C1); this plan is a quality fix, not a new product. |
| G4 MVP scope | FIX | Done-bar is measurable, but it expects websites/software for projects that aren't built yet, and there's no cut list or timebox. |
| G5 Feasibility | FIX | Three unproven dependencies: unit counts missing in 5 of 8 AZ sources (the "unknown units → drop" rule would delete most of them), sales-file property-type field not yet opened, Brave spend beyond the free $5. |
| G6 Cheaper model | FIX | Answer key can be built from the same permit layers the tool reads (circular); "city's ArcGIS hub search" has no rule for finding the hub URL; old AZ run data handling is loose. |
| G7 Pitch | PASS | Artifact = the Early Leads AZ table + deep dives on localhost, then Under the Hood; unchanged from prior plans. |

## Required fixes
1. **Quality bar by stage (F9).** Website/software/phone targets apply only to buildings that exist (leasing or sold). For permitted/under-construction projects, "not picked yet" is the correct software verdict and the target is a developer/owner name + office phone (≥50%). Otherwise the bar can never pass and the run STUCKs for the wrong reason.
2. **Unit counts (F4/F5 + 2.5 rule).** Phoenix, Scottsdale, Gilbert, Maricopa County and Peoria layers have no unit field. Add a unit lookup order: permit field → number in permit description ("300-unit", "(11) unit") → the project's own site/news via Jina (with the F2 relevance check) → county parcel/assessor record. Decision for Drew on what happens if still unknown (see Open decisions).
3. **Answer key independence (F6).** Build it only from sources the tool doesn't read: news articles, developer press releases, apartment association "new communities" lists, building websites. Not from city permit layers or the sales file. Record the source type per entry.
4. **Sales-file spike (F5).** First open the zip's file-spec document and confirm the property-type / use-code field that marks apartments and whether unit counts exist; if units are missing, get them from the parcel file or the building site. Acceptance: ≥10 real 20+ unit apartment sales in the last 24 months with buyer and date.
5. **Brave cap (F1).** Count Brave calls separately with a hard cap of 800/month across runs (inside the $5 free credit); when hit, Jina-only and log it.
6. **Hub URL rule (F3).** Find a city's ArcGIS hub through the ArcGIS Online search result's owner org (`orgId` → `https://<org>.maps.arcgis.com` / hub site) rather than guessing; if none, skip that source.
7. **Old data (F11).** Move `propertystack/data/az/` and `propertystack/runs/AZ/20260914-full/` to `propertystack/archive/az-run1/` before the new run, so nothing from the junk run leaks into merges or the chat.
8. **Cut list + timebox.** Add: out of scope = New York, Chandler/Goodyear/Buckeye (Accela-only), Shovels.ai, Google Places, email addresses, named contacts beyond permit/news. Timebox ≈ 15 tasks × 20-30 min ≈ 6-8 hours of bot time.

## Risks accepted
- Some Arizona cities stay blank (no free data) -- honest skips, shown as such on the site.
- Tucson's DwellingUnits is often 0 -- handled by fix 2's lookup order.
- Jina's $/token rate is third-party-sourced; cost stays trivial at ~450 searches/state either way.

## Open decisions for Drew
1. **Units still unknown after the lookup order:** default = keep the project if the permit clearly says new multifamily construction, show "Units: not public yet", rank it below projects with known units (instead of dropping it).
2. **Brave overage:** default = never pay beyond the free $5/month (cap at 800 calls).
3. **Near-Texas states:** default = run NM and LA only if each passes a 10-building answer key; don't force a third state.
