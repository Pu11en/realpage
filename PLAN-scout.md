# PropertyStack: the scout (find untapped Sun Belt areas)

Written 2026-09-12 (sell-plan Q3, Q4, Q5, H3, H4). Runs on **Drew's computer only** (local
harness), never in the chat agent. Scores ~25 Sun Belt metros (TX, FL, AZ, the Carolinas, plus
mid-size like Tucson, Boise, Greenville), **excluding the Dallas–Fort Worth area** (RealPage's
home turf), and writes 3–5 area cards Drew picks from. Local only; no push.

Score per metro, three parts (0–100 each) + a plain-English "why this city":
1. **Growth + weakness**: apartment stock and new multifamily units permitted (Census Building
   Permits Survey, free), renter households (Census ACS, free), and **RealPage share** in a
   sample of ~25 apartment websites (existing detector).
2. **Churn**: count of recent apartment sales / management changes found in news (last 24 months).
3. **Competitor pain**: Yardi/Entrata share in the sample + resident/manager complaints about
   portals and payments for that metro (Reddit tool + web search).

Tools: **crawl4ai** at `http://localhost:11235` (free, local) for reading pages; Jina **only for
search**, hard cap **1,500 searches per run** (stop and report what finished);
`tooling/reddit_search.py` (read-only); `tooling/pms_detect.py` vendor rules.

Run with: `Do the next unticked task in PLAN-scout.md, then tick it and stop.`
Check: `python3 -m pytest -q propertystack/skills/scout-areas/`
Try: `python3 propertystack/skills/scout-areas/run.py --metros tucson-az,boise-id --limit-searches 120`
Open: http://localhost:8765/map.html (scout markers) · cards in `propertystack/data/scout/<date>/cards.md`

## How to try it (30 seconds)
1. Run the Try command (2 metros, small cap): it prints progress per metro and the search count.
2. Open `cards.md` output: each metro has three part-scores, a short reason and source links.
3. Open the map: those metros show a "researching/scouted" marker.

## Tasks

- [x] **S1 Skeleton + tests.** `propertystack/skills/scout-areas/` with `SKILL.md` (contract:
  inputs, outputs, cap, tools) and `run.py` stub; `metros.csv` (~25 rows: slug, name, state,
  CBSA code, lat, lon; no DFW). Tests with **saved fixtures only** (no network): scoring math,
  cap stops the run cleanly, cards render. Tests fail first, commit.
- [x] **S2 Census data (free).** Per metro: new multifamily (5+ units) permitted last 12 months
  from the Census BPS metro files, renter households from ACS (api.census.gov, no key needed at
  this volume). Cache raw downloads under `propertystack/data/raw/census/`. Tests pass.
- [x] **S3 RealPage share sample (💲 search).** Per metro: search for apartment community sites
  (~25 per metro, skip big listing portals), fetch with crawl4ai, classify vendor with the
  `pms_detect.py` rules. Output `sample.csv` per metro with proof URLs. Counts searches; obeys cap.
- [x] **S4 Churn + pain (💲 search).** News search for apartment sales / new management in the
  metro (last 24 months), keep items with URL + date; Reddit tool + search for portal/payment
  complaints naming Yardi/Entrata/RealPage and the city. Save evidence JSON per metro.
- [ ] **S5 Score + cards + map markers.** `run.py` combines the three part-scores + total into
  `propertystack/data/scout/<date>/areas.json` (numbers + evidence links only, no prose). Then
  **this local session (Claude) reads areas.json + the evidence files and writes `cards.md`**
  (top 5 first: city, scores, a 3-line "why this city" argument citing the evidence links). No
  extra API model for the reasoning. Also add/refresh `kind: "scout"` markers in `site/data/reach.json`. Log the run
  to `propertystack/runs/`.
- [ ] **S6 Full run (💲 up to 1,500 searches).** Run all ~25 metros. Report to Drew in plain
  words: the top 5 cards and what each costs to build next. Drew picks the area for
  PLAN-new-area.md.
