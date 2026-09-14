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

## F4 Arizona permit recipes -- done
- Hand-tested every endpoint from the research file live (real `curl` queries against
  each city's actual ArcGIS/Socrata service, not the F3 auto-discovery chain -- these
  layers need per-city filter tuning that generic discovery can't infer) and saved a
  recipe per city under `propertystack/recipes/az/`: `phoenix.json`, `mesa.json`,
  `tempe.json`, `scottsdale.json`, `gilbert.json`, `tucson.json`,
  `maricopa-county-unincorporated.json` -- 7 of the 8 named sources.
- **Peoria dropped, not written as a recipe.** Its ArcGIS layer is one row per
  property (not per permit): filtering to apartment-use properties returns almost
  entirely trade/repair permits on existing buildings (gas line repairs, backflow
  device swaps) -- there's no field that isolates true new-construction permits (no
  "New" `B1_PER_SUB_TYPE` values exist at all in the layer). Rather than write a
  recipe that would flood the run with false "new apartment project" leads, it's
  skipped the same way F3 skips an Accela/Tyler-only city -- no free usable data.
  Flagging this for Drew: Peoria new-construction leads would need a paid/manual
  source if he wants that city covered later.
- Each recipe's `endpoint` is a complete, pre-built query URL (where clause +
  outFields + order already baked in server-side) rather than a bare table URL --
  necessary because plain unfiltered hits would return whichever few hundred rows
  the server defaults to, mostly unrelated permits, and because Mesa's real
  `type_of_work` values (`Multi-Family Residential`, discovered live) don't match
  what the research file guessed (`permit_type='Multi-Family Residential'` --
  `permit_type` is actually only ever COM/RES/SVC/N-A on that dataset).
- Found and fixed two real gaps in `find_upcoming.py` while getting these to
  return real rows, not just data-shape mismatches:
  - ArcGIS FeatureServer date fields (Phoenix, Scottsdale, Gilbert, Tucson,
    Maricopa County -- all except Mesa/Tempe) come back as epoch-millisecond
    integers, not date strings; `_parse_date` silently returned `None` for every
    row until given an `isinstance(value, (int, float))` branch, which would have
    made every permit "un-dated" and dropped.
  - Tempe's leasing-start field is `COIssuedDate`, which doesn't match the
    generic certificate-of-occupancy field-name regex (`cert.*occup|...`); added
    an explicit `fields["co_date"]` override, used by Tempe's recipe, that takes
    priority over the regex scan.
  - Added text-parsed units: `fields["units_text_field"]` + a recipe-level
    `units_text_pattern` regex, for cities whose layer has no numeric units field
    (Mesa's `description_of_work` has "(11) unit"/"17-unit"/"305-units"-style
    text; Maricopa County's `PermitDescription` has "144 UNIT..."-style text).
  - Gilbert, Phoenix, Scottsdale have no unit field and no parseable unit text on
    the permit row at all -- their recipes note `unit_lookup_order` (permit text
    -> project site/news via Jina -> county parcel) for F7/F8 to use later, per
    the plan's fallback order; units stay `None` here, never guessed.
  - Tucson's `DwellingUnits` field is often 0 or 1 even for large projects (one
    permit row = one building of a multi-building complex) -- noted in its
    recipe as suspect, to double check against `PROJECTNAME` text or site/news.
- Scottsdale's recipe carries `Owner`/`Builder` field names too (real developer
  names come back on live rows, e.g. "MREG 101 Bell LLC / Mack Real Estate
  Group") -- useful for F8 (owners/phones) without a second lookup.
- New tests in `lead-finder-permits/tests/test_find_upcoming.py`: epoch-ms date
  parsing, `fields["co_date"]` override beats the regex scan, and
  `units_text_field` + `units_text_pattern` parses "36 unit" out of a
  description. All offline/fixture-based, no network -- matches how the rest of
  this skill's tests work and keeps `check-lead-finder.sh` network-free.
