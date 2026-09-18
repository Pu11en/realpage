# Research run 01 — verify before we build (C1 Switch Radar, C3 fallback)

Source: planning session 2026-09-10
Fetched: 2026-09-10
Method: plan for a research session; nothing here is executed yet
Confidence: n/a (this is a spec)

Purpose: answer the questions that decide whether C1 (PMS Switch Radar) is
buildable and pitchable, cheaply, before any build work. Written so a cheaper
model can run it top to bottom without asking anything. Read
`brainstorm-2026-09-10-pitch-to-realpage.md` first for the why.

## Rules for the session

- Read-only toward third parties. No sign-ups, no forms, no posting.
- Polite crawling: ≤1 request/second per domain; Wayback CDX ≤1 request/2 s.
- Reuse the ladder in `task_plan.md` (WebFetch → Crawl4AI → Browser Use).
  Don't use Browser Use or paid APIs in this run — if a question needs them,
  write "needs Drew: <what, cost>" and move on.
- Every capture goes to `raw/research-01/` with the README header block.
  Each question's answer goes to `raw/research-01/R<n>-<slug>.md`.
- Stop a question when its time budget runs out; record what you have and
  mark it `INCONCLUSIVE`.
- End by filling in the results table at the bottom of this file and
  updating `task_plan.md`, `findings.md`, `progress.md`. Commit locally. Do
  not push unless Drew says so.

## Order and budgets (total ≈ 3.5 h)

R1 first because it can kill C1. If R1 = KILL, skip R2–R4 and run R6 fully.

### R1. Does anyone already sell property-level PMS data? (45 min) — KILL GATE
- Question: does RealPage, Yardi (Yardi Matrix), CoStar/Apartments.com, ALN
  Apartment Data, HelloData, Zonda, HG Insights, BuiltWith, or anyone else
  publicly offer "which property management software each apartment community
  uses" and/or switch history?
- Method: WebSearch + WebFetch of product pages. Queries to run at minimum:
  `"property management software" by property data multifamily`,
  `multifamily technographics PMS`, `"Yardi Matrix" property management software field`,
  `ALN apartment data "management software"`, `realpage market analytics data fields`,
  `apartment community "software used" dataset`, `BuiltWith rentcafe`,
  `BuiltWith "loftliving"`.
- Record for each vendor found: product name, URL, whether the PMS field is
  explicitly advertised (quote it), coverage claimed, price if public.
- **KILL** if a vendor publicly sells property-level PMS identification with
  history at national scale → C1 is dead as a novel product; move to R6.
- **PIVOT-SIGNAL** if a vendor has the PMS field but no history/switch events,
  or only via BuiltWith-style domain lists → C1 lives, differentiated on
  dated switch events + the "why" layer. Record the difference in one line.
- **PASS** if nothing found.

