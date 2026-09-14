# Progress log: lead-finder-fix

## F1 Remove SearXNG; Jina + Brave search -- done
- Deleted `tooling/searx_search.py` and `tooling/searxng/` (docker-compose, settings, cache).
- `fetch.py`'s `WebHelper.search()` now tries Jina first, then Brave Search API only when Jina
  errors or returns nothing relevant (same junk-detection check as before, renamed to
  `junk_jina`). Jina and Brave calls are counted separately (`SearchCounts.jina/.brave`).
- Added `BraveUsage` (persists monthly call counts to `propertystack/runs/brave-usage.json`,
  hard cap `BRAVE_MONTHLY_CAP = 800`); Brave is skipped once the month's cap is hit, falling back
  to whatever Jina returned.
- `BRAVE_API_KEY` loads from `/home/drewp/main-projects/realpage/.env` the same way
  `JINA_API_KEY` already did (`_load_env_key` helper).
- Updated the 3 skills that called `tooling/searx_search.py` directly from their `__main__`
  blocks (`lead-finder-sales-news/sales_news.py`, `lead-finder-agendas/agendas.py`,
  `lead-finder-awards/awards.py`) to use `WebHelper().search` instead.
- Renamed `RunCaps.searxng_searches` -> `RunCaps.brave_searches` (kept `jina_searches`) in
  `runfolder.py` and `run.py`, and updated `tests/test_runfolder.py` accordingly.
- Rewrote `tests/test_fetch.py` for the Jina-then-Brave flow, including a fake `BraveUsage` and
  a new test for the monthly-cap skip, plus 2 tests for `BraveUsage` itself.
- Updated docs that mentioned SearXNG: `tooling/LOCAL-ASSETS.md` (now documents Jina+Brave and
  the ban), `propertystack/skills/lead-finder/SKILL.md`, `propertystack/skills/lead-finder-sales-news/SKILL.md`.
- Old junk-run leftovers (`propertystack/runs/AZ/20260914-full/caps.json`,
  `propertystack/runs/NY/20260914-full/caps.json`) still have the old `searxng_searches` field
  name from before this change -- left alone, since F11 archives that whole run folder anyway.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (all lead-finder* skill tests + the
  site panel check). Also ran the full `propertystack` suite (`--ignore=client-map`, which fails
  to collect for an unrelated pre-existing reason -- missing `census` package, not related to
  this change): 200 passed.
- Nothing left open for F1.

Commit: (see git log for this file's commit)
