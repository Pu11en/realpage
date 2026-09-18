# PropertyStack — wireframe brief (v1)

Source: Drew + planning session 2026-09-10 (thread 1547545532241809478)
Fetched: 2026-09-10
Method: Q&A planning with Drew; decisions below are his
Confidence: high for decisions; lead scores use a first-draft formula

**What it is:** a dashboard showing the software stack behind every apartment
property in an area. Main story: "who's about to choose" (early leads), with a
full map of who runs what today underneath.

**How it runs:** a static site on Vercel. All data comes from files in the
repo, produced by local agent sessions using skills. Push to main → auto-deploy.
No backend, no live agent, no login. Nothing on the site writes data.
**Screens:** desktop first. The phone layout gets done automatically at the end.
**Style:** see `10-dashboard-wireframes/design-direction.md`.

## Decisions (Drew, 2026-09-10)
- Story B: "who's about to choose." Early signals in v1: upcoming buildings + recently sold
- Neutral product with a "View as" switch (RealPage / Yardi / Entrata)
- One Early Leads page ranked by a lead score; each lead has an agent-written "why" line with sources
- Under the Hood page shows how the agent works
- No Ask box; fixed pages only
- Manual local runs; "NEW since last run" badges come from diffing run files
- Name: PropertyStack
- Area for v1: Plano + Richardson (Collin County only)

## Global top bar (every page)
- Left: **PropertyStack** wordmark
- Tabs: **Early Leads** · **Master Table** · **Software Share** · **Under the Hood**
- Right: **Area** dropdown (Plano, Richardson) · **View as** switch
  (Neutral / RealPage / Yardi / Entrata) · "Last updated: <date>"
- **View as** effect everywhere: the chosen vendor's color is highlighted; rows
  already on that vendor are dimmed; everyone else is a "target"

## Page 1 — Early Leads (home page)
- Stat boxes (4): Leads · New this week · Units in play · Opening in next 12 mo
- Filters: signal type (Upcoming / Recently sold) · city · stage · units range ·
  current software · toggle "hide properties already on my software"
- Ranked list, one row per lead:
  Rank · **Score 0–100** (number + small bar) · Property/Project · City · Units ·
  **Signal pill** ("Upcoming · Permit issued" or "Sold · Mar 2026") ·
  **Current software** pill (or "Not chosen yet") ·
  **Why line** (one sentence written by the agent, with small source chips,
  e.g. [county record] [permit] [website]) · **NEW** badge if new since last run
- Row click → Property Detail

## Page 2 — Master Table (every apartment in the area)
- Stat boxes (4): Apartments · Total units · Software identified (% + count) · Top software
- Filters: search · city · software · year built · units
- Columns: Community · City · Units · Year built · Owner · Software (colored pill) ·
  Proof (link icon) · NEW badge
- Footer coverage funnel: In area 195 → Website found → Checked → Identified → Unknown (with reasons)
- Export CSV button · row click → Property Detail

## Page 3 — Software Share
- Two charts side by side: share by # properties · share by # units
- Table: Software · Properties · Units · % · Change since last run
- View as highlights the chosen vendor · click a vendor → Master Table filtered to it

## Page 4 — Property Detail (from any row)
- Header: name · address · city · units · year built · owner
- **Software card:** vendor pill · proof link · "checked <date>" · confidence (High/Med/Low)
- **Signals card:** for sold properties: sale date, new owner, previous owner.
  For upcoming buildings: stage timeline (Zoning filed → Approved → Permit → Construction → Leasing) with dates
- **Lead score card:** the score plus its breakdown (size · freshness · stage · current software), then the full "why" text
- **Sources list:** every link the data came from
- Website link · small static map pin

## Page 5 — Under the Hood (shows how the agent works)
- **Pipeline diagram** with live counts per step:
  find-apartments (195) → find-website → detect-software (34 identified) → build-table → leads
- **Run history table:** date · area · skills run · properties processed · % identified · cost ($) · duration · models used (cheap vs. expensive)
- **Accuracy card:** latest hand-check (e.g. "27/30 correct"), trend over runs
- **Review queue (read-only):** unknowns and low-confidence rows, with reason and suggested answer. Fixed in a local session, not on the site
- **Cost card:** cost per area, split by model

## Sample data for wireframes (real)
- Area: Plano + Richardson (Collin County): 195 apartments, 51,701 units
  (`raw/research-01/area-table-richardson-plano.csv`)
- Identified so far: Yardi 14 · RealPage 8 · Entrata 3 · Yotta 1
- Example rows: Legends at Chase Oaks · Plano · 346 units · 1996 · Yardi;
  Dorian · Plano · 398 units · 2007 · RealPage; The Emory · Plano · 270 · 2023 · Entrata
- Early Leads rows: real sample in `raw/research-01/early-leads-sample.csv` (19 leads: 11 upcoming projects + 8 recent sales, scored, with why lines)

## Not in v1
Ask box · map page · landlords page · alerts/digests · job-post and vendor-news signals · switch history
(see `09-build-ideas/later-value-layers.md`)
