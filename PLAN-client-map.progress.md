# Progress: PLAN-client-map

## C1 Skeleton + tests — done (commit 7356a24)
- Added `propertystack/skills/client-map/` with `SKILL.md`, `run.py` (SearchBudget capped at 150, `search_targets` stops cleanly at the cap, `vendor_of` via pms_detect VENDORS, `is_realpage_proof` = loftliving/activebuilding/onesite.realpage.com only, `dedupe` by portal host or normalized address, `counts` per state/city) and `tests/test_client_map.py` (12 fixture-only tests).
- Checked: tests failed with an empty run.py (12 failed), then 12 passed; `check-panel.sh` clean (0 problems, panel clean).
- Open: `run.py` main is a stub until C3.

## C1 fix — check command (plan check failed)
- The bot runs `Check:` without a shell, so `&&` reached pytest as a filename. Moved both steps into `tooling/qa/check-client-map.sh` and pointed the plan's `Check:` line at it.
- Checked: `bash tooling/qa/check-client-map.sh` → 12 passed, 0 problems, panel clean, exit 0.

## C2 States + cities — done (commit fa6e2d6)
- Added `propertystack/skills/client-map/targets.py`: sums the 12 latest monthly Census Building Permits files (Aug 2025–Jul 2026) for 5+ unit apartments, per state and per city (place files, 4 regions). Skips county/unincorporated areas, trims "town/village/borough/township" from names. Reuses `scout-areas/census.py` fetch; raw files cached (gitignored) in `propertystack/data/raw/census/`.
- Saved `propertystack/data/client-map/targets.json`: 15 states × 10 cities = 150 targets (exactly the 150-search cap). Order: TX, CA, FL, NY, NC, WA, GA, NJ, CO, VA, OH, AZ, WI, TN, UT.
- Checked: 3 new fixture tests (15 total pass); `bash tooling/qa/check-client-map.sh` clean.
- Open: some small-town picks (e.g. Kiryas Joel NY, Palm Tree NY) rank high on permits but may yield few hits; "most apartments" uses new permits, not ACS renter counts.

## C3 Search run — done (commit 803f931)
- `run.py` now runs the search: one Jina search per target city (150 targets), exactly **150 paid searches total** (1 trial + 149), cached in `data/raw/client-map/searches.json` (gitignored) so reruns are free. 1,090 hits.
- Most hits are RealPage portal pages themselves (`x.loftliving.com`, `x.activebuilding.com`, `oll-leasing.loftliving.com/?siteId=`) with name + address in the snippet; 67 other hits (Yellow Pages, Instagram…) were followed to the portal link they mention and read with local crawl4ai (3 s render wait). Every proof URL passes `pms_detect` RealPage rules; Entrata rejected.
- Duplicates removed by portal subdomain, or shared host + siteId, or same address. City names normalized (TACOMA → Tacoma). Geocoded with Census batch (OSM backup), cached in `data/raw/client-map/geocode.json`.
- Result: **260 buildings in 20 states** (TX 40, NC 32, AZ 27, FL 26, WA 24, VA 20, CA 19, TN 16, CO 14, OH 10, …); 9 without lat/lon (still counted). Files: `data/client-map/buildings.csv`, `counts.json`, log `runs/20260913T213834-client-map.json`.
- Checked: 7 new fixture tests (22 pass); `bash tooling/qa/check-client-map.sh` clean; spot-checked sample rows.
- Open: some names are just the street address (leasing pages with no building name); a few buildings sit outside the 15 target states (nearby hits) — counted under their real state. Counts show where RealPage is *found*, not full market share.

## C4 Map redo — done (commit 5ab5413)
- `site/data/build_data.py` now also writes `site/data/client-map.json` from `counts.json`: per state (full name) total + top 3 cities (city spelling variants like Mckinney/McKinney merged).
- `site/map.html` + `site/js/map.js`: states shaded green by count (brighter = more, sqrt scale), pointing at a state shows a small box with count and top 3 cities; unsearched states say "None found". Building dots, proof cards and the reach.json read are gone (reach.json file kept; scout-areas still writes it).
- `tooling/qa/check_map.py` updated: every state in client-map.json is shaded, no dots, no card, hovering the top state (Texas) shows 40 + Houston. `check-client-map.sh` now runs check_map too.
- Checked: `bash tooling/qa/check-client-map.sh` → 22 passed, panel clean, check_map 0 problems. Screenshot /tmp/client-map.png looked right (Texas brightest, tooltip Houston 7 / Fort Worth 5 / McKinney 5).
- Open: plan wording said "darker = more"; on the dark theme brighter green = more, so the page says that.
