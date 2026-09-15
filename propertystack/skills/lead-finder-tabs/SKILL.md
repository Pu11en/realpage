# lead-finder-tabs (T2: TDLR TABS -- the Texas statewide backbone)

The Texas Department of Licensing and Regulation's Architectural Barriers
project registry (TABS) is a statewide list of registered construction
projects -- every apartment/multifamily project of real size in Texas has to
register here, so it's the one free source that covers the whole state, not
just the cities with their own permit feeds.

Input: an area slug (`"tx"`) and a recipe (`recipes/tx/tabs.json`) naming
the search keywords, the registration-date cutoff, the "new construction"
type-of-work code, and the minimum estimated cost. Output: one `LeadRecord`
per qualifying project.

## How it works

- `_search_all_pages` runs TABS's `Search/SearchProjects` POST endpoint once
  per keyword, paginating 100 rows at a time until it has fetched
  `recordsTotal` rows (a project can match more than one keyword --
  `find_tabs_projects` dedupes by `ProjectNumber` before fetching details).
- Only rows whose `TypeOfWork` is the recipe's new-construction code and
  whose `EstimatedCost` is at/above the recipe's floor are kept -- this
  matches the plan's filter (New Construction, estimated cost >= $3M).
- Each surviving project's detail page (`Search/Project/<ProjectNumber>`) is
  fetched and parsed with a `<dt>Label:</dt><dd>value</dd>` regex (the page
  is plain server-rendered HTML, no API). The detail page gives the real
  city and county as text ("Brownsville, TX 78521" / "Cameron") -- **this is
  used directly instead of mapping the search row's numeric City/County
  codes**, because TDLR never publishes those codes' lookup table anywhere
  public and the detail page's own text is ground truth, not a guess.
- Units only ever come from a regex match (recipe's `units_text_pattern`)
  against the detail page's "Scope of Work" text (e.g. "New construction
  apartment complex, 300 units"). No scope match -> `units=None`, which the
  site already renders as "Units: not public yet" -- never estimated from
  square footage or cost.
- Owner name/phone and estimated start/finish come straight off the detail
  page too; office phone falls back to the design firm's phone only if no
  owner name/phone is on file (developer field prefers owner, falls back to
  design firm, matching `find_upcoming`'s owner-over-builder rule).
- A broken detail-page fetch (network error, 500, etc.) never drops the
  project -- it still gets a record from the search row alone (name, city
  from... nothing, in that case city is blank), just without owner/units.

## Rules

- `find_tabs_projects()` takes injected `fetch_search`/`fetch_detail`
  callables (same DI shape as every other lead-finder* skill) so the pytest
  suite stays network-free; `default_fetch_search`/`default_fetch_detail`
  (real HTTP) are only used by `live_self_test.py`.
- No place names anywhere in `tabs.py` -- keywords, date cutoff, cost floor
  and the type-of-work code all come from the recipe.
