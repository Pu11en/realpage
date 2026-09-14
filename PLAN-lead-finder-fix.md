# PropertyStack lead finder: fix it so it finds real leads (Arizona, then states near Texas)

Written 2026-09-14 with Drew after the first real run came back thin (AZ 19 leads, NY 2, every lead
"software unknown", no phones). Why it failed: `/home/drewp/main-projects/handoffs/2026-09-14-lead-finder-why-thin.md`.
Tested sources and tools: `/home/drewp/main-projects/handoffs/2026-09-14-lead-finder-tools-v2-research.md`
(read it first -- it has the exact, live-tested Arizona endpoints and filters).
Rules from `PLAN-lead-finder.md` still apply (area-agnostic code: place specifics only in data recipes;
never guess facts; Plano never rerun; localhost only, never push).

**Drew's decisions (2026-09-14):**
- **SearXNG is banned** -- removed from the computer; never use it, not even as a backup. Same for any
  tool that fails a real run.
- **Search = Jina first, Brave Search API second** (`JINA_API_KEY`, `BRAVE_API_KEY` in
  `/home/drewp/main-projects/realpage/.env`; never commit keys). No Google Places.
- **Arizona first, then states near Texas** (New Mexico, Louisiana, then Oklahoma, Colorado, Arkansas).
  New York is finished (keep its 2 leads as they are).
- **Quality alarms instead of blind non-stop:** a run must meet the quality bar on real data; if it
  can't after two fix attempts, stop with STUCK and a plain report rather than fill the site with junk.
- **Pre-approved, don't ask:** Jina + Brave searches up to 450 per state run (Jina ~$0.0005/search;
  Brave has $5 free credit a month -- hard cap 800 Brave calls/month, then Jina-only; never pay
  beyond the free credit), free public data downloads.
- **Out of scope (cut list):** New York; Chandler, Goodyear, Buckeye (Accela/SmartGov only, no free
  data); Shovels.ai; Google Places; email addresses; named contacts beyond what a permit/news names.
- **No website yet = the best lead, not a gap (Drew 2026-09-14):** a not-yet-built project with no
  website or leasing site hasn't picked its software. Show it as "Earliest: no website yet -- software
  not picked", and rank it above same-stage projects that already have a leasing site.
- **This build = Arizona only (Drew 2026-09-14).** States near Texas are planned after Drew sees Arizona.
- **Timebox:** 12 steps × 20-30 min ≈ 5-6 hours of bot time.
- Plan review: `09-build-ideas/review-lead-finder-fix.md`.

Run with: `Do the next unticked task in PLAN-lead-finder-fix.md, then tick it and stop.`
Check: `bash tooling/qa/check-lead-finder.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765 → Early Leads → Az

## How to try it (30 seconds)
1. Early Leads → Az: dozens of real new and recently sold apartment buildings, soonest openings on top.
2. Most rows show a software name (Yardi, Entrata...) or "not picked yet", and a phone number.
3. Click ✦ Deep dive on a Tempe lead: its real permit link, unit count and website.

## Tasks

### Part 1: Better tools
- [x] **F1 Remove SearXNG; Jina + Brave search.** Delete SearXNG from `fetch.py`, `tooling/searx_search.py`,
  `tooling/searxng/`, `tooling/LOCAL-ASSETS.md` and every SKILL.md/doc that mentions it. `WebHelper.search()`
  = Jina, then Brave only if Jina errors or returns nothing relevant; count Jina and Brave searches
  separately toward the 450 cap (and Brave toward its 800/month cap, tracked in
  `propertystack/runs/brave-usage.json`). Tests with fakes (Jina down → Brave; both down → clear error). Commit.
- [x] **F2 "Is this really about this building?" check.** A search result or page counts for a building
  only if its name (distinctive words) or street address appears in the title, URL or page text;
  listing sites (zillow, apartments.com, apartmentguide, apartmentratings, yelp, facebook, trulia,
  rent.com, rentcafe.com listing pages) are never the official website (but a rentcafe/securecafe
  link is Yardi evidence). Use it in `project_details`, `find_website`, `contact_scrape`. Fixture
  tests from real cases: "Marquee on 5th Tucson" must not match marqueesportsnetwork.com or
  themarqueestl.com; Bella Victoria must pick bellavictoria.com. Commit.
- [x] **F3 Find permit data everywhere.** `find_sources` asks, in order: ArcGIS Online search by place
  name (`https://www.arcgis.com/sharing/rest/search?q=title:permits "<place>"`), the city's ArcGIS hub
  search, the Socrata catalog, CKAN `package_search`. Find a city's ArcGIS hub from the ArcGIS Online result's owner org
  (`orgId` → its hub/maps site), never by guessing; none → skip that source. **Accept a dataset only after one real query
  returns permit-level rows (≥100 rows, an address field, dates in the last 24 months)** -- Phoenix's
  CKAN set was 22 rows of yearly totals. Accela/Tyler/SmartGov-only cities are marked "no free data"
  (no retries). Tests with saved real responses. Commit.

