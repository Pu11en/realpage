## P1 Check script — done (2026-09-13)
- Added `tooling/qa/check_map.py` (serves site/ on 8791, Playwright, ~14 s).
- Contract for later tasks: dots are `[data-dot]`, the dot card is `#map-card` (needs ≥1 `<a>`), buttons are `[data-deep-dive]`; property test uses the first lead in leads.json with a `propertyId`.
- Ran it: fails as expected (4 problems: no map.html, no redirect, no buttons on 42 rows / property page). check-panel.sh still clean.
