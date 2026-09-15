# CraneSignal: make the app look like the landing page

Written 2026-09-15 with Drew. **Starts only when Drew says "go work".** Localhost only, never push or deploy.

Drew's answers:
- The app (every page under `site/` plus the chat) gets the **same look as the landing page**
  (`business/marketing/landing/index.html`): white "paper" background, dark navy ink text, blueprint
  blue `#1a3d8f` as the main color, amber `#f5b700` for the one primary button / highlight, thin grey
  rules `#d9dce3`, green/amber soft badges (`--ok`, `--warn`). Copy the exact token names and values
  from the landing page's `:root`.
- **Fonts: headings = Plus Jakarta Sans, body/sub text = Inter.** This replaces Archivo on the landing
  page too, so both match. Self-host both as woff2 files (no Google Fonts link at runtime), like the
  landing page does with `/fonts/archivo-latin.woff2`. Variable-weight latin files, `font-display:swap`.
- Only the look changes: same pages, same data, same buttons, same text, same behaviour. No new
  features, no copy rewrites. If a page breaks, fix the break, don't redesign the page.
- Follow the `landing-page-design` and `redesign-existing-projects` skills for spacing, radius and
  states, but never add gradients-for-decoration, glows or new sections.
- User-facing name is **CraneSignal**; never show "PropertyStack" or "Hermes" to users.

Another build (Street Talk, a new `street-talk.html` tab) may merge into `local-test` while this runs.
Don't merge other branches mid-build; T9 restyles Street Talk only if it is already here.

How the check grows: every task that restyles a page adds that page's file name to
`tooling/qa/design-pages.txt`. The check then requires, for each listed page: Inter body text, Plus
Jakarta Sans headings, both font files actually loaded, a light background, and no old green `#22c55e`.
Never remove a page from that list to make the check pass.

AI for the build: same as the planning session (`"harness": "same"`).

Run with: `Do the next unticked task in PLAN-app-redesign.md, then tick it and stop.`
Check: `bash tooling/qa/check-design.sh`
Try: `python3 -m http.server 8765 -d site` (or `bash tooling/dev.sh` for the site plus the chat)
Open: http://localhost:8765/index.html

## How to try it (30 seconds)
1. Open the landing page and the app side by side: same white background, navy text, blue and amber.
2. Headings in the app look like the landing page headings (Plus Jakarta Sans); normal text is Inter.
3. Click every tab in the left menu and the chat button: nothing is dark, broken or unreadable, on a phone too.

## Tasks

- [x] **T1 Fonts + shared colors + app frame.** Download Plus Jakarta Sans and Inter (latin, variable
  weight woff2, from the official fontsource / Google Fonts files) into `site/fonts/`. In
  `site/css/styles.css`: `@font-face` for both, replace the dark `:root` with the landing tokens
  (keep old variable names as aliases pointing at the new values so pages don't break), `--font-head`
  = Plus Jakarta Sans, `--font` = Inter; `h1,h2,h3,.wordmark` use `--font-head`. Restyle the shared
  frame drawn by `site/js/app.js` `renderShell` (left menu, logo/wordmark, active tab = blue with
  amber marker, page header). Score colors: high = `--ok`, mid = `--warn`, low = a muted red that
  reads on white. Add `index.html` to `tooling/qa/design-pages.txt` only if it now passes; otherwise
  leave it for T2. Save a desktop screenshot of index.html to `docs/design-screens/T1-index.png`.
- [x] **T2 Early Leads page (`index.html`).** Table, State/Region/city filter rows, chips, search,
  counts, empty/loading states, inline `style=` colors in the page. Rows readable on white (zebra
  `--paper-2`, `--rule` borders), links in blue, primary action amber. Add `index.html` to the list.
  Screenshot desktop + phone to `docs/design-screens/T2-*.png`.
- [x] **T3 Property page (`property.html`).** Header card, facts, score, source links, all 11 inline
  `style=` colors moved to classes in styles.css. Add `property.html`. Screenshots.
- [x] **T4 Map page (`map.html`, `site/js/map.js`).** Light map: land `--paper-2`, borders `--rule`,
  markers blue with amber for the selected/hot one, tooltip = white card with navy text. Add
  `map.html`. Screenshots.
- [x] **T5 AI Visibility page (`ai-visibility.html`).** Cards, bars/charts and the 13 inline colors
  (follow the `dataviz` skill: blue/amber/grey series that read on white). Add `ai-visibility.html`.
  Screenshots.
- [x] **T6 The rest: `under-the-hood.html`, `privacy.html`, `master-table.html`.** Add all three.
  Screenshots.
- [x] **T7 Chat panel inside the app (`site/css/chat-panel.css`, `site/js/chat-panel.js`).** Panel,
  open button (amber), header (navy/blue), message bubbles, input, close button, phone full-screen
  view. The panel must match the pages; the check's quick-check (panel opens, no errors) must pass.
  Screenshot the panel open on desktop and phone.
- [x] **T8 The chat app itself (`chatbot/branding/custom.css`, `chatbot/branding/loader.js`).** Same
  fonts (self-hosted copies served next to custom.css) and colors for the standalone chat, light
  mode as the default. CSS/branding only: do not touch the model, prompts or proxy. If
  `bash tooling/dev.sh` can run, screenshot http://localhost:3000; if it can't (no key), note that
  Drew must look at it himself and move on.
- [ ] **T9 Landing page fonts + Street Talk.** Landing (`business/marketing/landing/index.html`):
  swap Archivo for Plus Jakarta Sans headings / Inter body (copy the woff2 files into its `fonts/`,
  drop the `font-stretch` tricks that only worked with Archivo, keep the headline just as big and
  bold), and check its phone layout still fits. If `site/street-talk.html` exists, restyle it and add
  it to the list. Screenshots of landing desktop + phone.
- [ ] **T10 Final pass.** Run `python3 tooling/qa/sweep.py` if it runs locally, fix anything it finds
  in the new look (contrast, focus rings, hover states, phone overflow). Take one desktop screenshot
  of every page plus the landing page into `docs/design-screens/final/`. Write
  `docs/design-screens/REPORT.md` in plain words: what changed per page, anything that still looks
  off, and anything Drew must check himself (the chat app if it couldn't run).
