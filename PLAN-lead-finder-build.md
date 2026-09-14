# PropertyStack lead finder: the whole build, start to finish

**One plan, run as one non-stop `/gowork` build** (Drew, 2026-09-13: "don't stop for anything, keep
going until everything we planned is done"). The rules are in `PLAN-lead-finder.md` -- read them
first (area-agnostic: no place names in code; Plano is never rerun; never guess facts; SearXNG
first, Jina fallback). Localhost only; never push.

**Pre-approved by Drew -- do not ask:** the searches in 6.2 and 6.3 up to the caps (SearXNG is free;
Jina only as fallback, inside the ~450 cap); downloading free public data (Census, HUD, state
housing agencies, city permit/agenda sites); deleting the 4 old Plano-only skills. **Never ask
Drew anything during this build.** If a choice comes up, pick the option that best fits the rules,
write it in the progress log, and keep going. If one source or city fails, skip it with a reason
and continue; only STUCK if the whole task truly can't be done.

Run with: `Do the next unticked task in PLAN-lead-finder-build.md, then tick it and stop.`
Check: `bash tooling/qa/check-lead-finder.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765 → Early Leads → the new state's button

## How to try it (30 seconds)
1. Early Leads: a row of area buttons; click the new state -- its own table, soonest openings on top.
2. Pick a city in the filter: only that city's leads; planned projects say "Planned (not permitted yet)".
3. Click ✦ Deep dive on the top lead: address, opening date and real links.

## Tasks

### Part 1: Shared base

- [x] **1.1 Skeleton + check + no-place-names test.** `propertystack/skills/lead-finder/`
  (`SKILL.md` describing the whole chain and its 6 parts; `run.py` stub). `tooling/qa/check-lead-finder.sh`
  runs every `tests/` under `propertystack/skills/lead-finder*/` and the other lead-finder skills,
  plus `check-panel.sh`, in under 2 minutes, no network. Test that **fails if any lead-finder step's
  code has a place name** (Plano, Richardson, Collin, Dallas, any US state or big-city literal).
  Delete the 4 old Plano-only skills (`find-apartments`, `find-sales`, `build-table`, `scout-areas`);
  Plano data files stay; check the site still builds. Commit.
- [x] **1.2 One lead format.** `lead-finder/record.py` + `docs/LEAD-FORMAT.md`: one record per
  project/building used by every part: area, city, name, address, lat/lon, units, **stage**
  (planned / permitted / under construction / leasing / sold), permit date, opening date (or blank),
  sale date + buyer, developer/owner, office phone, website, software (RealPage / competitor name /
  not picked / unknown), links (map, permit, agenda, news, website), sources (URL per fact), why.
  Save/load as JSON per step; a sample state area under `propertystack/data/_sample/` (fake, clearly
  marked, never shown as a real area) for later parts' tests. Also `merge.py`: one project per
  building across all sources -- same normalized address (usaddress), or geocodes within 75 m plus
  the same developer/name word; keep the most advanced stage (planned < permitted < under
  construction < leasing), keep every source and link; a planned project that gets a permit is
  upgraded, not duplicated. Tests with tricky pairs ("123 Main St" vs "123 Main Street Bldg B").
  Commit.
- [x] **1.3 Web helper.** `lead-finder/fetch.py` used by every part: search = SearXNG
  (`tooling/searx_search.py`) first, Jina only if SearXNG returns nothing or is down; page reads via
  crawl4ai, Scrapling if blocked, Playwright last; every page cached on disk (never read twice); 2 s
  between visits to one site; 3 blocks → site marked skipped with the reason; every search counted
  (Jina logged separately). Jina key from `/home/drewp/main-projects/realpage/.env` (`JINA_API_KEY`;
  never commit it). If SearXNG isn't running, start it with `docker compose -f
  tooling/searxng/docker-compose.yml up -d`. Page cache lives under `propertystack/runs/cache/`,
  which is **gitignored** (only result JSON is committed). Fixture tests (fake SearXNG down, cache
  hit, 3 blocks). Commit.
- [x] **1.4 Run folder, resume, caps, state pick.** `propertystack/runs/<state>/<run-id>/` with one
  file per step per city; rerunning skips finished steps. State = among the 15 states in
  `propertystack/data/client-map/targets.json` (already the 15 with most new apartment permits), the
  one with the lowest `total` in `client-map/counts.json` (a state missing there = 0); ties → more
  permits wins. Save the pick and the ordered backup list in the run folder. Caps: stop at **150 projects or ~450 searches**;
  **<30 projects → roll into the next state**, which becomes its own area. Fixture tests. Commit.
- [x] **2.1 Rank the state's cities (free).** `lead-finder-cities/`: Census Building Permits Survey
  **place-level** files (https://www2.census.gov/econ/bps/Place/ -- the regional monthly/annual
  place files; old download code is in git history at `propertystack/skills/scout-areas/census.py`,
  deleted in 1.1) -- 5+ unit permits, last 12-24 months, for any state; also add unincorporated
  county areas as "cities" when the county issues the permits; write `propertystack/data/<state-slug>/cities.json`
  (city, permits, RealPage count from client map). Fixture tests. Commit.
- [x] **2.2 Permit recipes + catalog lookup.** `propertystack/recipes/*.json` format (by permit
  system -- Socrata / ArcGIS / Accela / EnerGov / Tyler -- or by city): how to query new
  multifamily permits, fields, date tested, how complete. `find-sources` first asks the free
  **Socrata Discovery API** (`https://api.us.socrata.com/api/catalog/v1?q=building%20permits&search_context=<domain>`
  or `&q=<city> building permits`) and **ArcGIS Hub search**
  (`https://hub.arcgis.com/api/search/v1/collections/dataset/items?q=<city>%20building%20permits`)
  for a city's permit dataset; test the dataset really has recent multifamily permits before
  saving the recipe. Fixture tests. Commit.
- [x] **2.3 `find-sources` fallback.** No catalog hit: search for the city's permit portal, identify
  the system (Accela Citizen Access, Tyler EnerGov / CSS, OpenGov, CentralSquare, MyGovernmentOnline,
  or a city-published monthly permit report PDF/Excel -- reports count), test on 5 permits, save
  the recipe; use Scrapling/Playwright for search forms; nothing online → city "skipped: no permits
  online". Fixture tests. Commit.
- [x] **2.4 `find-upcoming` rebuilt for any city.** Replace the old Plano-only version: city + recipe
  → new apartment permits (permit issued → leasing). Stage from the permit: issued in the last 24
  months and no certificate of occupancy → "permitted"/"under construction" (inspections started);
  CO issued in the last 6 months → "leasing"; CO older → drop. Keep only type/description apartment or
  multifamily, or 20+ units; unknown units kept for 2.5 to fill. Several permits for one project
  **merged into one record** with its permit link. Fixture tests. Commit.
- [x] **2.5 `project-details` (new).** Clean addresses (usaddress + free Census batch geocoder) so
  merging is reliable. One web lookup per project: address, units, developer, opening date, news
  link, website. Never guess; still-unknown units → drop. Fixture tests. Commit.
- [x] **3.1 HUD FHA loan list.** `lead-finder-hud/`: download HUD's free "FHA Multifamily Firm
  Commitments and Endorsements" spreadsheet from https://www.hud.gov/hud-partners/multifamily-data
  (cache it; **print the real column names first** -- program codes may read "221(d)(4)", "221D4"
  or similar; match all forms); filter by state, 20+ units, last 36 months:
  221(d)(4) → new project (stage permitted), 223(f) → sold/refinanced building (stage sold, marked
  "HUD refi or sale"). Fixture tests. Commit.
- [x] **3.2 State housing agency awards.** `lead-finder-awards/`: for any state, find its housing
  agency's tax-credit / bond award lists (NCSHA directory, Novogradac state pages), save a per-state
  recipe; search `"<agency name> housing tax credit awards 2025"` / `2026` and `"bond" "awards"`; read PDF
  lists with pdfplumber (tables) or PyMuPDF, spreadsheets with openpyxl → projects with developer,
  units, city, award date (stage planned). Keep awards from the last 36 months, 20+ units, **new
  construction only** (drop "rehab"/"preservation" rows). No list found → state noted "no award
  list online" and move on. Fixture tests. Commit.
- [x] **3.3 Which meeting system does a city use?** `lead-finder-agendas/`: search the city's planning
  commission agenda page, match the address pattern (legistar.com, /AgendaCenter, granicus,
  primegov, civicclerk, boarddocs, escribemeetings, iqm2); cache per city. Fixture tests. Commit.
- [x] **3.4 Legistar reader.** Free Legistar data service (`https://webapi.legistar.com/v1/<client>/`
  where `<client>` is the city's `<client>.legistar.com` name; `bodies`, `events?$filter=EventDate ge
  datetime'YYYY-MM-DD'`, `events/<id>/eventitems`, `matters?$filter=substringof('multifamily',MatterTitle)`): last 12 months of Planning / Zoning /
  Council meetings, find items mentioning multifamily / apartments / "NNN units" / rezoning / site
  plan; token-required cities marked skipped. Fixture tests. Commit.
- [x] **3.5 Other systems + PDFs.** civic-scraper for CivicPlus, Granicus, PrimeGov, CivicClerk; read
  only the agenda (packets over 25 MB skipped; at most the 10 pages around a keyword hit) with PyMuPDF, OCR only for pages with no
  text. Fixture tests. Commit.
- [x] **3.6 Agenda hits → Planned projects.** Keep an item only if it has an address or case number;
  pull name, address, developer, units, case number; one project per case (P&Z + council merged);
  stage "planned", agenda link. Fixture tests. Commit.
- [x] **4.1 Software fingerprints.** `detect-software` gets a rules file in the Wappalyzer JSON
  format with **our own** rules (don't copy the GPL webappanalyzer files) (RealPage / OneSite / loftliving / activebuilding, Yardi RentCafe /
  securecafe, Entrata, AppFolio, ResMan, MRI, Knock, SightMap …), merged with `tooling/pms_detect.py`.
  Cheap page check first; full browser only if unclear. Any area (remove Plano paths). Fixture tests.
  Commit.
- [x] **4.2 Double check + drop RealPage.** Before a RealPage or competitor verdict, a second check
  (another page on the site or the resident portal link) must agree, else "unknown". RealPage
  buildings dropped; others "on <competitor> today" / "not picked yet". Fixture tests. Commit.
- [x] **4.3 `find-sales-news` (new).** SearXNG news search (`"<city>" apartments sold OR acquires OR
  acquisition units`) for the full 24 months, plus GDELT DOC API
  (`https://api.gdeltproject.org/api/v2/doc/doc?mode=artlist&format=json`) -- note GDELT DOC only
  covers the **last 3 months**, so it's a freshness add-on. Apartment sales in the state's cities,
  last 24 months, 20+ units → building, buyer, date, units, link (stage sold). Fixture
  tests. Commit.
- [x] **4.4 Who to call, any area.** `find-website` + `contact-scrape` take any area: developer (or
  new owner) office phone + website; `phonenumbers` pulls and de-duplicates numbers, office lines
  above fax/cell; a named person only if a permit, agenda or news page names one. Fixture tests.
  Commit.
- [x] **4.5 `score-leads`, any area.** Remove Plano bits. Order: soonest opening → more units → not
  picked above competitor; unknown opening ranked by permit date and shown "Opens: not public yet";
  order of groups: permitted / under construction / leasing first, then **sold** (newest sale first),
  then **planned** (soonest expected, then units); one-line "why" per lead. Fixture tests. Commit.
- [x] **5.1 Build every area.** `site/data/build_data.py` builds each area folder under
  `propertystack/data/` from the part-1 lead format (sample area only when a test flag is set, never
  in the real build). Plano–Richardson unchanged. Tests. Commit.
- [x] **5.2 Area buttons.** Early Leads: one button per area, each its own table; remove the
  sidebar area dropdown. Check passes. Commit.
- [x] **5.3 City filter + labels.** State areas get a city filter above the table; rows show
  "Planned (not permitted yet)", "Opens: not public yet", "Sold <date>" and the why line. Commit.
- [ ] **5.4 Chat knows every area.** The chatbot loads every area's leads; `SOUL.md` stops naming one
  county; deep dives work for a new area (links incl. 📋 Agenda when present). Rebuild with
  `bash tooling/dev.sh`; run `tooling/qa/check-answers.sh`. Commit.
- [ ] **6.1 Wire the chain.** `lead-finder/run.py` runs every step in order (cities → sources →
  permits → details → early signals → sales → **merge (1.2)** → software → who to call → score),
  resumable, on the sample area end to end. Page reading that needs judgment (news, agenda
  pages, project pages) is done by **this session**: the script writes a `to-read.jsonl` queue in the
  run folder, the session reads each item and writes the facts back (with the source URL), and the
  script continues. Everything else is plain code. Tests. Commit.
- [ ] **6.2 Small test run (~20 searches).** Whole chain on **one city** of the picked state,
  capped at 5 projects. Write the 5 leads in plain words in the progress log. If they look wrong
  (not apartments, made-up facts, RealPage buildings), fix the step at fault and rerun; then go on.
- [ ] **6.3 Full state run, part A (pre-approved).** Start the run in the background
  (`nohup … > propertystack/runs/<state>/<run-id>/log.txt`), cities in order; work the to-read queue
  as it fills; after ~45 minutes commit results so far (the run resumes). Caps for the whole run:
  150 projects or ~450 searches; roll into next state if <30.
- [ ] **6.4 Full state run, part B.** Resume the run and keep working the queue; commit. If the run
  already finished or hit a cap, just tick this.
- [ ] **6.5 Full state run, part C.** Same as part B.
- [ ] **6.6 Full state run, part D + finish.** Same as part B; when the run is finished: save
  recipes, spot-check 10 software calls by hand, and write in the progress log how many projects,
  searches (Jina vs free), cities skipped and why. Commit.
- [ ] **6.7 Fill the site + chat.** Build the site and rebuild the chat with the new area; run the
  Check and `check-answers.sh`. Commit. Recap in plain words what is on the site now.

### Part 2: Permits (new apartment projects)


### Part 3: Early signals (meetings, HUD loans, state awards)


### Part 4: Software, sales, who to call, ranking


### Part 5: Site and chat for any area


### Part 6: The real run


## 5.3 City filter + labels -- done

- The city filter above the table (`#f-city`) already existed generically in
  `site/index.html` since it's populated from whatever `data.leads` cities are
  present for any area, including state areas -- nothing to add there.
- What was actually missing: `site/data/build_data.py`'s `_area_lead_dict`
  (added in 5.1) never set a `signal` field for state-area leads, only
  `signalType` -- so `app.js`'s `signalHtml()` (which reads `l.signal`) would
  have rendered `undefined` for every state-area row the moment a real area
  existed. Added `_area_signal_text(record)`: "Planned (not permitted yet)"
  for planned-stage records; "Sold <date>" (or bare "Sold" if no sale date)
  for sold-stage; "Opens: <date>" for permitted/under-construction/leasing
  when `opening_date` is known, "Opens: not public yet" when it isn't --
  matching the plan's exact wording. Wired into `_area_lead_dict["signal"]`.
- The existing "why" line (`l.why`, from 4.5's `score_and_rank`) was already
  rendered per row; no change needed there.
- Tests: extended `propertystack/skills/lead-finder/tests/test_build_areas.py`
  with `test_area_signal_labels_planned_and_unknown_opening` (planned / no
  opening date / known opening date / sold-with-no-date cases) and a
  sold-signal assertion in the existing sample-area shape test.
- Checked: `bash tooling/qa/check-lead-finder.sh` -- lead-finder's tests now
  39 (was 34), every other lead-finder* dir and check-panel.sh unaffected and
  clean. Reran `python3 site/data/build_data.py` (real build, unaffected) and
  a one-off `LEAD_FINDER_BUILD_SAMPLE=1` build to confirm `_sample.json`'s
  leads now carry a real `signal` string per the new labels ("Opens: not
  public yet" / "Sold 2025-11-02"), then reran the real build and deleted the
  leftover `_sample.json` so the working tree stays on the real (non-sample)
  site state.
- Left open: no real state-area run exists yet (Part 6), so this can't be
  eyeballed in a live browser with real data -- verified via the `_sample`
  fixture area instead, same approach 5.1/5.2 used.
- Next task (5.4) makes the chatbot load every area's leads and stop naming
  one county in `SOUL.md`.
