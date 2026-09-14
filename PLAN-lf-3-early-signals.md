# PropertyStack lead finder, part 3: early signals (meetings, HUD loans, state awards)

Part of the lead finder. **Read the rules in `PLAN-lead-finder.md` first** (area-agnostic: no place
names in code; Plano is never rerun; never guess facts; SearXNG first, Jina fallback; localhost only,
no push). **NOT approved to run yet.** Starts after part 1 is merged; can run **at the same time as parts 2, 4 and 5**. Touches only its own skill folders.

Run with: `Do the next unticked task in PLAN-lf-3-early-signals.md, then tick it and stop.`
Check: `bash tooling/qa/check-lead-finder.sh`
Try: `bash tooling/dev.sh`
Open: (behind the scenes; results show on the site after part 6)

## How to try it (30 seconds)
1. Run the Check line: it passes.
2. A sample agenda with a "300-unit multifamily" zoning case becomes a "Planned (not permitted yet)" project with its agenda link.
3. A sample HUD loan file gives new-building projects (221(d)(4)) and likely-sold buildings (223(f)) for the sample state only.

## Tasks

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
