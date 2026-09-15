# PropertyStack lead finder: faster, fewer dropped leads, then as much of Texas as possible

Written 2026-09-14 with Drew. **Starts only when Drew says "go work"** (the Arizona fix build is merged; AZ is on the
site from the free permit pull, 94 leads). All rules from `PLAN-lead-finder.md` and `PLAN-lead-finder-fix.md`
still apply: area-agnostic code (place specifics only in data recipes), never guess facts, Jina first +
Brave second (keys in `/home/drewp/main-projects/realpage/.env`, or the build copy's own `.env`; never
commit), SearXNG banned, **no quality gates** (quality.json is a report only), localhost only, never push.
- Why part 1: live check of the Arizona run (2026-09-14) -- one-at-a-time lookups (Phoenix details 10 min,
  Mesa 12 min), dead-end steps on towns with no data, Scottsdale returned 0 of ~68 apartment permits,
  Phoenix kept 13 of 360 new commercial permits, 8 projects under 20 units slipped in, 150-project cap
  could cut cities off.
- **Data first, search last (Drew 2026-09-14, after the AZ run):** the free permit pull (`permit_only.py`)
  gave 94 AZ leads in 2 minutes for $0; the 40-minute web-lookup run mostly found nothing. So: every fact
  that a public record already holds (project name, units, address, dates, owner, builder, owner phone,
  sale date, buyer) comes from the record. Web search is used **only** for (a) software on buildings that
  already exist (leasing or sold) and (b) a developer's office phone when no record has one. Not-yet-built
  projects are never web-searched for a website (they're "Earliest: software not picked").
- **Save as you go:** every run commits its run folder and the area's `leads.json` **after each city /
  source** (`git add propertystack/runs/<state>/<run-id> propertystack/data/<state>; git commit`), because
  a gowork build copy deletes uncommitted files when the build ends (the first AZ full run lost 79
  projects this way).
- Texas sources (live-tested): `docs/2026-09-14-texas-sources-research.md` -- read it first.
- **Texas scope:** the whole state except Collin County (Plano-Richardson is its own finished area and is
  never rerun). Texas has many RealPage clients (40 in the client map) -- RealPage buildings are dropped
  as usual.
- **Aim at RealPage's gaps: rank, don't ban (Drew 2026-09-14).** Order Texas cities and sources so places
  with few or no RealPage buildings in `propertystack/data/client-map/counts.json` come first, and the
  growing suburbs around RealPage-heavy cities get priority. Cities with 3+ RealPage buildings in the
  client map (today: Houston, Fort Worth, McKinney, Frisco, Grand Prairie, Allen, Austin, Dallas, Denton --
  read them from the data file, never hard-code) go **last**, only if the caps allow. The client map is a
  sample, so this is a ranking, not a ban. Each lead's "why" notes when its city is a RealPage gap.
- **Pre-approved, don't ask:** Jina searches up to 1,500 for the Texas run (~$0.75) and 900 for the
  Arizona re-run; Brave stays under its 800/month free cap; free public downloads (incl. the ~200 MB
  appraisal-district files, cached under `propertystack/runs/cache/`, gitignored).

Run with: `Do the next unticked task in PLAN-lead-finder-texas.md, then tick it and stop.`
Check: `bash tooling/qa/check-lead-finder.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765 → Early Leads → Tx

## How to try it (30 seconds)
1. Early Leads → Az: more leads than before (Scottsdale and more Phoenix projects now show).
2. Early Leads → Tx: hundreds of new and recently sold Texas apartment buildings with a city filter (Austin, Houston, Dallas, Fort Worth, San Antonio...).
3. Open a Texas lead from the state registry: owner name and phone, estimated start and finish dates.

## Tasks

### Part 1: Faster, fewer dropped leads (Arizona)
- [x] **S0 Save as you go + data-first switch.** `run.py` commits the run folder + `leads.json` after
  each city (wrapper script or a `--commit-each` flag); enrichment runs only as described in "Data
  first" above (skip website search for not-yet-built projects). Tests. Commit.
- [x] **S1 Parallel lookups.** Details, website, software and contact lookups run 6 at a time (thread
  pool) instead of one by one; keep 2 s between visits to the same site, stay under Jina ~100/min, cache
  every page. Time Tempe's details step before and after and write both in the progress log. Tests.
  Commit.
- [ ] **S2 Skip dead ends.** Meeting-agenda, Legistar, civic and per-city sales-news steps run only for
  cities with a working permit source or ≥10 new 5+ unit permits in the Census data; cache a city's
  agenda-system detection across runs. Log what was skipped and why. Tests. Commit.
- [ ] **S3 Fix dropped and leaked leads.** Find out, with the saved real rows, why Scottsdale's recipe
  gives 0 projects and why Phoenix keeps only 13 of ~360 (date parsing? keyword filter? unknown units
  being dropped instead of kept as "Units: not public yet"?) and fix it in code or the recipe; fill blank project names from the permit's other name/description
  field or, failing that, the street address (Phoenix returned many blank names); make
  sure projects with a known unit count under 20 are never kept (8 slipped in, mostly Mesa). Fixture
  tests from those real rows. Commit.
- [ ] **S4 Caps that don't cut cities off.** Per-state caps become 400 projects / 900 searches, and a
  cap is only checked between cities (a city is never cut in half). Tests. Commit.
- [ ] **S5 Arizona re-run.** Start from the free permit pull (`permit_only.py --state AZ`), add the Maricopa
  County sales file (sold buildings -- it was never wired into run 1) and owner/builder fields, then
  enrichment per "Data first"; new run id with S0-S4; build the site + chat (`bash tooling/dev.sh`); write
  before vs after in the progress log (projects, per-city counts, minutes, searches, websites, software
  found). Commit.

### Part 2: Texas
- [ ] **T1 Texas area.** Area `tx` = Texas minus Collin County (skip any city/record in Collin County;
  Plano-Richardson untouched). City list from Census permits, reordered by the RealPage-gap rule above (fewest RealPage
  buildings first, RealPage-heavy cities last). Commit.
- [ ] **T2 TDLR TABS -- the statewide backbone.** Puller for the Texas registry (endpoint and form fields
  in the research file): registrations since 2024-09, New Construction, estimated cost ≥ $3M, project or
  facility name / scope matching apartment, apartments, multifamily, multi-family, lofts, residences,
  flats, senior living; 100 per page; then each project's detail page for full address, scope, square
  feet, owner name + address + **phone**, design firm, estimated start/finish (start/finish drive the
  stage and "opens" date). Map city/county codes to names (find the code table on the TABS site). Units
  only from the scope text ("300 units"), else "Units: not public yet". 1-2 s between requests, cache
  every page. Tests with saved responses. Commit.
- [ ] **T3 Texas city permit recipes.** Tested recipes (data) for Austin (Socrata, `housing_units`),
  San Antonio (CKAN SQL, two resources), Fort Worth (ArcGIS, page past 1,000 rows, `Units` as text),
  Arlington (ArcGIS), Houston (weekly "Sold Permits" spreadsheets -- read all posted weeks), San Marcos,
  and Tarrant County's TAD commercial permits zip (all Tarrant cities, `Total Units`). Live self-test
  each. Commit.
- [ ] **T4 Dallas + Houston from appraisal-district files.** DCAD bulk zip: apartment accounts that are
  new / under construction (PCT_COMPLETE < 100, NUM_UNITS ≥ 20, with PROPERTY_NAME) → new projects;
  deed transfers since 2024-09 on apartment accounts (NUM_UNITS ≥ 20) → sold, with new owner + mailing
  address. HCAD bulk zip: state class B1 accounts with a deed since 2024-09 (drop small buildings by
  building area) → sold; new_construction_val > 0 → new projects. Stream-parse, cache the zips. Generic
  code ("appraisal file recipe"), county specifics in data. Tests with small saved samples. Commit.
- [ ] **T5 Tarrant sales with prices + affordable pipeline.** TAD improved-sales zip, Apartment sheet
  (2025 + 2026 files): sold with price, units, date, buyer where given. TDHCA HTC inventory (new
  construction approved since 2024) and the 4% status log: new affordable projects with units and
  applicant phone. Commit.
- [ ] **T6 Texas run.** Records first, commit after each source: TABS + city recipes + appraisal files +
  TDHCA (all free, no web search), then enrichment per "Data first"; full chain for `tx` with S0-S4: TABS + city recipes + appraisal files +
  TDHCA, merge duplicates across sources (address/geocode + name), website / software / phone
  enrichment, score (quality.json report only). Commit.
- [ ] **T7 Texas on the site + chat.** Build the site and rebuild the chat with the `tx` area; run the
  Check and `tooling/qa/check-answers.sh`. Commit. Recap in plain words: Texas leads by city and by
  source, how many with software and phone, searches used.
