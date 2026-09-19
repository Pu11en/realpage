# Plan: Gap 3, honest freshness (Software Sellers edition, 2026-09-18)

Decision (Drew): no automatic refresh. Hide the "new this week" count; show the real data date and point to "add your area".

Check: python3 -m pytest -q tooling/qa/fixes_tests/
Try: bash tooling/dev.sh
Open: http://localhost:8765/index.html

## Tasks
- [ ] T1 Early Leads: remove the "NEW" stat card (and the "New" badge on rows if it depends on newThisWeek). Keep Leads, Units in play, Opening soon.
- [ ] T2 "Last updated" in the sidebar shows the date the lead data was built (from the area JSON / build time of site/data/areas/*.json), not the site deploy date. Today it wrongly shows Sep 18 while the data is from Sep 15.
- [ ] T3 Under the stats on Early Leads: one line "Data from <date>. Don't see your area? Ask for it" linking to map.html#request-area (Gap 2).
- [ ] T4 Tests for all three; screenshot Early Leads for Drew.

## How to try it
1. Early Leads has no "New" box.
2. The date shown is when the data was gathered (Sept 15).
3. The "Ask for it" link jumps to the area request box on the Map.
