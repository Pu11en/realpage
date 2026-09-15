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

## T4 Map page (map.html) — done 2026-09-15 (commit 8462ce5)
- States: land --paper-2 with --rule borders; states with RealPage buildings shaded in a blue ramp (was green); legend ramp matches.
- Lead markers amber with navy outline (the "hot" states), labels navy with white halo in Plus Jakarta Sans, hover brighter amber, keyboard focus ring blue. Tooltip = white card, navy text, soft shadow; lead count in --warn.
- Page intro colour words updated to match ("Darker blue", "Amber markers") — only the colour names changed.
- Added map.html to design-pages.txt. check-design.sh passes (3 pages, 0 problems); no sideways scroll at 390px, no page errors, tooltip shows on hover.
- Left open: tooling/qa/check_map.py can't start — it waits for the text "PropertyStack" on index.html, which the site no longer shows (stale test, not caused by this task).
- Screenshots: docs/design-screens/T4-desktop.png, T4-phone.png.

## T5 AI Visibility page (ai-visibility.html) — done 2026-09-15 (commit 0ba2fe0)
- All inline colours moved to classes: trend lines/points/legend dots use series classes (Gemini dark blue, Gemini+web light blue, Claude dark amber, Claude+web light amber, ChatGPT grey; spare blue/brown/grey for unknown AIs). Old #22c55e gone.
- Chart grid lines --rule; bar tracks and tone bar = paper-2 with rule border; plain bars grey, RealPage bar blue; tone bar harsh = muted red, neutral = grey, settled = amber; tone key words as classes; quote rule blue-soft.
- Font-size/margin inline styles moved to small note classes. Only data-driven bar widths stay inline.
- Added ai-visibility.html to design-pages.txt. check-design.sh passes (4 pages, 0 problems); no sideways scroll at 390px, no page errors.
- Screenshots: docs/design-screens/T5-desktop.png, T5-phone.png.

## T6 Under the Hood, Privacy, Master Table — done 2026-09-15 (commit c609f91)
- under-the-hood.html: all 5 inline style= moved to classes (review-links, review-note, cost-label/value, clickable row cursor). Dark #27272a tag now grey paper-2 badge with rule border; pipeline step boxes paper-2, numbers in Plus Jakarta Sans; run-history/review tables framed, zebra rows, sticky grey headers; status "ok" = green --ok, "error" = muted red --bad.
- privacy.html: already light via styles.css; headings set to navy ink, h1 bolder. No text changes.
- master-table.html is only a redirect to map.html (no styling of its own); listed so the check covers the redirect landing.
- Added all three to design-pages.txt. check-design.sh passes (7 pages, 0 problems); no sideways scroll at 390px, no page errors.
- Left open: Under the Hood shows the text "propertystack/runs/*.json" (existing copy; plan forbids copy rewrites) — Drew may want it renamed later.
- Screenshots: docs/design-screens/T6-under-the-hood-{desktop,phone}.png, T6-privacy-{desktop,phone}.png.

## T7 Chat panel inside the app — done 2026-09-15 (commit 18c163d)
- chat-panel.css: header is a blueprint-blue band with white Plus Jakarta Sans title and amber underline; close button light blue, hover darker blue. Panel body white, soft shadow only while open.
- "Try again" and "Sign in free" buttons now amber with navy text (same as the Ask button); sign-in card light grey with navy heading. Old dark #0b1410 and green-on-dark text gone.
- Open button (.ask-fab) was already amber from T1; phone view stays full-width (390px checked).
- Message bubbles and the input live inside the chat app (iframe) — those are T8's job, not changed here. No JS changes.
- check-design.sh passes (quick check 0 problems, 7 design pages 0 problems); panel opens with no page errors on desktop and phone.
- Screenshots: docs/design-screens/T7-chat-desktop.png, T7-chat-phone.png (sign-in card shown, since the chat app isn't running locally).
