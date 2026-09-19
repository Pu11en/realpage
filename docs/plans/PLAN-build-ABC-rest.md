# Build ABC (rest): agent-first Early Leads, area box, Lead Pack (Software Sellers edition, 2026-09-19)

One build, run in order (the bot runs one build per project; starting another stops this one).
Picks up where Build A stopped (G1-T1..T3 done: contact-first prompt, chat rules, "Get contact →" button).
Decisions and details: PLAN-gap1-who-to-call.md, PLAN-agent-first-leads.md, PLAN-gap3-freshness.md,
PLAN-build-B-area-box.md, PLAN-build-C-lead-pack.md. Do not touch business/ (separate repo; already done by hand:
landing wording, Start free -> index.html, POST /api/signup source=area-request with area + optional email,
CORS for app.cranesignal.com and localhost:8765). No real AI calls.

Check: python3 -m pytest -q tooling/qa/fixes_tests/
Try: bash tooling/dev.sh
Open: http://localhost:8765/index.html

## Tasks
- [ ] AF-T1 Top of the filter area on Early Leads: a wide search bar, placeholder "Describe the leads you want…". Enter sends the text to the agent panel (opens it, sends automatically; signed-out visitors see "Make a free account" first and the question sends after sign-up). Reuse the Get-contact send path from PLAN-gap1 T3.
- [ ] AF-T2 Under the bar, 3 example chips built from the current state/region (e.g. "Dallas buildings opening in 2027", "Recently sold, 200+ units", "Not on any software yet near Austin"); a click sends that chip to the agent.
- [ ] AF-T3 Fold the existing dropdowns (signal, city, software, sort, "hide properties already on my software") and the plain "Search property" box under a small "Filters" toggle button, closed by default; state and region pills stay visible. Filtering must still work exactly as before when opened.
- [ ] AF-T4 Phone width (<900px): bar, chips and Filters button stack cleanly; screenshot desktop + phone for Drew. Tests for T1-T3.
- [ ] G3-T1 Early Leads: remove the "NEW" stat card (and the "New" badge on rows if it depends on newThisWeek). Keep Leads, Units in play, Opening soon.
- [ ] G3-T2 "Last updated" in the sidebar shows the date the lead data was built (from the area JSON / build time of site/data/areas/*.json), not the site deploy date. Today it wrongly shows Sep 18 while the data is from Sep 15.
- [ ] G3-T3 Under the stats on Early Leads: one line "Data from <date>. Don't see your area? Ask for it" linking to map.html#request-area (Gap 2).
- [ ] G3-T4 Tests for all three; screenshot Early Leads for Drew.
- [ ] B-T3 (this repo) Map page: small "Don't see your area?" box under the map (id request-area): one text field "City or county, state", optional email, button "Ask for it". Sends to the landing server (cranesignal.com/api/signup locally → http://localhost:8791). Shows "Got it — we'll add it" on success. Test that the box renders and posts the right fields.
- [ ] B-T4 Local end-to-end: submit "Tulsa, OK" on the local map; the row appears in the local signups CSV. (Discord post only fires where SIGNUP_WEBHOOK_URL is set — verify on live after Drew's OK.)
- [ ] C-T1 Data: when the area JSON is built (site/data/build_data.py), give every lead a stable "firstSeen" date: keep the date from the previous build for existing ids, stamp today for new ids. Existing leads get the current data date (2026-09-15). Test.
- [ ] C-T2 Vendor jsPDF + jspdf-autotable (pinned versions, license files) into site/vendor/. Early Leads gets a "Download Lead Pack (PDF)" button next to the state/region pills. It builds a PDF of ALL leads in the chosen state/region: title "CraneSignal Lead Pack: <region>, <date>", then a table (building, city, units, stage/signal, opens or sold date, owner/developer/buyer, phone if known, why now) and a source link per row; footer "Find who to call for any building at app.cranesignal.com". Letter size, readable on a phone. File name cranesignal-lead-pack-<region>-<date>.pdf.
- [ ] C-T3 "Get new leads" button: remembers (localStorage, per state/region) the date of the visitor's last Lead Pack download; downloads a PDF of only leads with firstSeen after that date. If there are none, it says "No new leads since <date>. Ask for your area on the Map." Hidden until the visitor has downloaded once.
- [ ] C-T4 Cross-device check with Playwright: desktop Chromium, Firefox and WebKit, plus iPhone 13 and Pixel 7 device emulation; each download completes and is a valid PDF with the right row count. Save one sample PDF to docs/plans/sample-lead-pack.pdf and screenshots for Drew.

## How to try it
1. Early Leads: "Get contact →" next to each name; a big "Describe the leads you want…" bar with chips; dropdowns under "Filters"; no "New" box.
2. Map: "Don't see your area?" box says "Got it" after asking.
3. "Download Lead Pack" asks for a free account, then downloads a PDF of every lead in the area.
