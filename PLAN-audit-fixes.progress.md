## A1 Phones — done (7f8a73b)
- Added the viewport tag to index, under-the-hood, property, ai-visibility (one line only) and the master-table redirect page, so every site/*.html has it.
- sweep.py and quick-check.py phone runs now use is_mobile=True, has_touch=True.
- Test: tooling/qa/fixes_tests/test_a1_viewport.py (tag on every page; QA scripts emulate phones).
- Checked: check-fixes.sh passes (2 tests, design check 0 problems); every page at 390px phone emulation has no sideways scroll (Under the Hood's wide table scrolls inside its own box).
- Note: port 8791 had a stale server serving old pages; use another port if checks look odd.

## A2 Early Leads stat boxes + Nothing found — done (46fde57)
- New leadStats(rows) in site/js/app.js; index.html renders the 4 number boxes from the rows currently shown (state, region, city, search, signal, software, hide-mine) on every filter change.
- "Opening soon" is now the count of shown, not-sold buildings opening in the next 12 months (same meaning the state builds already used).
- Empty result: one row "Nothing found. Clear the search or pick another region." with a Clear search button.
- Test: tooling/qa/fixes_tests/test_a2_stats_follow_filters.py (runs leadStats in node on the DFW rows).
- Checked: check-fixes.sh passes (5 tests, design 0 problems); in a browser Texas shows 628 leads, DFW 320 leads / 68,254 units, "zzzz" shows Nothing found, Clear search brings back 320 rows; no page errors.
