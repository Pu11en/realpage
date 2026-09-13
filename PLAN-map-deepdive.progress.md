## P1 Check script — done (2026-09-13)
- Added `tooling/qa/check_map.py` (serves site/ on 8791, Playwright, ~14 s).
- Contract for later tasks: dots are `[data-dot]`, the dot card is `#map-card` (needs ≥1 `<a>`), buttons are `[data-deep-dive]`; property test uses the first lead in leads.json with a `propertyId`.
- Ran it: fails as expected (4 problems: no map.html, no redirect, no buttons on 42 rows / property page). check-panel.sh still clean.

## P2 Map page — done (2026-09-13)
- Added `site/map.html` + `site/js/map.js`: US states outline (vendored us-atlas + d3-geo + topojson-client in `site/vendor/`, no CDN), Albers USA projection; green dots sized by `signs`, yellow diamond + "researching" for `kind: "scout"`; click → `#map-card` with city, count, proof links.
- `site/data/reach.json` seeded by `tooling/reach/seed_reach.py`: Plano (28) and Richardson (8) = 36 proven RealPage buildings, links = their proof URLs. P3 should keep dots with `source: "our-data"` (the seed script only replaces those).
- Nav: Master Table → Map; `master-table.html` is now a redirect. Software Share bars now go to `index.html?software=X` (Early Leads picks up the filter). Property page "Back" goes to Early Leads. Caddyfile serves `/map.html` and `/vendor/*`. QA scripts (sweep, quick-check, panel_test) use map.html.
- Checked: check-panel.sh clean; check_map.py map/nav/redirect parts pass, the only 2 failures left are the P4 deep-dive buttons. Screenshot looked right.
- Open: Plano and Richardson dots overlap at national scale (Richardson's small dot sits on top of Plano's).
