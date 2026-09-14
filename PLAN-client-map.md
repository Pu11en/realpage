# PropertyStack: where RealPage already has clients (fast + cheap)

Written 2026-09-13 with Drew (answers: `/home/drewp/main-projects/handoffs/2026-09-13-realpage-clients-plan-answers.md`).
Only purpose: show where RealPage already has apartment clients, so the lead finder
(`PLAN-lead-finder.md`, runs after this) avoids those places. Keep it **fast and cheap**:
**max 150 Jina searches**, under an hour. Runs on Drew's computer; data only until the map
redo task. Localhost only; no push (Drew pushes after he checks).

RealPage resident logins live at **loftliving.com**, **activebuilding.com** and
**onesite.realpage.com** (see `tooling/pms_detect.py`). NOT `residentportal.com` -- that's Entrata.
A building whose own site links to one of these is a proven client.

Run with: `Do the next unticked task in PLAN-client-map.md, then tick it and stop.`
Check: `bash tooling/qa/check-client-map.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765/map.html

## How to try it (30 seconds)
1. Open the map: states are shaded -- darker = more RealPage buildings found.
2. Point at a shaded state: it shows the count and its top cities.
3. No building dots and no proof cards on the map (proof links stay in the data file).

## Tasks

- [x] **C1 Skeleton + tests.** `propertystack/skills/client-map/` with `SKILL.md` (purpose,
  150-search cap, outputs) and `run.py`. Tests with saved fixtures only (no network): a
  search-budget object that stops cleanly at the cap, URL → vendor using `pms_detect.py` rules
  (loftliving/activebuilding/onesite = RealPage; residentportal = Entrata, rejected), duplicate
  removal (same portal subdomain or same address = one building), per-state/per-city counts.
  Tests fail first; commit.
- [x] **C2 States + cities (free).** Pick the 15 states with the most new 5+ unit apartment
  permits in the last 12 months (Census Building Permits Survey, state files, free; reuse
  `scout-areas/census.py` if it fits). Per state, list its ~10 cities with the most apartments
  (Census place-level permit or ACS renter data). Save `propertystack/data/client-map/targets.json`.
  Cache raw downloads under `propertystack/data/raw/census/`. Commit.
- [x] **C3 Search run (💲 max 150 searches).** One Jina search per target city (e.g.
  `"loftliving.com" OR "activebuilding.com" OR "onesite.realpage.com" apartments <city> <state>`),
  in state order, stop at 150. For each hit, open the building's site with crawl4ai
  (`http://localhost:11235`, free; Playwright only if it needs a real browser), confirm the
  RealPage link with `pms_detect.py`, pull name + address. Turn addresses into lat/lon with the
  free Census batch geocoder (OpenStreetMap as backup). Save
  `propertystack/data/client-map/buildings.csv` (name, city, state, lat, lon, proof_url) and
  `counts.json` (per state and per city). Log searches used to `propertystack/runs/`. Commit.
- [ ] **C4 Map redo (simple).** Redo `site/map.html`: shade each state by its RealPage
  building count from `counts.json` (built into site data by `site/data/build_data.py`);
  pointing at a state shows the count and its top 3 cities. Remove the building dots and proof
  cards (proof links stay in the data only). Keep visuals minimal -- Drew does design himself.
  Update `tooling/qa/check_map.py` to match. Check passes. Screenshot to `/tmp/client-map.png`
  and look at it. Commit. Tell Drew in plain words it's ready to try.
