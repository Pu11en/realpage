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
- [ ] **1.2 One lead format.** `lead-finder/record.py` + `docs/LEAD-FORMAT.md`: one record per
  project/building used by every part: area, city, name, address, lat/lon, units, **stage**
  (planned / permitted / under construction / leasing / sold), permit date, opening date (or blank),
  sale date + buyer, developer/owner, office phone, website, software (RealPage / competitor name /
  not picked / unknown), links (map, permit, agenda, news, website), sources (URL per fact), why.
  Save/load as JSON per step; a sample state area under `propertystack/data/_sample/` (fake, clearly
  marked, never shown as a real area) for later parts' tests. Tests. Commit.
- [ ] **1.3 Web helper.** `lead-finder/fetch.py` used by every part: search = SearXNG
  (`tooling/searx_search.py`) first, Jina only if SearXNG returns nothing or is down; page reads via
  crawl4ai, Scrapling if blocked, Playwright last; every page cached on disk (never read twice); 2 s
  between visits to one site; 3 blocks → site marked skipped with the reason; every search counted
  (Jina logged separately). Fixture tests (fake SearXNG down, cache hit, 3 blocks). Commit.
- [ ] **1.4 Run folder, resume, caps, state pick.** `propertystack/runs/<state>/<run-id>/` with one
  file per step per city; rerunning skips finished steps. State = fewest RealPage buildings among
  the 15 fastest-growing (client-map `counts.json`). Caps: stop at **150 projects or ~450 searches**;
  **<30 projects → roll into the next state**, which becomes its own area. Fixture tests. Commit.

### Part 2: Permits (new apartment projects)

- [ ] **2.1 Rank the state's cities (free).** `lead-finder-cities/`: Census place-level permits
  (5+ units, last 12-24 months) for any state; write `propertystack/data/<state-slug>/cities.json`
  (city, permits, RealPage count from client map). Fixture tests. Commit.
- [ ] **2.2 Permit recipes + catalog lookup.** `propertystack/recipes/*.json` format (by permit
  system -- Socrata / ArcGIS / Accela / EnerGov / Tyler -- or by city): how to query new
  multifamily permits, fields, date tested, how complete. `find-sources` first asks the free
  **Socrata and ArcGIS catalog APIs** for a city's permit dataset. Fixture tests. Commit.
- [ ] **2.3 `find-sources` fallback.** No catalog hit: search for the city's permit portal, identify
  the system, test on 5 permits, save the recipe; nothing online → city "skipped: no permits
  online". Fixture tests. Commit.
- [ ] **2.4 `find-upcoming` rebuilt for any city.** Replace the old Plano-only version: city + recipe
  → new apartment permits (permit issued → leasing). Keep only type/description apartment or
  multifamily, or 20+ units; unknown units kept for 2.5 to fill. Several permits for one project
  **merged into one record** with its permit link. Fixture tests. Commit.
- [ ] **2.5 `project-details` (new).** Clean addresses (usaddress + free Census batch geocoder) so
  merging is reliable. One web lookup per project: address, units, developer, opening date, news
  link, website. Never guess; still-unknown units → drop. Fixture tests. Commit.

### Part 3: Early signals (meetings, HUD loans, state awards)

- [ ] **3.1 HUD FHA loan list.** `lead-finder-hud/`: download HUD's free "FHA Multifamily Firm
  Commitments and Endorsements" spreadsheet (cache it); filter by state, 20+ units, last 36 months:
  221(d)(4) → new project (stage permitted), 223(f) → sold/refinanced building (stage sold, marked
  "HUD refi or sale"). Fixture tests. Commit.
- [ ] **3.2 State housing agency awards.** `lead-finder-awards/`: for any state, find its housing
  agency's tax-credit / bond award lists (NCSHA directory, Novogradac state pages), save a per-state
  recipe; read PDF or spreadsheet lists → projects with developer, units, city, award date (stage
  planned). Fixture tests. Commit.
- [ ] **3.3 Which meeting system does a city use?** `lead-finder-agendas/`: search the city's planning
  commission agenda page, match the address pattern (legistar.com, /AgendaCenter, granicus,
  primegov, civicclerk, boarddocs, escribemeetings, iqm2); cache per city. Fixture tests. Commit.