### R2. Fingerprint probe — can we tell a property's software from its website? (60 min)
- Pick 50 communities: 10 each from the portfolio pages of 5 management
  companies that list communities publicly (start with Greystar, Lincoln
  Property Co, Cortland, Camden, Avenue5 — swap any that don't list; record swaps).
  Prefer the target metro from R4 if already known; otherwise any US metro.
- For each: fetch the homepage; collect every outbound link whose text or URL
  matches pay / resident / portal / login / apply / lease. Save
  `raw/research-01/R2-links.json` (community, site URL, links).
- Classify with this starter table, extending it as you find patterns (log
  every new pattern with an example URL):

  | Pattern in link host/path | Vendor (hypothesis) |
  |---|---|
  | `loftliving.com`, `realpage.com`, `activebuilding.com`, `onlineleasing.realpage` | RealPage |
  | `rentcafe.com`, `yardi.com` | Yardi |
  | `residentportal.com`, `entrata.com` | Entrata |
  | `appfolio.com` | AppFolio |
  | `managebuilding.com` | Buildium |
  | `myresman.com`, `resman` | ResMan |
  | `mrisoftware.com`, `rentmanager.com` | MRI / Rent Manager |

- Ground truth: find ≥10 of the 50 whose PMS is stated publicly elsewhere
  (manager's press release "selects Entrata", vendor case study, job posting
  "must know OneSite"). Compare.
- **PASS** if ≥70% of the 50 classify to one vendor AND ground-truth agreement
  ≥9/10. **FIX** if 50–70% (note which link types were missing). **KILL** if <50%.
- Watch for: marketing-site vendor ≠ PMS vendor (e.g. a RealPage-built site
  pointing to a Yardi portal). Portal/pay-rent link wins over site builder;
  record the conflict cases.

### R3. Wayback history — can we date a switch? (45 min)
- For the same 50 homepages: query
  `http://web.archive.org/cdx/search/cdx?url=<domain>&output=json&from=2023&filter=statuscode:200&collapse=timestamp:6`
  (one row per month). Record snapshots per year.
- For 10 communities with ≥6 snapshots, fetch 3 snapshots (oldest, middle,
  newest), re-run the R2 classifier on each.
- Also record: in the old snapshots, is the pay-rent/portal link still on the
  homepage (vs. only on a subpage)? If it's mostly on subpages, say so — the
  build then has to fetch one subpage per snapshot, which doubles the backfill.
- **PASS** if ≥60% of the 50 have ≥4 snapshots/year AND you find at least one
  real vendor change (that's our first switch event — save the evidence URLs).
  **FIX** if coverage is fine but zero switches in 50 (then the demo needs a
  bigger sample; note it). **KILL** if <30% have usable history → C1 becomes
  "who runs what now" only; say so.

### R4. Where does a metro's full community list come from? (45 min)
- Candidate metros, in order: Austin, Dallas–Fort Worth, Phoenix, Seattle.
  (Texas = RealPage home turf and heavy multifamily; Phoenix = AZ AG suit;
  Seattle = local algorithmic-pricing ban → switching may be legally driven.)
- Evaluate free sources for the first metro, then stop if one passes:
  management-company portfolio pages (aggregate top 20 managers), HUD LIHTC
  database (public, addresses), city/county rental registries, OpenStreetMap
  `building=apartments` with `website=*`, Google search result counts. Paid
  (Google Places API, ALN, CoStar) → record price, mark "needs Drew".
- Estimate: how many communities (100+ units) exist in the metro (find a public
  figure) and how many a free source gives us with a website URL.
- **PASS** if a free source (or combination) gets ≥60% of the metro's 100+ unit
  communities with a website. **FIX** if only paid gets there — write the cost.
  Pick the metro; tiebreak = Austin.

### R5. Pitch path — how does this reach a human at RealPage? (30 min)
- RealPage partner/marketplace program: does one exist (e.g. RealPage
  Exchange / marketplace / "become a partner")? Requirements, public contact.
- Which roles would own this: market intelligence / analytics, sales strategy,
  customer success, corporate development. Find public names only from press
  releases, conference speaker lists, and realpage.com — **LinkedIn is
  Drew-initiated only; list "LinkedIn search to run: <query>" for Drew instead**.
- Events in the next 6 months where these people appear (NMHC OPTECH, AIM,
  NAA Apartmentalize, RealWorld user conference).
- Output: `raw/research-01/R5-pitch-path.md`.

### R6. C3 fallback check — affordable compliance (30 min; 60 if R1 = KILL)
- Does RealPage's affordable-housing compliance offering advertise an AI
  assistant or rules Q&A? (realpage.com affordable pages, Lumina AI pages.)
- Existing AI compliance assistants for LIHTC / HUD (name, URL, pricing).
- Are HUD Handbook 4350.3 and Section 42 guidance freely downloadable as
  text/PDF? (URLs.)
- Output: one line per finding plus a gut call: open / crowded.

## Results (fill in at the end of the run)

| # | Question | Result (PASS / FIX / KILL / INCONCLUSIVE) | One-line evidence | File |
|---|---|---|---|---|
| R1 | Existing property-level PMS data | | | |
| R2 | Fingerprint probe | | | |
| R3 | Wayback switch dating | | | |
| R4 | Metro community list | | | |
| R5 | Pitch path | | | |
| R6 | C3 compliance check | | | |

**Decision rule after the run:**
- R1 not KILL, R2 PASS/FIX, R3 not KILL, R4 PASS/FIX → C1 goes to build using
  `mvp-plan-switch-radar.md` (apply any FIX notes to it first, then re-run
  `/mvp-plan-review`).
- R1 KILL or R2 KILL → bring R6 to Drew; C3 gets its own MVP plan.
- Anything else → bring the table to Drew with a one-paragraph recommendation.
