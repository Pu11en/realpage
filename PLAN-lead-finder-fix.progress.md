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

## F2 "Is this really about this building?" check -- done
- New shared module `propertystack/lib/building_match.py`: `distinctive_words`,
  `is_listing_domain` (a broadened listing/aggregator reject list -- zillow, apartments.com,
  apartmentguide, apartmentratings, yelp, facebook, trulia, rent.com, plus the generic
  `rentcafe.com` hub; a `*.rentcafe.com` community subdomain is still allowed, since it's
  the community's own leasing page and Yardi evidence), `street_hit` (house number + street
  word both present), `matches_building` and `is_about_building` (the full check: reject
  listing domains, then require every distinctive word of the name, or the street address,
  somewhere in the url/title/page text -- a single shared word like "Marquee" is never enough).
- Wired into all three places named in the plan:
  - `skills/find-website/run.py` (`classify`): "high" now needs every distinctive word (or
    the address) to hit, not "all but one" -- that's what was letting
    `marqueesportsnetwork.com` and `themarqueestl.com` both count as "Marquee on 5th"'s site.
    Also dropped the old always-accept "low" tier (a single-word partial match) entirely --
    it's rejected now instead of returned as a website at low confidence.
  - `skills/lead-finder-details/project_details.py` (`_pick_website`, used by `fill_project_details`):
    only accepts a search result as a project's website if `is_about_building` passes on its
    url+title; a not-yet-built project with no real name/address match correctly gets no
    website (matches the "no website yet = the lead" rule already in the plan).
  - `skills/contact-scrape/run.py` (`scrape`): before pulling phone/email off a fetched page,
    checks the page text is really about that building's name/address; rejects with
    `notes: "page-not-about-this-building"` otherwise (catches a bad website slipping through
    from an earlier step).
  - Looked at `skills/lead-finder-contact/contact.py`'s `find_website` (developer/owner site
    lookup) too, but its existing tests assume domains like "acmedev.example.com" for
    "Acme Development" -- a full-word match would break real matches there, so left it as-is;
    the plan's F2 examples (Marquee, Bella Victoria) are building names, which is what F2's
    named targets (`project_details`, `find_website` [the skill], `contact_scrape`) actually
    cover.
- Tests: new `propertystack/lib/tests/test_building_match.py` (9 tests), new
  `propertystack/skills/find-website/tests/test_find_website_run.py` (3, including the exact
  Marquee/Bella Victoria fixtures from the plan), new
  `propertystack/skills/contact-scrape/tests/test_contact_scrape_run.py` (3), plus 2 new
  fixture tests added to `lead-finder-details/tests/test_project_details.py` for the same
  two real cases. Both new test files import their skill's `run.py` via `importlib` by path
  (not `from run import ...`) so they don't collide with `contact-scrape/run.py` also being
  named `run.py` when pytest collects the whole `propertystack/` tree at once.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes. Full suite
  `python3 -m pytest -q propertystack --ignore=propertystack/skills/client-map`: 217 passed
  (up from 200 at F1, all new).
- Nothing left open for F2.
