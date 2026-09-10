# 6-upcoming extract notes (plano-richardson)

91 candidates gathered (12 legistar, 27 tabs, 52 news) -> 12 real projects extracted.

## Update 2026-09-10 — fixes from evals/review-weak-spots.md
Re-ran GATHER with 5 added queries (civicplus, Preston Road/Spring Creek unit counts, two
Glenville-specific queries) -> 102 candidates (12 legistar, 27 tabs, 63 news). Then:

- **Excluded `plano-aura-northline`.** Freshness re-check (new SKILL.md rule) confirmed via
  live search that Aura Northline is now an actively-leasing property (grand-opening-special
  listings on RentCafe/Apartments.com/Zillow/its own site). Its only source was a Feb 2024
  article projecting "completion early 2026" — stale by the time of this review (today is
  2026-09-10, past that projection). Was a false positive; removed.
- **Added `plano-351-unit-project-at-4701-w-park-blvd`** (research-01's "Preston Road
  Project"). Found by fetching the full (untrimmed) `content.civicplus.com` Development
  Review List asset live — the GATHER script's own civicplus query still only surfaced the
  first ~4000 chars (TRIM_CHARS) of this ~85,000-char document, so the entry itself wasn't
  in this run's candidates jsonl either; found by reading the source directly instead.
  Description: "351 multifamily residences" at 4701 W Park Blvd (Berkeley Square Addn, north
  side of Park Blvd, 275 ft west of Ohio Dr, Preston Road Overlay District), owner Berkeley
  Square (Edens) LLC, Project #PR2026-024 (Preliminary Replat applied 8/13/2026). No project
  brand name stated for the residential component — used the `<units>-unit project at
  <address>` fallback per SKILL.md. stage=zoning-filed (only a replat application on file, no
  P&Z hearing/approval yet).
- **Added `plano-304-unit-project-at-spring-creek-pkwy-k-ave`** (research-01's "Spring Creek
  Project"). Same civicplus document, same TRIM_CHARS limitation — this entry had already
  rolled off the live Aug-2026 snapshot of the review list by the time of this re-run
  (projects move through/off this rolling report), so it was confirmed via a live web search
  quoting the July 2, 2026 snapshot instead: "304 multifamily residence units" on 26.4 acres,
  north side of Spring Creek Pkwy, 375 ft east of K Ave, owner Plano Mall Owner LP, Project
  #RLP2026-010. No brand name stated; used the fallback naming rule. stage_date is the
  document date (2026-07-02), not a confirmed application date — flagged as lower-confidence
  than the other rows' dates.
- **Added `richardson-390-unit-project-at-2520-n-central-expressway`** (research-01's "The
  Glenville / Central Expressway"). This is a **different project** from `Glenville
  Independent Living` (TDLR, N Glenville Dr, opened 2024 — correctly excluded, see below):
  a five-story, 390-unit apartment building at 2520 N Central Expressway, developer JLB
  Partners, replacing an existing office building. Richardson City Council approved the
  rezoning at its Jan 8, 2024 meeting (communityimpact article published 2024-01-09,
  confirmed via live fetch); expected completion 2027. No project brand name stated in the
  source — used the fallback naming rule rather than research-01's "The Glenville" label, to
  avoid re-creating the name collision with the TDLR "Glenville Independent Living" project
  that caused this to be missed in the first place. stage=zoning-approved.

**TRIM_CHARS=4000 is a real limitation worth fixing in `run.py`** for long rolling documents
like the Plano Development Review List (~85,000 chars) — it truncates before reaching
alphabetically/positionally later project entries. Not fixed this session (found via manual
untrimmed fetch instead); flagging for a future GATHER change: either raise TRIM_CHARS for
`city`-type sources specifically, or chunk long civicplus documents into multiple candidates.

## Merges
- **Collin Creek Multifamily** (811 N Central Expressway, Plano): merged `Collin Creek
  Multifamily S1` (TABS2026023342, registered Jun 2026, completion Jul 2027) with
  `COLLIN CREEK MULTI-FAMILY S2 BUILDING (NORTH)` (TABS2022024873, same address, review
  complete, completion Dec 2025) — both are residential building phases of the same
  Centurion American redevelopment site. Kept S1 as source (more current filing, states
  project name + address). The separate `Collin Creek Mall` and `TMOBILE - Collin Creek
  Mall` TABS filings at the same address are retail/renovation, not merged (excluded below).
- **Polk St Multifamily** (110 E. Polk Street, Richardson): merged TABS `Polk St Multifamily`
  (TABS2025026678, registered Aug 2025, permit) with three news articles covering the same
  project's lifecycle — "Downtown Richardson redevelopment project to add 279 apartments"
  (zoning-approved), "279-unit Polk Street apartment complex to start construction in
  December" (early estimate), and "Developers break ground on 281-unit multifamily community"
  (under-construction, groundbreaking Apr 6 2026, final unit count 281). Kept the
  groundbreaking article as source (most advanced stage, states units + address); TABS owner
  "High Street DFW Development, Inc" and news developer "High Street Residential" are the
  same firm (name form differs by source, not treated as a mismatch).
- **The Parks at Legacy West** (StreetLights tower, 6501 Legacy Drive, Plano): merged
  dallasnews "New 22-story Plano apartment tower" (261 units, expected finish Feb 2029),
  candysdirt "Apartment Tower Construction to Gear Up" (Dec 2025, phase one of $102.8M),
  candysdirt "StreetLights Residential Bets on Older Affluent Renters" (Jul 2026, construction
  underway — kept as source, most recent + most descriptive), and communityimpact "5 recent
  permits filed in Plano" (confirms 261-unit building at 6501 Legacy Drive). Project's
  building-specific name ("The Parks at Legacy West") found in a photo credit line in the
  July 2026 candysdirt article; the broader redevelopment is branded "The Park at Legacy."
- **Legacy Arapaho** (250 E Arapaho Road, Richardson): merged TABS `Legacy Arapaho`
  (TABS2026022855, registered Jun 2026, states project name + address but no unit count) with
  communityimpact "443-unit apartment complex approved by Richardson City Council" (states
  units + address, developer Legacy Partners, but not the project's filed name). Kept the news
  article as source since it's the one with the unit count; TABS owner "Lucky Property Two
  LLC" is presumably the SPV Legacy Partners development entity (not independently confirmed).

## Exclusions (reason)
- `LEGACY/KINCAID MULTI-FAMILY TOWER` (7200 Dallas Parkway, Plano) — TDLR project closed Jan
  2019, opened/completed well before 2025.
- `Promontory on Preston` (4708 W Spring Creek Pkwy, Plano) — TDLR project closed Feb 2024,
  opened before 2025 (264 units).
- `Glenville Independent Living` (2600 N Glenville Dr, Richardson) — TDLR project closed May
  2024, opened before 2025. (Would otherwise be allowed — independent-living apartments.)
- `CUSTER @ 190 RICHARDSON MULTIFAMILY`, `CITYLINE PHASE II - BLOCK D` — TDLR closed 2019/2017,
  years before 2025.
- `Collin Creek Mall`, `TMOBILE - COLLIN CREEK MALL`, `Sysgration TI`, `Coca-Cola Plano TX
  Renovation`, `CityLine Market` (EV charger) — retail/office/industrial renovation, not
  multifamily.
- `Haggard Farm Tillage Offices` — office building, not residential (same broader Haggard Farm
  development as the apartment/townhome rows kept above, but this filing is non-residential).
- `Adler Warehouse`, `Auto Lube at 8330 S Polk Street`, `Coworking at Post`, `JLB - Grid III`
  (Stafford), `JLB Navhi Road` (Mansfield), `JLB Cesar Chavez` (Austin) — outside Plano/
  Richardson.
- Zabalist firm/owner/city directory pages (`WDG Architecture...`, `Haggard Enterprises LTD`
  owner page, `Corrigan TX Construction Projects`) — not project pages, index/noise.
- Legistar matters `ID=1537,1538,1539,1541,1542,1543,1545,1646,1648,1649,1650` — P&Z consent/
  public-hearing items with no residential signal in the title (minutes approvals, a shopping
  center site plan, an Oncor substation, unlabeled zoning-case public hearings with no name/
  address stated in the matter title itself).
- "East Plano development nixes 1.3M square feet of office for homes, apartments" and "New
  apartments, townhomes get green light from Plano commission" (Heritage Creekside district
  amendments) — describe a 156-acre mixed-use *district's* zoning capacity (2,342 units at
  full build-out across the whole district), not one identifiable building/project with an
  address. `The Buckley` (kept above) is the one specific HC building with enough detail to
  extract as a project.
- "State law affects Plano apartment growth and city decisions" — mentions "three planned
  multifamily developments under SB 840... 827 incoming units" but names no specific
  project/address; not enough to extract a row.
- "Richardson council approves higher maximum number of apartments in CityLine" — raises a
  62.5-acre district's apartment cap by 1,175 units; not one specific building/address.
- "Richland Park Apartments set to add 5 units in Richardson after council approval" — a
  5-unit addition to an *existing* community, not a new development; too minor to be a
  meaningful software-lead signal.
- "Plano officials to consider senior living development at Park Boulevard, Preston Road"
  (Watermere) — still at "call a public hearing" stage (not yet filed/approved), and described
  as a combined "independent living and active adult facility" (Watermere brand typically
  bundles assisted-living-adjacent services) — too ambiguous to confidently classify as the
  independent-living-apartments exception; no unit count given either. Flagged, not included.
- Several dallasnews/bizjournals/communityimpact URLs returned only nav/ad boilerplate (paywall
  or ad-interstitial blocked the article body even after a second direct fetch attempt):
  "Two affordable apartment developments clear hurdle in Plano" (2022), "High Street
  Residential plans Plano rental community" (2021), "Plano to consider apartments for land next
  to Liberty Mutual campus" (2024), "Lang Partners to bring 297 multifamily units to
  Richardson" (2022), "KDC may add more housing at CityLine" (2024), "Rosewood reveals plans
  for final Heritage Creekside phase in Plano" (2026), "Haggard Farm first phase kicks off in
  Plano" (2025, redundant with the kept Haggard Farm row anyway), "Big Plano mall
  redevelopment... The Bend" (2024), "Utah-based investor bringing 351-unit apartment
  community to Richardson" (2021), "The Shire at CityLine sells" (a sale, not upcoming supply
  — that's skill 5's domain), "What's Developing: Roanoke, Melissa, Arlington, Richardson"
  (2021, no Richardson content in the fetched excerpt). Several are also stale (pre-2025).
- "Plans for Plano apartments get thumbs down from council" (2019) — council rejected this
  proposal; not upcoming supply.
- Market-stat / non-project articles: "Dallas-Fort Worth multifamily market shifts inward",
  "Who owns most apartments in Dallas area?", "Arlington Leads Nation in Apartment Shrinkage",
  "Dallas Ranks No. 7 Among Nation's Largest Metros For New Housing Permits", "Dallas is The
  Most Expensive City For Apartment Renters" — market-wide statistics, not single projects.
- Out-of-area projects mentioned in news: "Park at Northpoint" (Dallas), "60-Foot-Tall
  Apartment Development" on Garland Road (Dallas/Lochwood), "Build-to-Rent in Justin... 23Springs
  in Uptown... Frisco" — outside Plano/Richardson.
- Non-project pages: plano.gov zoning ordinance/planning pages, communityimpact
  pagination/index pages (`?page=3`, `?page=6`, `/denton/development/`), "How Plano Apartment
  Dwellers Can Grade Their Building" (city inspection program, not a project), "Willow Bridge
  Added to DOJ's Lawsuit Against RealPage" (not a project).
- `beta2.communityimpact.com` URL for "Richland Park Apartments..." — domain didn't resolve via
  Jina; the working `communityimpact.com` copy of the same story was used instead to evaluate
  that project (see exclusion above — excluded on merits, not on fetch failure).

## Recall gaps (checked against research-01/R5-upcoming-projects.csv by name/address only, not copied)
- **Preston Road Project** (~351 units) and **Spring Creek Project** (~304 units) — both
  sourced there from a `content.civicplus.com` PDF asset (a city staff report), which this
  run's queries never surfaced. Not in the candidates jsonl at all — a GATHER recall gap, not
  an extraction miss. Add a civicplus/city-staff-report query for a future run.
  (The Sherman Street and 360-unit-downtown rows in this CSV are likely two of the *other*
  P&Z items from that same window, but couldn't be confirmed against the PDF.)
- **The Glenville** (390 units, 2520 N Central Expressway, Richardson, council-approved Jan
  2024) — distinct from the `Glenville Independent Living` TDLR filing this run found (161
  units, 2600 N Glenville Dr, excluded as opened 2024). This run's TDLR/news queries never
  surfaced the actual Central Expressway "Glenville" 390-unit project. Recall gap.
- **StreetLights Townhomes** (3 units, same site as The Parks at Legacy West) — mentioned in
  passing in the dallasnews tower article but not treated as its own row (3 units is
  immaterial and it's part of the same StreetLights filing/site as the kept tower row).
- Units unknown for `Collin Creek Multifamily`, `Haggard Farm`, `JLB West Cityline`,
  `Haggard Farm Townhomes` — no candidate document stated a unit count for these; contract
  requires units only if actually stated, so left blank rather than guessed.
