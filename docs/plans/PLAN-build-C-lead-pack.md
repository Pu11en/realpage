# Build C: Lead Pack download (Software Sellers edition, 2026-09-19)

Decision (Drew): the deliverable is a Lead Pack anyone can download, covering ALL current leads for the
area they picked. Later, after Drew adds leads in a new lead session, a "Get new leads" button downloads
only the leads they haven't downloaded yet. Must work on every browser, computer, iPhone and Android.
Use a proven library, no custom PDF code: jsPDF + jspdf-autotable (github.com/parallax/jsPDF, MIT, 31k stars),
vendored into site/vendor/ (no CDN), generated in the browser from the same lead data the page shows.

Run AFTER Build A (same files: site/index.html, site/js/app.js). Do not touch business/.
No AI calls.

Check: python3 -m pytest -q tooling/qa/fixes_tests/
Try: bash tooling/dev.sh
Open: http://localhost:8765/index.html

## Tasks
- [ ] T1 Data: when the area JSON is built (site/data/build_data.py), give every lead a stable "firstSeen" date: keep the date from the previous build for existing ids, stamp today for new ids. Existing leads get the current data date (2026-09-15). Test.
- [ ] T2 Vendor jsPDF + jspdf-autotable (pinned versions, license files) into site/vendor/. Early Leads gets a "Download Lead Pack (PDF)" button next to the state/region pills. It builds a PDF of ALL leads in the chosen state/region: title "CraneSignal Lead Pack: <region>, <date>", then a table (building, city, units, stage/signal, opens or sold date, owner/developer/buyer, phone if known, why now) and a source link per row; footer "Find who to call for any building at app.cranesignal.com". Letter size, readable on a phone. File name cranesignal-lead-pack-<region>-<date>.pdf.
- [ ] T3 "Get new leads" button: remembers (localStorage, per state/region) the date of the visitor's last Lead Pack download; downloads a PDF of only leads with firstSeen after that date. If there are none, it says "No new leads since <date>. Ask for your area on the Map." Hidden until the visitor has downloaded once.
- [ ] T4 Cross-device check with Playwright: desktop Chromium, Firefox and WebKit, plus iPhone 13 and Pixel 7 device emulation; each download completes and is a valid PDF with the right row count. Save one sample PDF to docs/plans/sample-lead-pack.pdf and screenshots for Drew.

## How to try it
1. On Early Leads pick Texas → Dallas–Fort Worth, click "Download Lead Pack": a PDF of all Dallas leads downloads.
2. Open it on your phone: readable table, every row has a source link.
3. Click "Get new leads": it says there are none yet (until new leads are added).
