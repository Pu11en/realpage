# PropertyStack lead finder, part 2: permits (new apartment projects)

Part of the lead finder. **Read the rules in `PLAN-lead-finder.md` first** (area-agnostic: no place
names in code; Plano is never rerun; never guess facts; SearXNG first, Jina fallback; localhost only,
no push). **NOT approved to run yet.** Starts after part 1 is merged; can run **at the same time as parts 3, 4 and 5**. Touches only its own skill folders.

Run with: `Do the next unticked task in PLAN-lf-2-permits.md, then tick it and stop.`
Check: `bash tooling/qa/check-lead-finder.sh`
Try: `bash tooling/dev.sh`
Open: (behind the scenes; results show on the site after part 6)

## How to try it (30 seconds)
1. Run the Check line: it passes.
2. The saved city list for the sample state has cities ordered by most new apartment permits.
3. A sample permit file becomes one project per building (several permits merged), apartments with 20+ units only.

## Tasks

- [ ] **2.1 Rank the state's cities (free).** `lead-finder-cities/`: Census place-level permits
  (5+ units, last 12-24 months) for any state; write `propertystack/data/<state-slug>/cities.json`
  (city, permits, RealPage count from client map). Fixture tests. Commit.
- [ ] **2.2 Permit recipes + catalog lookup.** `propertystack/recipes/*.json` format (by permit
  system -- Socrata / ArcGIS / Accela / EnerGov / Tyler -- or by city): how to query new
  multifamily permits, fields, date tested, how complete. `find-sources` first asks the free
  **Socrata and ArcGIS catalog APIs** for a city's permit dataset. Fixture tests. Commit.
- [ ] **2.3 `find-sources` fallback.** No catalog hit: search for the city's permit portal, identify
  the system, test on 5 permits, save the recipe; nothing online → city "skipped: no permits
  online". Fixture tests. Commit.
- [ ] **2.4 `find-upcoming` rebuilt for any city.** Replace the old Plano-only version: city + recipe
  → new apartment permits (permit issued → leasing). Keep only type/description apartment or
  multifamily, or 20+ units; unknown units kept for 2.5 to fill. Several permits for one project
  **merged into one record** with its permit link. Fixture tests. Commit.
- [ ] **2.5 `project-details` (new).** Clean addresses (usaddress + free Census batch geocoder) so
  merging is reliable. One web lookup per project: address, units, developer, opening date, news
  link, website. Never guess; still-unknown units → drop. Fixture tests. Commit.
