# PropertyStack: build a brand-new area end to end

Written 2026-09-12 (sell-plan Q3, H5). **Blocked until Drew picks an area from the scout's
cards** (PLAN-scout.md S6); write the pick into the line below before starting.
Area: `<slug>` — counties: `<list>` — picked on `<date>`.

Builds every apartment building (20+ units) in the area, its website and software, plus sales
and new builds where the county puts them online, then its Early Leads, and publishes it to the
site and the chat. Where records aren't online: publish anyway with a clear "not available here"
note and rank on what we have. Size cap **400 buildings** (raise only if Drew says). Localhost
only; no push.

Run with: `Do the next unticked task in PLAN-new-area.md, then tick it and stop.`
Check: `python3 -m pytest -q propertystack/ && bash tooling/qa/check-panel.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765 → area picker → the new area's Early Leads

## How to try it (30 seconds)
1. Open Early Leads and switch the area picker to the new area: a ranked list appears.
2. Click Deep dive on the top lead: the chat opens with it filled in; ask it; sources point
   to the new area's data.
3. Ask the chat "How many buildings in <new area> run RealPage?": it answers from the new data.

## Tasks

- [ ] **N1 Area config + run-area.** `propertystack/areas/<slug>.json` (name, counties, cities,
  sources per step, cap) and `propertystack/skills/run-area/` (`SKILL.md` + `run.py`): runs the
  finder chain in order for one area, stops at the cap, prints progress, skips steps whose source
  is `"none"` and writes that into `data/<slug>/coverage.json`. Tests with a fake area. Commit.
- [ ] **N2 County buildings source.** Research the picked county's appraisal district data
  (API or bulk file; `find-apartments/run_dallas.py` is the bulk-file example). Add an adapter so
  `find-apartments --area <slug>` lists every 20+ unit apartment property. Record the source
  URL + date in `propertystack/areas/<slug>.json`.
- [ ] **N3 Sales + new builds sources.** Same county: deed/owner-change data for find-sales and
  city/county zoning or permit sources for find-upcoming. If none online, set `"none"` with a
  one-line reason (H5). Don't guess.
- [ ] **N4 Run it (💲 ~2–4 Jina calls per building).** `run-area --area <slug>`: websites,
  software, sales, upcoming, contacts, score-leads. Spot-check 10 software calls by opening their
  proof URLs. Log the run.
- [ ] **N5 Site: area picker.** `site/data/build_data.py` builds every area under
  `propertystack/data/` (not just plano-richardson) into per-area JSON; an area picker on Early
  Leads, Software Share and building pages; the "not available here" note where coverage says
  so. Existing Plano–Richardson views unchanged by default.
- [ ] **N6 Chat reads every area.** Chatbot image copies all areas; the plugin loads each area's
  CSVs with an `area` column (or per-area tables) and `ps_schema` lists them. Rebuild locally, ask
  one question about the new area and one about Plano: both answered with sources. Then tell
  Drew in plain words it's ready to try.
