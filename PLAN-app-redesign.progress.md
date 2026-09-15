# Progress: PLAN-app-redesign

## T1 Fonts + shared colors + app frame — done 2026-09-15
- Self-hosted Inter + Plus Jakarta Sans (fontsource variable latin woff2) in `site/fonts/`.
- `site/css/styles.css`: @font-face for both, landing `:root` tokens (plus `--bad`, `--blue-soft`), old dark names kept as aliases; `--font` Inter, `--font-head` Plus Jakarta Sans on h1-h3/.wordmark; sidebar = paper-2, active tab blue on blue-soft with amber left marker; Ask button amber; score high/mid/low = ok/warn/muted red; sig tags + placeholder banner use soft badges.
- `site/js/app.js`: vendor pill greys readable on white.
- Check: `bash tooling/qa/check-design.sh` passes (quick check 0 problems; design list still empty). Both fonts confirmed loaded in the browser.
- index.html NOT added to design-pages.txt: its inline "New" pill still uses #22c55e — T2 fixes it. Screenshot: `docs/design-screens/T1-index.png`.
- Note: the landing page lives only in the main checkout (`business/` is not in this branch); T9 must handle that.

## T2 Early Leads page (index.html) — done 2026-09-15 (commit 3c9d6e9)
- All 4 inline style= colors on index.html moved to classes (.hide-mine, .pill-new = ok-soft green, .pill-unknown = grey, row cursor via tr.clickable). No #22c55e left.
- styles.css: leads table framed with --rule border, grey header, zebra --paper-2 rows, blue-soft hover, blue source links, Deep dive button blue outline; filters get blue focus ring; stat numbers in Plus Jakarta Sans; region/state chips hover blue. Phone card view (≤760px) keeps zebra per card.
- Primary amber action stays the Ask button (one amber per page); no copy or behaviour changes. No empty-state message added (would be new text).
- Added index.html to tooling/qa/design-pages.txt. Check passes (quick check 0 problems, design 1 page 0 problems); no sideways scroll at 390px.
- Screenshots: docs/design-screens/T2-desktop.png, T2-phone.png.

## T3 Property page (property.html) — done 2026-09-15 (commit c164c68)
- All 11 inline style= on property.html moved to classes (back link, deep-dive spacing, pill rows, stage labels, score row, why text, sources list, not-found link). Unknown software pill now uses .pill-unknown (was dark #27272a).
- Score badge colour via score-high/mid/low classes (new scoreClass() on the page) instead of inline background; breakdown boxes get paper-2 + rule border.
- Added property.html to tooling/qa/design-pages.txt. check-design.sh passes (0 problems, 2 design pages); no sideways scroll at 390px, no page errors (sold + upcoming examples).
- Note: check-local.sh on default port 8799 showed 404s because another session held that port; CHECK_PORT=8811 run passes clean.
- Screenshots: docs/design-screens/T3-desktop.png, T3-phone.png, T3-upcoming.png.