- [ ] **3.4 Legistar reader.** Free Legistar data service: last 12 months of Planning / Zoning /
  Council meetings, find items mentioning multifamily / apartments / "NNN units" / rezoning / site
  plan; token-required cities marked skipped. Fixture tests. Commit.
- [ ] **3.5 Other systems + PDFs.** civic-scraper for CivicPlus, Granicus, PrimeGov, CivicClerk; read
  only the agenda (never whole packets over a size cap) with PyMuPDF, OCR only for pages with no
  text. Fixture tests. Commit.
- [ ] **3.6 Agenda hits → Planned projects.** Keep an item only if it has an address or case number;
  pull name, address, developer, units, case number; one project per case (P&Z + council merged);
  stage "planned", agenda link. Fixture tests. Commit.

### Part 4: Software, sales, who to call, ranking

- [ ] **4.1 Software fingerprints.** `detect-software` gets a rules file in the Wappalyzer JSON
  format with **our own** rules (RealPage / OneSite / loftliving / activebuilding, Yardi RentCafe /
  securecafe, Entrata, AppFolio, ResMan, MRI, Knock, SightMap …), merged with `tooling/pms_detect.py`.
  Cheap page check first; full browser only if unclear. Any area (remove Plano paths). Fixture tests.
  Commit.
- [ ] **4.2 Double check + drop RealPage.** Before a RealPage or competitor verdict, a second check
  (another page on the site or the resident portal link) must agree, else "unknown". RealPage
  buildings dropped; others "on <competitor> today" / "not picked yet". Fixture tests. Commit.
- [ ] **4.3 `find-sales-news` (new).** GDELT (free news index) + SearXNG news: apartment sales in
  the state's cities, last 24 months → building, buyer, date, units, link (stage sold). Fixture
  tests. Commit.
- [ ] **4.4 Who to call, any area.** `find-website` + `contact-scrape` take any area: developer (or
  new owner) office phone + website; `phonenumbers` pulls and de-duplicates numbers, office lines
  above fax/cell; a named person only if a permit, agenda or news page names one. Fixture tests.
  Commit.
- [ ] **4.5 `score-leads`, any area.** Remove Plano bits. Order: soonest opening → more units → not
  picked above competitor; unknown opening ranked by permit date and shown "Opens: not public yet";
  **Planned below permitted**; one-line "why" per lead. Fixture tests. Commit.

### Part 5: Site and chat for any area

- [ ] **5.1 Build every area.** `site/data/build_data.py` builds each area folder under
  `propertystack/data/` from the part-1 lead format (sample area only when a test flag is set, never
  in the real build). Plano–Richardson unchanged. Tests. Commit.
- [ ] **5.2 Area buttons.** Early Leads: one button per area, each its own table; remove the
  sidebar area dropdown. Check passes. Commit.
- [ ] **5.3 City filter + labels.** State areas get a city filter above the table; rows show
  "Planned (not permitted yet)", "Opens: not public yet", "Sold <date>" and the why line. Commit.
- [ ] **5.4 Chat knows every area.** The chatbot loads every area's leads; `SOUL.md` stops naming one
  county; deep dives work for a new area (links incl. 📋 Agenda when present). Rebuild with
  `bash tooling/dev.sh`; run `tooling/qa/check-answers.sh`. Commit.

### Part 6: The real run

- [ ] **6.1 Wire the chain.** `lead-finder/run.py` runs every step in order (cities → sources →
  permits → details → early signals → sales → software → who to call → score), resumable, on
  the sample area end to end. Tests. Commit.
- [ ] **6.2 Small test run (~20 searches).** Whole chain on **one city** of the picked state,
  capped at 5 projects. Write the 5 leads in plain words in the progress log. If they look wrong
  (not apartments, made-up facts, RealPage buildings), fix the step at fault and rerun; then go on.
- [ ] **6.3 Full state run (~450 searches, pre-approved).** Whole state until 150
  projects or the cap (roll into next state if <30); save recipes; spot-check 10 software calls;
  log to `propertystack/runs/`. Commit.
- [ ] **6.4 Fill the site + chat.** Build the site and rebuild the chat with the new area; run the
  Check and `check-answers.sh`. Commit. Recap in plain words what is on the site now.
