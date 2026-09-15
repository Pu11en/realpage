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

## A3 Chat panel no longer hides Software and Why — done (7b801fc)
- With the chat docked on desktop (900px+), the Early Leads table turns into one card per lead (same layout as phones), so Software and Why are always visible; before, the table scrolled sideways inside its box and those two columns sat out of view.
- The Chat menu link no longer gets the selected look; while the panel is open it reads "Close chat". Only the current page's tab is selected.
- Test: tooling/qa/fixes_tests/test_a3_chat_panel_layout.py.
- Checked: check-fixes.sh passes (7 tests, design 0 problems); check-panel.sh clean; browser at 1000/1280/1440 wide with panel open: no sideways scroll, only "Early Leads" selected.

## A4 Every building opens a detail page — done (a5d938d)
- Every Early Leads row is now clickable: rows with no propertyId link to property.html?id=<lead id>&area=<state>.
- property.html: if the id isn't in properties.json, new findLead/pickLead (site/js/app.js) looks it up in the state files (asked state first) and shows name, address, city, state, units, developer/buyer, stage, signal, dates, software, score + why, phone, sources (plain labels for non-link sources) and the Deep dive button.
- Test: tooling/qa/fixes_tests/test_a4_every_lead_opens.py (all built lead ids resolve, via node).
- Checked: check-fixes.sh passes (10 tests, design 0 problems); browser: tx-1, az-1, ny-1, a Plano property and a click from the Arizona list all open, "zzz" still says not found, Deep dive opens chat, no page errors.
- Left for later tasks: Deep dive still calls non-sold rows "planned" (A5); raw ArcGIS source URLs shown as-is (C4); NY units 0 shows "units not stated" here.

## A5 Deep dive says the real stage — done (11b4f02)
- deepDivePrompt in site/js/chat-panel.js now takes the lead's stage/signalType and says it in plain words: "permit filed", "planned", "under construction", "leasing now" (asks who is leasing it / how full), or "recently sold". Plano property stages (zoning-filed, under-construction, ...) map too.
- Early Leads and the detail page pass stage + signalType instead of a guessed "upcoming" flag (before, TX "Planned"/"Leasing" rows got the existing-building prompt and every other upcoming row was called "planned").
- Test: tooling/qa/fixes_tests/test_a5_deep_dive_stage.py (fails on the old code).
- Checked: check-fixes.sh passes (12 tests, design 0 problems).
