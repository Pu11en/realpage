---
name: qa-site
description: Skill for QA-ing the PropertyStack site. Runs a headless-browser sweep over every page and interaction (desktop/tablet/phone), checks every property page and every link, optionally tests a 3-turn chat, and reports a deduplicated bug list with screenshots. Use before any version bump or after any site/data change.
---

# qa-site

One script, `tooling/qa/sweep.py`, does the whole sweep with Playwright headless Chromium.
No judgment calls during the sweep — judgment happens when triaging the bug list.

## Run

```bash
python3 tooling/qa/sweep.py http://localhost:8765            # site sweep only
python3 tooling/qa/sweep.py http://localhost:8765 --chat     # + 3-turn live chat test (small model cost)
```

Serve the site first (`python3 -m http.server 8765 -d site` or the usual dev server).
Add `--chat` only when chat prompt/config actually changed.

## What it covers

- All 4 pages at 3 widths (desktop 1440, tablet 820, phone 390): full-page screenshots,
  console/page errors, failed requests, HTTP >=400, horizontal scroll on phone,
  clipped or offscreen text, `NaN`/`undefined`/`null`/`[object Object]` in rendered text.
- Every `<select>` option, every visible checkbox, search box with hit/miss/empty,
  Export CSV (must have >=200 lines and no `undefined`/`NaN`), every sortable header,
  every visible non-chat button (must change the page somehow), first/middle/last rows
  (must navigate, never to a not-found page).
- Nav links from the sidebar at each width.
- 3 random + all property ids: each `property.html?id=...` must render a heading, never
  "property not found"; the Back link must leave the page.
- Every link found anywhere: must return 2xx-3xx (401/403/405/429 allowed on external sites).
- With `--chat`: 3 real turns (new question -> follow-up "which of those" -> follow-up
  "the biggest one") to test history carry-over; any error bubble is a bug.

## Output

- `--chat` answers print to stdout as `CHAT A1/A2/A3`.
- Bug list: `/tmp/qa/bugs.json` + printed summary `- [page @ width] what (steps: ...)`.
- Screenshots: `/tmp/qa/*.png` (`*-full.png` per page/width, plus each bug's shot).

## Triage rules

1. Fix site/data bugs (bad value, not-found page, dead link, broken button) in the
   pipeline or `site/` source, then rebuild and re-run the sweep. Never hand-edit `site/data/*.json`.
2. Screenshot-only issues (cosmetic overflow) still get fixed if they repro at any width.
3. External-site 403/429s are not bugs; a link that returns a soft-200 spam/hotel page IS —
   clear it in `2-websites.csv` and rebuild (see build-table skill).
4. Chat answers are spot-checked by a human-standard read: citation must exist in
   `site/data/properties.json` for that building. Two prompt fixes max per pass, in
   `chatbot/hermes-profile/SOUL.md`.
5. Re-run the sweep until bugs == 0 (or only pre-accepted externals remain), then commit.