### Part 2: Arizona sources
- [x] **F4 Arizona permit recipes.** Save tested recipes (data files) for Phoenix, Mesa, Tempe,
  Scottsdale, Gilbert, Tucson, Maricopa County unincorporated and Peoria from the research file:
  endpoint, date field, multifamily filter, unit-count source (a field like Tempe's `HousingUnits`, or
  parsed from the description like Mesa's "(11) unit apartment", or looked up later), name keywords
  (Phoenix's APART/APT/MULTI/MF), leasing-date field if any (Tempe `COIssuedDate`). **Unit lookup order**
  when the layer has no unit field (Phoenix, Scottsdale, Gilbert, Maricopa County, Peoria, often
  Tucson): permit field → number in the permit text ("300-unit", "(11) unit") → the project's own
  site or news via Jina (F2 check) → county parcel record. **Still unknown (Drew 2026-09-14):** keep a
  clearly new multifamily project, show "Units: not public yet", rank it below projects with known
  units -- never drop it and never estimate. Each recipe gets a
  live self-test that returns ≥1 multifamily row. Commit.
- [x] **F5 Recently sold, from the county's sales file.** First open the zip's file-spec document and
  confirm which field marks apartment property (type or use code) and whether unit counts exist
  (if not, take units from the parcel file or the building site). County sales recipe (data): Maricopa County
  Assessor "Sales Affidavits" CSV joined to the parcel file (item ids in the research file) → apartment
  properties (multifamily use codes) with 20+ units sold in the last 24 months: address, buyer, seller,
  date, price. Acceptance: ≥10 real 20+ unit apartment sales in the last 24 months with buyer and
  date. Code stays generic (any county with a sales file + parcel file). Commit.
- [x] **F6 Answer key for Arizona.** Build `propertystack/answer-keys/az.json` by hand, independent of
  the tool: 15 real new or recently sold AZ apartment buildings (20+ units) **only from sources the
  tool doesn't read** -- news articles, developer press releases, apartment association new-community
  lists, building websites (never the city permit layers or the county sales file) -- each with its
  source link and source type; 5 of them with the
  software verified by hand from the building's own site (Marquee on 5th = Yardi, Bella Victoria =
  Yardi, plus 3 more, at least 1 non-Yardi if one can be found). Commit.

### Part 3: Software and phones that work
- [x] **F7 Software detection v2.** Official site (from F2) → plain fetch → crawl4ai render if no portal
  link found → match resident-login / pay-rent / apply links: Yardi `*.securecafe.com`, `*.rentcafe.com`;
  RealPage `*.onlinesite.realpage.com`, `loftliving.com`, `activebuilding.com`, `*.realpage.com`;
  Entrata `*.residentportal.com`; AppFolio `*.appfolio.com`; ResMan `*.myresman.com` (merge into
  `tooling/pms_detect.py`). Keep the double check. Test live on the 5 answer-key buildings: all 5
  correct. Commit.
- [x] **F8 Phones and owners.** Owner/developer from permit owner/builder fields (Scottsdale, Tempe) or
  the sales file's buyer; phone from the building's own contact page, then the owner/developer's site
  (found with Jina/Brave + the F2 check), read with Jina Reader or crawl4ai; `phonenumbers` pulls and
  de-duplicates, office lines above fax/cell. Never guess. Fixture tests + a live test on 3 answer-key
  buildings. Commit.
- [ ] **F9 Quality alarms.** In `run.py`: after the run, write `quality.json` -- % cities with a real
  source, % leads with units, website, software verdict, phone, and answer-key recall (share of key
  buildings found) and software accuracy. **Bar for a state:** answer-key recall ≥60%, software
  correct on ≥80% of key buildings; for **existing buildings (leasing or sold)**: website on ≥70%,
  a software verdict on ≥70%, phone on ≥50%; for **not-yet-built projects (permitted / under
  construction)**: software = "not picked yet" is correct, and a developer/owner name + office phone
  on ≥50%. Below the bar → the run
  is marked "failed quality" and is **not** built into the site. Tests. Commit.

### Part 4: Real runs
- [ ] **F10 Tempe test run.** Full chain on Tempe only (best data). Compare to the bar (answer-key part
  limited to Tempe buildings). If below: find the step at fault, fix it, rerun -- up to 2 fix rounds;
  still below → STUCK with a plain report of what's missing and why. Write the leads in plain words in
  the progress log. Commit.
- [ ] **F11 Full Arizona run.** First move `propertystack/data/az/` and `propertystack/runs/AZ/20260914-full/`
  to `propertystack/archive/az-run1/` so nothing from the junk run leaks in. New run id. Whole state in permit
  order until 150 projects or the 450-search cap, plus the county sales file. Must pass the bar
  (same 2-fix-rounds rule, then STUCK). Save recipes. Commit.
- [ ] **F12 Arizona on the site + chat.** Build the site and rebuild the chat (`bash tooling/dev.sh`)
  with the new AZ leads; run the Check and `tooling/qa/check-answers.sh`. Commit. Recap in plain words
  how many AZ leads, how many with software and phone, and the quality numbers.

## Later (not in this build -- Drew 2026-09-14: Arizona only, plan the rest after seeing it)
- **F13 New Mexico.** Discovery (F3) for its top permit cities (Albuquerque's ArcGIS layer has
  `NumberofUnits`; research file), county sales file if one exists (else news-based sales), a 10-building
  NM answer key, then a full run held to the same bar. Build into site + chat if it passes. Commit.
- **F14 Louisiana.** Same as F13 (New Orleans Socrata `rcm3-fn58`, Baton Rouge `7fq7-8j7r` --
  find the right multifamily filter). Commit.
- **F15 Next state near Texas.** Run discovery for Oklahoma, Colorado and Arkansas; pick the one with
  the most real permit sources; answer key + full run + same bar; build it in if it passes. Commit.
  Recap in plain words for Drew: leads per state, quality numbers, what's still missing.
