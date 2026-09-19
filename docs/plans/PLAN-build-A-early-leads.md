# Build A: Early Leads agent-first (Software Sellers edition, 2026-09-18)
Goal: On Early Leads, every building has a "Get contact →" button that asks the agent who to call (company, phone, website and role, each with a source), a "Describe the leads you want…" bar with example chips sits above a folded "Filters" toggle, and the page shows the real data date with no fake "NEW" count, all finished and pushed live.
Done when: `python3 -m pytest -q tooling/qa/fixes_tests/` passes, and in 30 seconds on http://localhost:8765/index.html you can see "Get contact →" on the building rows, the search bar with chips, and no "NEW" card.

Combined from PLAN-gap1-who-to-call.md, PLAN-agent-first-leads.md, PLAN-gap3-freshness.md (read them for the decisions).
These all touch site/js/chat-panel.js, site/js/app.js and site/index.html, so they run in order in ONE build.
Do NOT touch business/ (separate repo, handled elsewhere) or site/map.html (Build B).
No real AI calls in this build.

Check: python3 -m pytest -q tooling/qa/fixes_tests/
Try: bash tooling/dev.sh
Open: http://localhost:8765/index.html

## Tasks
- [x] G1-T1 Deep dive prompt (site/js/chat-panel.js deepDivePrompt): ask first for "Who to call: management company, office phone, website, and the role to ask for (with a source link for each)", then why now. Both upcoming and sold variants. For recently sold buildings with no buyer (the 24 Texas sales), also ask "who bought it (new owner)" — Gap 4, decided by Drew. Update/add a test.
- [x] G1-T2 Chat rules (chatbot/hermes-profile/SOUL.md + skills/query-propertystack): for a deep dive, start the answer with a short "Who to call" block; use the building's own data first (officePhone, website, developer), then web search (max ~6 searches); every phone/website must have a source link; if not found, say "not found" and never guess a number. For a recent sale, include "New owner" (from our data, else county/news search, with source).
- [ ] G1-T3 Button (Drew 2026-09-18): on every Early Leads row and building page, the "Deep dive" button becomes "Get contact →", placed on the LEFT right next to/under the building name (where Deep dive sits now) so it never gets cut off on narrow screens. Clicking it opens the agent panel and SENDS the question automatically. If signed out: show "Make a free account" first; after sign-up the waiting question sends by itself. Update tests that look for the old label.
- [ ] AF-T1 Top of the filter area on Early Leads: a wide search bar, placeholder "Describe the leads you want…". Enter sends the text to the agent panel (opens it, sends automatically; signed-out visitors see "Make a free account" first and the question sends after sign-up). Reuse the Get-contact send path from PLAN-gap1 T3.
- [ ] AF-T2 Under the bar, 3 example chips built from the current state/region (e.g. "Dallas buildings opening in 2027", "Recently sold, 200+ units", "Not on any software yet near Austin"); a click sends that chip to the agent.
- [ ] AF-T3 Fold the existing dropdowns (signal, city, software, sort, "hide properties already on my software") and the plain "Search property" box under a small "Filters" toggle button, closed by default; state and region pills stay visible. Filtering must still work exactly as before when opened.
- [ ] AF-T4 Phone width (<900px): bar, chips and Filters button stack cleanly; screenshot desktop + phone for Drew. Tests for T1-T3.
- [ ] G3-T1 Early Leads: remove the "NEW" stat card (and the "New" badge on rows if it depends on newThisWeek). Keep Leads, Units in play, Opening soon.
- [ ] G3-T2 "Last updated" in the sidebar shows the date the lead data was built (from the area JSON / build time of site/data/areas/*.json), not the site deploy date. Today it wrongly shows Sep 18 while the data is from Sep 15.
- [ ] G3-T3 Under the stats on Early Leads: one line "Data from <date>. Don't see your area? Ask for it" linking to map.html#request-area (Gap 2).
- [ ] G3-T4 Tests for all three; screenshot Early Leads for Drew.

## How to try it
1. Early Leads: each building has "Get contact →" on the left next to its name; clicking opens the agent and sends the question.
2. A big "Describe the leads you want…" bar with example chips sits on top; the dropdowns are under "Filters".
3. No "New" box; the date shown is when the data was gathered.
