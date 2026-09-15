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

## T8 The chat app itself — done 2026-09-15 (commit bcf74c3)
- custom.css: self-hosted Inter (body) + Plus Jakarta Sans (headings) from /static/fonts/; white paper, navy ink, blue links, grey table rules; message box white with thin rule and blue focus ring; send button amber with navy arrow; sign-in submit button blue; "Past chats"/"Back to chat" pills blue instead of green (dark mode uses light blue). Blue focus ring everywhere.
- loader.js: sets light theme once per browser (remembered via cs-light-default), so later theme choices in Open WebUI settings are kept. Redirect guard unchanged.
- Fonts copied to chatbot/branding/fonts/; added to webui.Dockerfile (COPY) and docker-compose.local.yml (mount). No model/prompt/proxy changes.
- Checked: the chat app was already running on :3000 (another session's), so I didn't restart it; screenshots load it framed with this branch's custom.css/loader.js/fonts swapped in. Browser set to prefer dark still shows light, Inter loaded, no page errors. check-design.sh passes (7 pages, 0 problems); chatbot tests 35 passed.
- Left open: locally loader.js isn't mounted in compose (standalone pages would redirect-loop to "/"), so the light default applies on Railway builds; locally the running chat needs a restart of dev.sh to pick up the new CSS/font mounts.
- Screenshots: docs/design-screens/T8-chat-desktop.png, T8-chat-phone.png.

## T9 Landing page fonts + Street Talk — done 2026-09-15 (commit f9414fa)
- Landing page (business/marketing/landing/index.html in the main realpage folder): Archivo replaced by self-hosted Plus Jakarta Sans (headings, buttons, labels, logo) and Inter (body). Both woff2 files copied into its fonts/ folder and preloaded. Every font-stretch trick removed (0 left); heading sizes and weights unchanged; heading letter-spacing loosened a little (-.035em/-.03em → -.022em/-.018em) because the new face is narrower and words were crowding.
- Note: that landing folder is not tracked by git (business/ is in .git/info/exclude), so the landing edit itself can't be committed — it is saved in place; a copy of the old file is at /tmp/landing-index-before-T9.html. Old archivo/manrope font files left in place (not deleted).
- Street Talk: site/street-talk.html does not exist on this branch, so nothing to restyle.
- Checked: both fonts load, no page errors, no sideways scroll at 1440px and 390px; check-design.sh passes (7 pages, 0 problems).
- Screenshots: docs/design-screens/T9-landing-desktop.png, T9-landing-phone.png.
