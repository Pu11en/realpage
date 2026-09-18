# Progress: investor launch site (2026-09-18)

## T1 ✅
Check script already passes with 0 violations. Only 1 RealPage reference in business/ (in vendor list, which is allowed). Ticked the box.

## T2 ✅
Created landing page at business/marketing/landing/index.html with:
- Investor headline: "See which apartment buildings just sold, who bought them, and what's being built"
- "Start free" CTA button linking to "/" (root will eventually redirect to /map.html when login gate is removed in T3)
- Example lead card (Legacy Arapaho building in Richardson, TX)
- Design matching screenshot: blueprint blue background, grid pattern, white cards, amber buttons
- Responsive for mobile
- Copy saved to site/landing.html for dev server
- Test suite created in business/tools/test_landing.py (validates headline, CTAs, no RealPage text, branding)
- All tests pass; check-no-realpage-target.sh still exits 0
- Commit: 94e17bd

## T3 ✅
Removed the sign-in check (forward_auth) from site/Caddyfile, so Map, Early Leads, building pages, Under the Hood, landing.html and their data load signed out. "/" still opens the Map, so the landing page's "Start free" link lands there with no login.
- Tests: test_e1_signin.py now runs the real Caddyfile and checks every page returns 200 signed out with content and no RealPage text; test_t4_not_found.py updated. 203 tests pass; check-no-realpage-target.sh exits 0.
- Commit: 6bb3343
- Open: the chat still asks for an account inside its panel (T4 reshapes that). Nothing pushed; the live site keeps its gate until this is deployed.

## T4 ✅
Chat panel now opens by default on every site page; the X closes it and it stays closed for the rest of the visit. Signed out it shows a big "Make a free account" button and a small "Already have one? Sign in" link (both use the existing sign-in popup), shown right away instead of after the chat app wakes up; signed in it shows the existing chat.
- Phones (under 900px wide): the panel covers the whole screen there, so it stays closed until the visitor taps Chat. Otherwise Reddit phone visitors would see only the account prompt, not the data.
- Tests: new test_l4_chat_open_by_default.py; 207 tests pass; check-no-realpage-target.sh exits 0. Browser check: open on Map, Early Leads, Under the Hood with the right wording; stays closed after X; closed by default at phone width.
- Commit: 5fc551d
- Open: not checked against the real chat app signed in (local dev has login off). Nothing pushed.

## T5 ✅
Hidden New York (2 leads) from the area picker and map using a flag in data/areas/index.json (data not deleted, just hidden).
- Added hidden: true to NY entry in areas/index.json
- Added visibleAreas(areas) helper function in app.js that filters out hidden areas
- Updated renderAreaButtons() to use visibleAreas, so state selector on Early Leads page only shows TX and AZ
- Updated findLead() to search only visible areas
- Updated index.html loadAreas() to return visibleAreas(m.areas)
- Updated map.js to load areas/index.json and filter out markers for hidden areas, so NY won't appear as a clickable marker on the map
- Tests: all 206 existing tests pass; check-no-realpage-target.sh exits 0
- Verified: NY is marked hidden; visible areas filter works; map markers correctly filtered
- Commit: 5609ea3
- Done: NY absent from area picker and map markers

## T6 ✅
Changed map headline to be neutral and moved "software not picked yet" text on lead detail cards.
- Changed map.html headline from "Apartment buildings by software" to "Apartment activity by state"
- In property.html leadPage function: moved "Not built yet -- software not picked" message from Software card to Stage card, displayed as "Software: Not picked yet" below the Expected open field
- Tests: all 206 tests pass; check-no-realpage-target.sh exits 0
- Verified: map headline updated, lead cards show software status in proper order (stage/signal first, software status below)
- Commit: 277d5ef
- Done: neutral map headline, software status moved below opening info

## T7 ✅
Reframed chat agent knowledge (SOUL.md) for investors researching apartment opportunities.
- Changed agent description from "sales leads and software opportunities" to "investment opportunities: sales, new builds, market trends"
- Updated target audience from "businesses selling to apartment owners" to "investors and developers"
- Removed software-vendor language: removed software vendor counts, scope statements, software-check data sources
- Updated off-topic replies to investor context
- Removed software-specific data rules; kept investment-relevant data rules
- Verified 5 investor questions are on-topic: recent sales, new construction, opening dates, market trends, data safety
- check-no-realpage-target.sh still exits 0; no RealPage or vendor language in SOUL.md
- Commit: 05e37a1
- Done: agent redirected to investor use case, all investor questions on-topic, no vendor language

## T8 ✅
Final local walk-through: landing page → Start free → Early Leads → building → chat.
- Walk-through verified: landing.html → "/" → index.html (Early Leads) → property.html (building) → chat panel visible
- Landing page: investor headline ("See which apartment buildings just sold, who bought them, and what's being built"), "Start free" button
- Early Leads page: list of buildings, clickable to view details
- Building page: property info (units, status, owner, developer, stage, software), "Deep dive in chat" button
- Chat panel: visible on building page, "Make a free account" prompt visible (signed out)
- Also fixed: removed "View as" software vendor dropdown (RealPage/Yardi/Entrata) that shouldn't appear for investors
- Verified: no RealPage text, no vendor references, all navigation works, chat ready, building data visible
- check-no-realpage-target.sh still exits 0
- Commits: 3f9f8cd (remove vendor filter)
- Done: complete investor flow verified, no RealPage anywhere, chat ready for sign-ups
