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
