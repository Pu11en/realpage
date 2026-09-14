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

## F3 Find permit data everywhere -- done
- `propertystack/skills/lead-finder-sources/find_sources.py` now tries, in order: an
  ArcGIS Online search by place name (`www.arcgis.com/sharing/rest/search?q=title:permits
  "<place>"`) whose first hit's owner org is resolved to that org's own ArcGIS Hub search
  endpoint (`community/organizations/<orgId>` -> `urlKey` -> `<urlKey>-hub.arcgis.com`) --
  falling back to the generic `hub.arcgis.com` hub search only if no org-specific hub was
  found; then the Socrata Discovery catalog (unchanged); then a new `_try_ckan`, which
  queries data.gov's CKAN `package_search` (the closest thing to a universal CKAN catalog --
  individual city CKAN portals have no common discovery API) and pulls the first CSV/JSON
  resource URL from a hit whose owning organization's name says it belongs to this
  city/state.
- Tightened acceptance (`test_dataset`): a dataset is only accepted once a real sample-row
  query returns **at least 100 rows** (bumped the Socrata `$limit` and equivalent sample
  size from 20 to 200), **has an address field** (address/stname/street), and **at least
  one row dated within the last 24 months** (new `_has_recent_date`/`_parse_date` helpers,
  `today` is now an injectable/optional argument on `find_sources()` and `test_dataset()`
  for deterministic tests). A small table of yearly totals -- the kind of thing a real CKAN
  city portal can return instead of permit-level rows -- now fails the row-count check
  instead of being accepted.
- `find_sources_fallback.py`: added a `smartgov` URL/HTML pattern next to the existing
  `accela`/`tyler-energov` ones, and a `NO_FREE_DATA_SYSTEMS` set. If any search result's
  portal is identified as one of those three, it's noted and skipped without ever being
  scraped for "sample permits" (previously an Accela/Tyler portal with a few visible rows
  on its search page was accepted as a working recipe, which isn't real bulk free data --
  it's a permit-by-permit lookup form). If nothing else in the search results works, the
  city comes back as `{"skipped": True, "reason": "no free data (<system> only)", "no_retry":
  True}` instead of the old generic "no permits online" -- so the run loop (and Drew) can
  tell "we truly found nothing" apart from "this city's portal has no free bulk data, don't
  bother retrying it."
- `propertystack/skills/lead-finder/run.py`'s `step_sources` now forwards `deps.today` into
  `find_sources.find_sources(..., today=...)` so the 24-months-recent check is deterministic
  under the chain's injectable "today" the same way every other date-aware step already is.
- Tests: rewrote `tests/test_find_sources.py` for the new try-order (ArcGIS Online org hub
  -> generic ArcGIS hub -> Socrata -> CKAN), with 100+-row fixtures, a new
  `test_arcgis_online_org_hub_used_before_generic_hub`, `test_ckan_catalog_hit_used_when_...`,
  `test_small_yearly_totals_table_is_rejected` (the Phoenix-CKAN-shaped case from the plan),
  `test_dataset_with_no_address_field_is_rejected`, and `test_dataset_with_only_old_dates_is_
  rejected`. Rewrote the two Accela/Tyler tests in `tests/test_find_sources_fallback.py` to
  expect the new no-free-data skip instead of a saved recipe, and added a `smartgov`
  `identify_system` case. Updated `lead-finder/tests/test_run.py`'s fixture rows from 1 to
  121 (100+ needed to pass the new bar) and routed its fake `http_get_json` to return empty
  ArcGIS results so the Socrata path is still what the test exercises.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (all lead-finder* suites + the site
  panel check). Full suite `python3 -m pytest -q propertystack --ignore=propertystack/skills/client-map`:
  221 passed (up from 217 at F2).
- Nothing left open for F3. The ArcGIS-Online-org-hub-resolution shape (exact JSON fields
  from `sharing/rest/community/organizations/<orgId>`) is my best-faith reading of the
  plan's instruction and is only exercised against fakes here -- it should get its first
  real-network exercise in F4 (Arizona permit recipes), which is the first task that will
  actually call `find_sources` against live endpoints.
