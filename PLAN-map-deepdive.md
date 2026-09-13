# PropertyStack: US reach map + "Deep dive in chat" button

Written 2026-09-12 (sell-plan Q5, Q6, H1, H2). Two site changes, localhost only until Drew
says it's good; no push. Keep visuals minimal (site colours, green ✦); Drew designs later.
1. A **simple US map** replaces the Master Table page: dots = RealPage's **public reach**
   (offices, case studies, press-release customers, RealPage buildings we've proven), plus
   markers for areas the local scout is researching. Clicking a dot shows a small card: city,
   how many RealPage signs, proof links.
2. A **"Deep dive in chat"** button on every building page and on every Early Leads row: opens
   the chat panel with that building's prompt filled in; the person presses send.

Run with: `Do the next unticked task in PLAN-map-deepdive.md, then tick it and stop.`
Check: `bash tooling/qa/check-panel.sh && python3 tooling/qa/check_map.py`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765/map.html

## How to try it (30 seconds)
1. Click **Map** in the nav: a plain US map with dots; the Master Table tab is gone.
2. Click a dot: a small card with the city, a count and proof links that open.
3. On Early Leads, click **Deep dive** on a row: the chat opens with "Deep dive on <building>…"
   typed in; press send.

## Tasks

- [x] **P1 Check script.** `tooling/qa/check_map.py` (Playwright, free, serves `site/` itself on
  port 8791, under 60 s): map.html loads with 0 console errors and ≥1 dot; clicking the first dot
  shows a card with ≥1 link; nav has "Map" and no "Master Table"; `master-table.html` redirects
  to `map.html`; every Early Leads row has a `[data-deep-dive]` button; `property.html?id=<first
  lead>` has one too. Run it once to see it fail, commit.
- [ ] **P2 Map page.** `site/map.html` + `site/js/map.js`: US states outline from vendored
  files under `site/vendor/` (`us-atlas` states-albers-10m.json + `d3-geo`/`topojson-client`,
  no CDN), Albers USA projection. Reads `site/data/reach.json`
  (`[{city, state, lat, lon, signs, kind: "reach"|"scout", links: [{title, url}]}]`). Reach dots:
  size by `signs`; scout markers: different shape + "researching" label. Click → small card.
  Seed `reach.json` with Plano/Richardson from our data (36 RealPage buildings, proof = the
  `proof_url`s). Nav: replace Master Table with Map; `master-table.html` becomes a redirect.
  Fix any test that used master-table.html (check-panel, sweep) to use map.html or index.
- [ ] **P3 Reach data (💲 ~100 Jina searches).** `tooling/reach/build_reach.py`: web search for
  RealPage offices, case studies and press-release customers (named apartment companies +
  cities), keep only items with a source URL, geocode cities from a small built-in table of
  US metro lat/lon (no paid geocoder), merge into `reach.json`. Aim 20–60 dots across the US.
  Log to `propertystack/runs/`. Check passes.
- [ ] **P4 Deep-dive button.** `data-deep-dive` button on each Early Leads row and on
  property.html. Click opens the chat panel and puts this in the input, not sent:
  "Deep dive on <name>, <city> (<units> units, <software>): why would they switch now, and get
  me ready to call." Try Open WebUI's parent→iframe `postMessage` `{type: "input:prompt", text}`
  first; if the running version ignores it, reload the frame at `/?q=<text>` only if that does
  **not** auto-send; otherwise copy the text to the clipboard and show "Paste into the chat".
  Record which one works in `chatbot/README.md`. The row button must not also trigger the row's
  "open building page" click (stop the click from bubbling). **Upcoming projects** (14 of 42 leads,
  no building page, no website/software yet) still get the row button, with this prompt: "Deep
  dive on <name>, <city> (<units> units, planned, software not chosen yet): who is developing
  it, when does it open, and get me ready to call." Check passes.
- [ ] **P5 Real click-through.** Uses the shared local stack (ports 8765/3000/18080): if another
  plan's loop is using it (`docker ps` shows a rebuild in progress), wait. With `bash tooling/dev.sh` running, Playwright: Early Leads →
  Deep dive on Vantage At Spring Creek → prompt appears in the chat input; map dot card links
  return 200. Screenshot both to `/tmp/`. Then tell Drew in plain words it's ready to try.
