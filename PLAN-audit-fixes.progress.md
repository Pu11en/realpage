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

## A6 Menu footer honest — done (4118523)
- build_data.py now writes "updated" (the build day) into site/data/areas/index.json; the menu footer reads it and shows "Last updated: Sep 15, 2026" (rebuilt data committed; only index.json changed).
- "View as" dropdown has a plain "View as" label and tooltip "Highlight the buildings a Yardi / Entrata / AppFolio seller would win"; "Neutral" is now "Everyone" (an old saved "Neutral" choice reads as Everyone; index.html hide-mine filter updated).
- Test: tooling/qa/fixes_tests/test_a6_menu_footer.py.
- Checked: check-fixes.sh passes (16 tests, design 0 problems); browser on index/map/property/under-the-hood shows the date and label, no page errors.
- Note: the date changes whenever build_data.py is rerun (that is the point).

## A7 Under the Hood cleaned for users — done (92ed756)
- Removed "area: plano-richardson" and the "propertystack/runs/*.json" tag; the intro now says the step detail comes from the Plano and Richardson sample and the site has 909 leads across Texas, Arizona, New York (read live from areas/index.json).
- Run history only lists successful runs (the one build-reach error row and the status-less client-map row are hidden); no "(N errors)" text.
- The "Cost per area" card with the PLACEHOLDER box is gone.
- The last pipeline step now shows "909 leads on the site" (site total) instead of the Plano-only "49 ranked leads".
- Test: tooling/qa/fixes_tests/test_a7_under_the_hood.py.
- Checked: check-fixes.sh passes (19 tests, design 0 problems); browser shows 909, no PLACEHOLDER/error/plano-richardson, no page errors.
- Left: pipeline.json still carries costPerArea and error runs (page just hides them); skill names like find-apartments still show under each step.

## A8 Privacy page — done (a73ee37; landing repo 9b5b29f)
- site/privacy.html: sign-in section now covers Google sign-in and email sign-up (name, email, hashed password), early-access sign-up emails, chats; new Contact section; old "support email on the Google sign-in screen" line removed. Date bumped to Sep 15, 2026.
- App menu footer (site/js/app.js renderShell) has a "Privacy" link under Last updated.
- Landing footer (business/marketing/landing/index.html, its own repo) links to https://app.cranesignal.com/privacy.html; committed there (9b5b29f).
- ⚠️ No contact email exists on the landing page, so the page says CONTACT_EMAIL_TBD: Drew must pick one (for D1 report).
- Test: tooling/qa/fixes_tests/test_a8_privacy.py. Checked: check-fixes.sh passes (21 tests, design 0 problems).

## A9 Map labels easier to read — done (e6277c2)
- Each state label ("TX · 628 leads") now sits in a small white pill with navy text and a soft shadow, above its amber dot, so it no longer sits on dark blue.
- site/js/map.js layoutLabels() sizes label text (~12px on screen) and the dot to the drawn map width and refits the pill on resize, so on a phone the labels stay readable (before they shrank to ~5px) and dots are easier to tap.
- Test: tooling/qa/fixes_tests/test_a9_map_labels.py.
- Checked: check-fixes.sh passes (23 tests, design 0 problems); browser at 1280 wide and phone 390 wide (mobile/touch): pills readable, no sideways scroll, no page errors.

## B1 No more "PropertyStack" in chat sources — done (dff4f4c)
- Chat Sources now say "CraneSignal lead ranking" (plugin SOURCE_NAMES and the query-propertystack SKILL.md table); tool descriptions and the skill description say CraneSignal. Internal names (plugin/skill/toolset ids, hermes-agent) unchanged.
- proxy.py: no user-facing message had the old names; only its top docstring changed. SOUL.md only mentions the names in its "never say" rule, left as is.
- Sign-in popup: Open WebUI adds " (Open WebUI)" to WEBUI_NAME itself. webui.Dockerfile (Railway) patches that line out (checked against the real image: env.py line becomes pass); branding/loader.js also strips it from the page title and text, covering the local compose.
- ⚠️ For D1 report: the Open WebUI license only allows removing its name while we have 50 or fewer users in any 30 days; beyond that, restore it or buy their enterprise license. Takes effect live only after the chat app is redeployed (Drew).
- Test: tooling/qa/fixes_tests/test_b1_chat_names.py. Checked: check-fixes.sh passes (28 tests, design 0 problems); chatbot/tests 35 passed.
