## P1 Check script — done (2026-09-13)
- Added `tooling/qa/check_map.py` (serves site/ on 8791, Playwright, ~14 s).
- Contract for later tasks: dots are `[data-dot]`, the dot card is `#map-card` (needs ≥1 `<a>`), buttons are `[data-deep-dive]`; property test uses the first lead in leads.json with a `propertyId`.
- Ran it: fails as expected (4 problems: no map.html, no redirect, no buttons on 42 rows / property page). check-panel.sh still clean.

## P2 Map page — done (2026-09-13)
- Added `site/map.html` + `site/js/map.js`: US states outline (vendored us-atlas + d3-geo + topojson-client in `site/vendor/`, no CDN), Albers USA projection; green dots sized by `signs`, yellow diamond + "researching" for `kind: "scout"`; click → `#map-card` with city, count, proof links.
- `site/data/reach.json` seeded by `tooling/reach/seed_reach.py`: Plano (28) and Richardson (8) = 36 proven RealPage buildings, links = their proof URLs. P3 should keep dots with `source: "our-data"` (the seed script only replaces those).
- Nav: Master Table → Map; `master-table.html` is now a redirect. Software Share bars now go to `index.html?software=X` (Early Leads picks up the filter). Property page "Back" goes to Early Leads. Caddyfile serves `/map.html` and `/vendor/*`. QA scripts (sweep, quick-check, panel_test) use map.html.
- Checked: check-panel.sh clean; check_map.py map/nav/redirect parts pass, the only 2 failures left are the P4 deep-dive buttons. Screenshot looked right.
- Open: Plano and Richardson dots overlap at national scale (Richardson's small dot sits on top of Plano's).

## P3 Reach data — done (2026-09-13)
- Added `tooling/reach/build_reach.py`: Jina search over 32 US metros (2 queries each) + 4 general queries, plus RealPage's office-locations page (1 read). Keeps only results with a URL that mention RealPage and name the metro; skips social sites, Wikipedia, and RealPage's own market-report pages (`/analytics/`), which name cities but not customers. Geocodes from a built-in metro table. Search results cached in `tooling/reach/cache.json`, so reruns are free (`--fresh` to re-search).
- Spent 68 searches + 1 page read (under the ~100 budget). Needs `JINA_API_KEY` in env (the worktree has no .env; it's in the main repo's .env).
- `reach.json` now 19 dots: Plano 28 + Richardson 8 (our data, untouched) + 17 web dots (Dallas 6, Seattle/NY 3, Austin/San Antonio/Miami/SF/San Diego/DC 2, Houston/Atlanta/Nashville 1, offices in Irvine, Lombard, Boston, Reno, Woodway 1). Run logs in `propertystack/runs/*-build-reach.json`.
- Checked: check-panel.sh clean (one earlier run hit a one-off page-load timeout, rerun clean); check_map.py map parts pass, only the 2 P4 deep-dive failures remain.
- Open: 19 dots is just under the 20–60 aim. Many web "signs" are lawsuit/settlement news naming local landlords, not case studies — honest but mixed as proof of reach. Case-study search found almost no named-city customers.

## P4 Deep-dive button — done (2026-09-13)
- "✦ Deep dive" button (`[data-deep-dive]`) on all 42 Early Leads rows and on property.html. Click opens the chat panel with the prompt typed in, not sent. Row click is stopped from bubbling (stays on Early Leads). Upcoming leads (signalType "Upcoming", 14) get the "planned, software not chosen yet" prompt; others get "why would they switch now"; missing software shows "software unknown".
- How it gets in (checked in the running Open WebUI 0.11.3's JS): `postMessage input:prompt` only works same-origin, so it's used live; locally the panel loads `/?q=<text>&submit=false` (submit defaults to true, so the flag matters). Clipboard fallback not needed. Written up in chatbot/README.md. Code: `deepDive()` in site/js/chat-panel.js.
- Also fixed the flaky check-panel timeout: the fake chat server was single-threaded; now ThreadingHTTPServer (baseline flaked 1 in 5, now 5/5 clean).
- Commit be39285. Checked: check-panel.sh 5/5 clean, check_map.py 0 problems, Playwright click test showed the right prompt in the frame URL and no page change.
- Open: not yet tried against the real chat app on :3000 (that's P5).

## P5 Real click-through — done (2026-09-13)
- The shared chat stack on :3000 was left over from the v6 plan in sign-in mode (Google login), so the deep dive landed on a login page. No other session was running, so I restarted it with `bash tooling/dev.sh` from this checkout (no-sign-in dev mode). It is still running for Drew to try.
- Live result: Early Leads → Deep dive on Vantage At Spring Creek → the real Open WebUI input shows "Deep dive on Vantage At Spring Creek, Richardson (420 units, Yardi): why would they switch now, and get me ready to call." Not sent; page stayed on Early Leads; 0 console errors.
- Map: 19 dots, 60 card links. In a real browser all open (portal links redirect to their loftliving.com login pages, 200) except Miami Herald and Washington Post, which block automated browsers (likely fine for a person).
- Screenshots /tmp/p5-deepdive.png and /tmp/p5-map.png. Script saved as tooling/qa/live_deepdive_click.py. Check: check-panel.sh clean, check_map.py 0 problems.
- Open: at US scale the Plano/Richardson/Dallas dots bunch together, and the dot card can cover East Coast dots.