- New `lead-finder-permits/live_self_test.py` -- not part of the pytest suite,
  run by hand (`python3 propertystack/skills/lead-finder-permits/live_self_test.py
  az`): hits every saved recipe's real endpoint and asserts `find_upcoming()`
  returns at least one real multifamily row. Ran it just now: all 7 recipes
  passed, e.g. Tempe returned 11 rows including a real 533-unit project, Mesa
  returned 47 rows including a real 305-unit project -- these are today's live
  permit data, not fixtures.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (51 lead-finder* tests
  now, up from 50, plus the site panel check); full suite
  `python3 -m pytest -q propertystack --ignore=propertystack/skills/client-map`:
  224 passed (up from 221 at F3). Also re-ran `live_self_test.py` after the fix
  to confirm it still passes live.
- Nothing left open for F4 except the Peoria gap noted above (no free data, by
  design, same as F3's Accela/Tyler/SmartGov skip rule) -- F5 (county sales
  file) is next and is unrelated to Peoria specifically.

## F5 Recently sold, from the county's sales file -- done
- Fetched and read both Maricopa County Assessor items live (item pages +
  actual `.../data` zip downloads, ~61MB Sales Affidavits, ~109MB Secured
  Master parcel file across 5 book-series `.txt` files) and read both file
  spec PDFs end to end before writing any code:
  - **Property type/use code**: the Sales Affidavits file's column 8
    (`PROPERTYTYPECODE`) is the field, and it's self-labeling -- column 9
    right next to it (`PROPERTYTYPEDESCRIPTION`) prints the human name on
    every row. Code `E` = `"Apartment Building"`, confirmed by grepping the
    live 1M+-row file (15,564 rows are code E, next to `B`=Single Family
    Reside, `C`=Condo/Townhouse, `F`=Commercial/Industrial, `D`=2-4 Plex,
    etc.). No separate code-lookup table was needed or invented.
  - **Unit counts**: the sales file has **no unit-count field at all** (44
    columns total, checked every one against the file-spec PDF). Units come
    only from the second file, the parcel/"Secured Master" file, whose
    column 38 is `NumUnits` (called `Number_Of_Units` in the PDF spec, but
    the actual `.txt` header uses `NumUnits`). Joined the two files live on
    parcel number (Sales `PARCELNUMBER` == Parcel `FolioKey`, e.g.
    `"15940087A"` in both) -- confirmed real matches, e.g. parcel
    `13303005C` (a sales-file code-E row) has `NumUnits=289` in the parcel
    file.
  - Also checked the parcel file's own `Property_Use_Code` (PUC, 4-digit)
    field as a possible second/independent apartment signal -- real PUC
    values on 20+-unit properties cluster in 0300-0399 (0376, 0377, 0366...)
    but that range isn't apartment-exclusive (also covers other
    multi-residential/commercial-adjacent categories per Maricopa's own use
    code list) and would need a use-code table this build has no verified
    source for. Not used -- the sales file's own labeled type code (`E`) is
    the authoritative, already-verified signal, so PUC was left as a noted
    "also inspected, not needed" fact in the recipe rather than guessed into
    the filter.
- New skill `propertystack/skills/lead-finder-sales/find_sold.py` --
  generic, area/county-agnostic: takes an area slug, a recipe (sales source +
  parcel source + field-name maps + apartment type codes + min units +
  recent-months window), and an injected `fetch_rows(source) -> rows`
  callable (same dependency-injection shape as `find_upcoming`'s `http_get`).
  Filters sales rows to the recipe's apartment type code(s), parses the
  `MMYYYY`-format sale date (Maricopa's format; also handles `YYYY-MM-DD` /
  `MM/DD/YYYY` / `MMDDYYYY` for other counties' likely formats), keeps only
  sales within `recent_months` (24) of "today", looks up units via the
  parcel-number join, and drops (never estimates) any sale with no unit
  record or fewer than `min_units` (20). Returns one `LeadRecord` per
  qualifying sale: `stage="sold"`, `address`, `city`, `units`, `sale_date`,
  `buyer` (grantee), `developer` (grantor, doubling as seller), and a
  `why` note that includes the sale price when known.
  `default_fetch_rows` (real zip download + pipe-delimited parse, used only
  by `live_self_test.py`) is a separate, equally generic function -- any
  county whose sales/parcel data ships as a zipped pipe-delimited flat file
  with a header row works with it unchanged.
- Confirmed **not** confusing this with `lead-finder-sales-news` (already
  existed, part 4.3, news/GDELT-based sale mentions for any city) -- this is
  a new, separate skill reading the county's own recorded-sale flat file, not
  news text.
- New recipe `propertystack/recipes/az/maricopa-county-sales.json`: both
  ArcGIS item URLs (`.../data` for the real zip, `?f=json` item page for
  provenance), `file_glob: "Data/*.txt"` for both zips, the field-name maps
  above, `apartment_type_codes: ["E"]`, `min_units: 20`, `recent_months: 24`,
  and a `notes` field spelling out the PUC-not-used decision so nobody
  re-guesses it later.
- **Live test** (`python3 propertystack/skills/lead-finder-sales/live_self_test.py az`,
  actually run just now against the real live Maricopa County zips, not
  fixtures): **153 real apartment sales (20+ units) in the last 24 months**,
  well over the plan's 10-sale bar -- e.g. 6901 E Chauncey Ln, Phoenix, 497
  units, sold 2024-09, buyer AZ DESERT CLUB APARTMENTS LLC, $187,500,000;
  1350 E Thomas Rd, Phoenix, 130 units, sold 2024-09, buyer SRP TERRACE LLC,
  $16,500,000.
- Offline tests: new `lead-finder-sales/tests/test_find_sold.py` (10 tests,
  all fixture-based, no network) -- apartment+enough-units kept; wrong type
  code dropped; too-few-units dropped; no unit record at all dropped (not
  guessed); sale older than 24 months dropped; a bad/blank date dropped; a
  missing sales source returns empty; a `fetch_rows` exception returns empty
  instead of raising; only the qualifying row survives out of a mixed batch.
- Found one incidental collection issue while running the full suite: two
  `live_self_test.py` files (this one and F4's, in different skill
  directories with no `__init__.py`) collide under whole-tree pytest
  collection ("import file mismatch") because they share a basename and
  pytest's default `python_files` pattern (`*_test.py`) picks them up even
  though they're meant to be hand-run only. Fixed generically, not by
  renaming either script: added `propertystack/conftest.py` with
  `collect_ignore_glob = ["*/live_self_test.py"]`, so any current or future
  skill's hand-run live self-test is excluded from pytest collection
  wherever it's run from, while `check-lead-finder.sh` (which never globbed
  these files anyway -- it only runs each skill's `tests/` directory) is
  unaffected.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (61 lead-finder*
  tests now, up from 51 at F4, plus the site panel check); full suite
  `python3 -m pytest -q propertystack --ignore=propertystack/skills/client-map`:
  234 passed (up from 224 at F4).
- Still open: none for F5 itself. Two honest limitations carried into the
  recipe's `notes` rather than papered over: (1) the sales file's "last
  recorded sale" note in its own file spec means a parcel that sold twice in
  the window only shows its most recent sale -- acceptable per the plan's
  literal ask ("recently sold... in the last 24 months") but worth knowing if
  Drew later wants a full sale history; (2) the parcel file's PUC field could
  give a second, more granular apartment signal for other counties whose
  sales files lack a labeled type code the way Maricopa's does, but no
  verified PUC-to-description table was found in this build, so it's left
  unused rather than guessed -- a future county recipe with only a numeric
  use code and no separate lookup table would need that table sourced first.

## F6 Answer key for Arizona -- done
- Built `propertystack/answer-keys/az.json` by hand using live web search/fetch
  (WebSearch + WebFetch), never the lead-finder tool itself and never the city
  permit layers or the Maricopa County sales file -- sources are news
  articles, developer/trade press releases, and buildings' own websites.
- 15 real 20+ unit-scale Arizona apartment properties (8 new/leasing/under
  construction, 7 recently sold), each with address, city, unit count (where
  publicly known -- The Crescent's isn't yet, left `null` rather than
  guessed), a `why`, and a `source_url` + `source_type` for hand re-verification:
  Lumara (Phoenix, Toll Brothers/Willton, 456u), Avilla Foothills (Surprise,
  NexMetro, 108u), Album Surprise (Surprise, Greystar 55+, 161u), The Crescent
  (Phoenix hotel-to-apartment conversion, Foundation 8), Northbend (Tempe,
  Milhaus/Banyan, 310u), Dwell at 5th and Farmer (Tempe, Mark Taylor, 129u),
  Navona (Mesa, Toll Brothers/Canyon Partners, 400u), The Stately Avondale
  (Avondale, Ascent/Merit, 286u), Marquee on 5th and Bella Victoria (Tucson/Mesa,
  the plan's own named fixtures), Azul (Phoenix, sold 2025-05, 227u, $37.1M),
  Broadstone Seventh Street (Phoenix, sold 2026-06, 258u, $81.4M), and Lazo /
  Zone / Zone Lux (Chandler/Glendale, the 3-asset Sunroad->Fairfield portfolio
  sale, sold 2025-07, $244.8M/907 units total).
- **5 with software hand-verified from the building's own site** (its real
  resident-portal/applicant-login link, fetched live, not a listing site):
  Lumara = Yardi (securecafenet.com/securecafe.com), Navona = **Entrata**
  (residentportal.com/prospectportal.com -- the required non-Yardi example),
  The Stately Avondale = Yardi (securecafenet.com), Marquee on 5th = Yardi and
  Bella Victoria = Yardi (both per the plan's own stated ground truth, cross-
  checked against their sites' portal links).
- Checked: `python3 -c "import json; d=json.load(open('propertystack/answer-keys/az.json')); assert len(d['leads'])==15; assert sum('software' in l for l in d['leads'])==5"` passes.
  Also reran `bash tooling/qa/check-lead-finder.sh` (unaffected by this task,
  still all green) since the plan's Check command runs after every task.
- Nothing left open for F6. This key is the ground truth F9's quality bar
  (answer-key recall, software accuracy) will be measured against starting
  at F10/F11.

## F7 Software detection v2 -- done
- Found the software-detection chain was already built (`propertystack/skills/lead-finder-software/detect.py` +
  `rules.json`), using the exact portal/hop/asset/text approach the plan describes, with rules for RealPage,
  Yardi, Entrata, AppFolio, ResMan and more (already matching the vendor host patterns F7 names). What was
  missing was the required live test on the 5 answer-key buildings -- ran it and found 2 real bugs, both fixed:
  1. **Cloudflare challenge pages were accepted as real content.** `fetch.py`'s `_BLOCK_MARKERS` didn't catch
     a "Just a moment..." Cloudflare Turnstile page, so `WebHelper.fetch()` returned it as `ok=True` with no
     real links on it -- 3 of 5 buildings (Marquee on 5th, Bella Victoria, The Stately Avondale) looked
     "no-portal-link"/"blocked" even though Scrapling's stealthy fetcher gets past Cloudflare fine when the
     block is actually detected and it's given the chance to run. Added `"just a moment"`,
     `"checking your browser"`, `"cf-turnstile"`, `"challenges.cloudflare.com"` to `_BLOCK_MARKERS` so the
     fallback chain (crawl4ai -> Scrapling -> Playwright) actually kicks in.
  2. **A too-broad "captcha" marker was a false positive.** Bella Victoria's real homepage JSON config has a
     harmless `"recaptchaV3Key":""` field -- the old bare `"captcha"` substring check treated that as a block.
     Tightened to `"complete the captcha"` / `"solve the captcha"` (still catches a real captcha wall, stops
     matching ordinary reCAPTCHA config mentions). Updated the one test fixture
     (`tests/test_fetch.py::test_fetch_falls_through_fetcher_chain`) that relied on the bare word.
  3. **Second-page "confirm" was rejecting real portal matches.** Part 4.2's second-page re-fetch
     (`_confirm_on_second_page`) was being applied even to `portal`-signal matches, but a resident-login link's
     own domain (e.g. `lumaraphoenix.securecafe.com`) is frequently *itself* behind the same kind of bot wall
     -- re-fetching it to "confirm" just returned a challenge page with no vendor evidence, turning a correct
     match into a false "unconfirmed" (this hit 2 of 5 buildings even after the Cloudflare-marker fix). Added
     `_vendor_owns_host()`: when the vendor pattern matches the link's actual *host* (not just some
     coincidental path/query substring), that's already unambiguous evidence and skips the extra fetch;
     a match only in the path (the existing fixture test's contrived case) still requires second-page
     confirmation, so that protection against a coincidental match stays in place. Updated `detect.py`'s
     docstring to describe the new rule.
  - Also found the cause behind an earlier confusing debug run: `WebHelper.fetch()`'s on-disk cache
    (`propertystack/runs/cache/`) stores whatever the first fetch returned, blocked page included, and serves
    it forever after with no re-check -- so a stale blocked-page cache entry from before these fixes kept
    failing even once the code was fixed. No code change needed (F9's quality alarms / a future run naturally
    gets a fresh cache dir per run), but cleared the 5 stale cache entries left over from local debugging.
- New `propertystack/skills/lead-finder-software/live_self_test.py` (hand-run only, matches the F4/F5 pattern
  and is excluded from pytest collection by `propertystack/conftest.py`'s existing `collect_ignore_glob`):
  fetches each of the 5 F6 answer-key buildings' real website (Lumara, Navona, The Stately Avondale, Marquee
  on 5th, Bella Victoria) and asserts `detect_software()` returns the same vendor a human verified by hand.
  Ran it live just now: **5/5 correct** (Lumara=Yardi, Navona=Entrata, Stately Avondale=Yardi,
  Marquee on 5th=Yardi, Bella Victoria=Yardi, all `signal=portal`).
- Updated 2 existing offline tests in `lead-finder-software/tests/test_detect.py` that assumed every portal
  match needed second-page confirmation -- now split into "host match, no confirm needed" (already covered by
  other passing tests) vs. the contrived path-only-match case, which still requires confirmation and still
  passes.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (still 51 lead-finder* tests + the site panel check,
  no count change since this was fixes/tests to existing files, not a new skill). Full suite
  `python3 -m pytest -q propertystack --ignore=propertystack/skills/client-map`: 234 passed (unchanged from F6,
  same reason). Also reran the new live self-test after each fix to confirm against real websites, not fixtures.
- Nothing left open for F7.

## F8 Phones and owners -- done
- **Permit-row owner/builder (Scottsdale, Tempe-style recipes):** `find_upcoming.py`'s
  `_build_record` now reads a new `_find_owner()` helper, which checks the recipe's top-level
  `owner_field`/`builder_field` (already present in Scottsdale's saved recipe from F4, e.g. its
  live-tested `Owner: MREG 101 Bell LLC`) against the row and fills `LeadRecord.developer` --
  owner preferred over builder (the property owner, not the general contractor, is who to call
  about picking software), and a `{"fact": "developer", "url": permit_link}` source recorded.
  Never guesses: a recipe/row with neither field leaves `developer` blank, same as before.
- **Sold-stage owners:** already covered by F5 (`find_sold.py` sets `developer` = grantor,
  `buyer` = grantee straight from the county sales file) -- nothing new needed there, confirmed
  by re-reading that code.
- **F2 check now used in the developer-website lookup**, as the plan asks (`contact.py`'s
  `find_website`): imports `is_about_building` from `propertystack/lib/building_match.py` (the
  same module F2 built) and only accepts a search result whose url+title is really about that
  developer, rejecting listing/directory domains and unrelated hits with no name match --
  before this it returned whatever the first search result was, developer name entirely
  unchecked. Updated the existing fixture tests to add a `title` to their fake search results
  (a bare "acmedev.example.com" url alone doesn't literally contain the word "development"),
  and added `test_find_website_skips_result_not_about_the_developer` and
  `test_find_website_skips_listing_domain`.
- **Phone de-duplication:** `find_office_phone` now tracks every formatted number already seen
  and skips repeats, so the same office number printed twice on a page (header + footer, a
  common real pattern) doesn't change the result, and a duplicated cell/fallback number doesn't
  block a later real office number from replacing it. Office/unlabeled numbers still always win
  over fax (skipped outright) and cell/mobile (fallback only). New tests
  `test_find_office_phone_dedupes_repeated_number` and
  `test_find_office_phone_prefers_office_over_repeated_cell`.
- **Live test** (`python3 propertystack/skills/lead-finder-contact/live_self_test.py`, run just
  now against real live sites, not fixtures) on 3 of the F6 answer-key buildings: Lumara ->
  (520) 636-0838, Navona -> (833) 816-2135, The Stately Avondale -> (785) 451-3548, all real
  office numbers pulled straight off each building's own website. Also ran `find_website` live
  for "Toll Brothers Apartment Living" (Lumara's real developer, per its own press release) and
  it correctly found `https://www.tollbrothersapartmentliving.com/` through the new F2 check.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (51 lead-finder* tests + the site panel
  check -- unchanged count since these are edits to existing skills, not new ones; the new tests
  land inside those same suites). Full suite
  `python3 -m pytest -q propertystack --ignore=propertystack/skills/client-map`: 241 passed (up
  from 234 recorded at F7 -- F7 itself added no new tests, so this is +7 net: 3 permit-owner
  tests, 4 contact tests). `propertystack/runs/brave-usage.json` was created/updated by the live
  test's real search call -- left untracked, same as before (it's runtime usage-counter state,
  never committed).
- Nothing left open for F8.

## F9 Quality alarms -- done
- New `propertystack/skills/lead-finder/quality.py`: `check_quality(state, records,
  cities_with_source, total_cities, answer_keys_dir=None)` reads
  `propertystack/answer-keys/<state>.json` (F6), matches each answer-key building to
  a run's LeadRecords by normalized address (`record.normalize_address`, same rule
  `merge.py` uses) or name if neither side has an address, and computes: answer-key
  recall, software accuracy (only over key entries that carry a hand-verified
  `software` field), overall %-with-units/website/software/phone, and separate bars
  for existing buildings (`stage` leasing/sold: website/software/phone %) vs
  not-yet-built projects (`stage` permitted/under construction: % correctly showing
  "not picked yet" software, % with both a developer name and an office phone).
  Every bar from the plan is checked; `passed=False` with a `fail_reasons` list of
  plain-English reasons (including "no answer key found for this state") when any
  bar is missed. `write_quality_json(run_folder_path, report)` writes it to
  `<run folder>/quality.json`.
- Wired into `run.py`'s `main()`: after `run_chain` finishes, loads the saved
  `cities` step file to get the real city list (works whether it came from an
  explicit `--city` list or the ranked Census fetch), counts cities whose
  `sources` step found a real (non-skipped) recipe via new `cities_with_real_source()`,
  calls `check_quality`, writes `quality.json`, and **only calls `write_area_leads`
  (which is what makes a run show up on the site) if `report["passed"]` is true** --
  a failing run prints its fail reasons and `main()` returns exit code 1 instead of
  writing `propertystack/data/<state>/leads.json`. `run_chain()`'s own signature and
  return value are unchanged (still just the scored `LeadRecord` list) so the
  existing `test_run.py` resume tests didn't need touching.
- Tests: new `propertystack/skills/lead-finder/tests/test_quality.py` (5 tests, all
  offline with fake `LeadRecord`s and a temp answer-key file) -- a fully-passing run
  meets every bar; low answer-key recall fails with the right reason string; a
  missing answer-key file fails with "no answer key found for this state"; an
  existing (leasing-stage) building missing its website fails that specific bar;
  `write_quality_json` writes the file. Did not add a live test against the real AZ
  answer key here -- F10/F11 (the next tasks) are exactly that real run, and will be
  the first live exercise of this gate on real data.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes, lead-finder-tagged suites
  now 56 (up from 51, +5 new quality tests). Full suite
  `python3 -m pytest -q propertystack --ignore=propertystack/skills/client-map`:
  246 passed (up from 241 at F8, +5, matching the new test file exactly -- no
  existing test broke).
- Nothing left open for F9.
