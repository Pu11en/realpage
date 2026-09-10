# Upcoming Apartment Projects - Data Sources & Automation Feasibility

## 1. Community Impact Plano & Richardson Editions

**Source:** https://communityimpact.com/

**Fetched:** 2026-09-10

**Method:** Web news aggregator covering Plano and Richardson development news; tracks zoning approvals, groundbreakings, construction updates.

**What it contains:** Articles on apartment zoning approvals, site plans, groundbreaking ceremonies, construction milestones. Covers projects from planning through lease-up phase.

**Stage it reveals:** Zoning/permit approval → construction start → lease-up/opening

**Machine-readable?** No (news articles, HTML only). No API or export.

**Update frequency:** 1-3 articles per week during active development seasons

**Verdict:** GOOD for weekly automation. Can RSS subscribe to Plano/Richardson development sections; track article publication dates. Human review required to filter for apartments vs. other development types.

---

## 2. Texas Department of Licensing and Regulation (TDLR) TABS Project Search

**Source:** https://www.tdlr.texas.gov/TABS/Search

**Fetched:** 2026-09-10

**Method:** Official Texas registration system for architectural barriers projects; includes new construction. Web interface searchable by city, project status, date ranges.

**What it contains:** Project ID, name, address, facility type, work scope, cost estimate, registered date, completion date, design firm, project owner. Shows registered projects at various completion stages.

**Stage it reveals:** Zoning/registration → review complete → inspection complete

**Machine-readable?** Limited. Web interface only; no API, no CSV export visible. URL-based search parameters may be programmatically exploitable. Results are printable/paginated HTML.

**Update frequency:** Real-time; new projects registered ongoing.

**Verdict:** GOOD for weekly automation. Can script URL queries by city + date filters to detect newly registered projects. Manual HTML parsing required; no structured data export. Covers Texas-wide compliance filings, so may include non-apartment projects.

---

## 3. City of Plano Planning & Zoning Commission Agendas

**Source:** https://www.plano.gov/1251/Planning-Zoning-Commission-Agendas

**Fetched:** 2026-09-10

**Method:** Official city agendas and meeting minutes from Planning & Zoning Commission (meets ~monthly). Agendas posted Friday before meeting. Minutes posted after meeting.

**What it contains:** Zoning case numbers, project descriptions, site plans, unit counts, developer names, recommended actions. Minutes record approvals/denials.

**Stage it reveals:** Zoning application → preliminary approval → final site plan approval

**Machine-readable?** No; PDF agendas and minutes. No API or data feed.

**Update frequency:** Monthly agendas posted; minutes follow meetings (typically 1-2 weeks after).

**Verdict:** GOOD for weekly automation. Calendar is predictable (recurring dates). Can check Friday before each meeting for new agenda PDFs; flag multifamily cases. Requires PDF text extraction.

---

## 4. City of Plano Development Review List

**Source:** https://content.civicplus.com/api/assets/ac54ba65-bc6a-4347-92d9-239d91767bd3 (PDF)

**Fetched:** 2026-09-10

**Method:** Official City Planning Department monthly development review snapshot. Available as PDF.

**What it contains:** Project status (submitted, under review, approved), address, PSP number, unit counts, site acreage, zoning, next scheduled review date. Covers apartments, retail, office, mixed-use.

**Stage it reveals:** Under review → approved → ready for permits

**Machine-readable?** PDF only; not consistently machine-readable. Monthly release.

**Update frequency:** Monthly (last checked July 2, 2026; likely updated first of each month).

**Verdict:** OK for weekly automation. Can check monthly for updated list; flag multifamily rows. PDF is not well-structured for scraping; manual column interpretation needed.

---

## 5. City of Richardson City Plan Commission Agendas & Minutes

**Source:** https://www.cor.net/government/boards-commissions-meetings/city-plan-commission

**Fetched:** 2026-09-10

**Method:** Official city agendas, calendar, meeting documents. Commission meets ~2x per month (1st and 3rd Mondays). Agendas posted by Friday before.

**What it contains:** Case numbers, applicant/developer names, location, project type (residential, commercial, etc.), zoning recommendations, council actions. Minutes record approvals and conditions.

**Stage it reveals:** Zoning application → preliminary approval → council vote → final approval

**Machine-readable?** PDF agendas; no API. Agendas follow predictable calendar.

**Update frequency:** Biweekly agendas; minutes follow meetings.

**Verdict:** GOOD for weekly automation. Predictable schedule (1st & 3rd Mondays). Can check Friday before meetings for agenda PDFs; extract multifamily cases. Requires PDF parsing.

---

## 6. City of Richardson Open Data Hub

**Source:** https://opendata-richardson.opendata.arcgis.com/

**Fetched:** 2026-09-10

**Method:** Official ArcGIS-based open data portal. Permits, GIS/planning data available as downloadable datasets.

**What it contains:** Permit applications (type, status, date filed, location), project GIS layers, zoning maps, development status.

**Stage it reveals:** Permits filed → under review → approved → construction

**Machine-readable?** Yes. ArcGIS API, GeoJSON, CSV download available for most datasets.

**Update frequency:** Real-time or near-real-time (depends on city data sync schedule; typically daily or weekly).

**Verdict:** EXCELLENT for weekly automation. ArcGIS API or CSV export can be queried programmatically. Filter by permit type (multifamily) and date range. Most reliable automated source identified.

---

## 7. TDLR TABS Project Search (Advanced)

**Source:** https://www.zabalist.com/projects (third-party aggregator of TDLR data)

**Fetched:** 2026-09-10

**Method:** Zabalist is a permit tracking/real estate intelligence site that indexes TDLR projects. Provides structured project cards with status, timeline, cost, address.

**What it contains:** Project name, address, units (when available), estimated cost, expected completion date, TDLR registration number. Filterable by city, project type, status.

**Stage it reveals:** Registered → under construction → completed

**Machine-readable?** Partial. Project pages are HTML; detailed info in structured format. No documented API. May be scrapeable.

**Update frequency:** Updates when TDLR database updates (real-time).

**Verdict:** GOOD for weekly automation. Cleaner interface than raw TDLR; easier to filter and browse. Can query by city and date. Third-party service (may have access restrictions).

---

## 8. Dallas Morning News & Dallas Business Journal Real Estate Coverage

**Source:** https://www.dallasnews.com/business/real-estate/ + https://www.bizjournals.com/dallas/

**Fetched:** 2026-09-10

**Method:** Traditional business news outlets. Dallas Morning News covers major metro developments; DBJ focuses on commercial/real estate deals. Search archives or subscribe to real estate news feeds.

**What it contains:** Press releases, deal announcements, groundbreaking photos, completion announcements, developer profiles, capital raises, financing details.

**Stage it reveals:** Deal announced → zoning approved → groundbreaking → lease-up → opening

**Machine-readable?** No native API. HTML articles; RSS feeds available for selected sections.

**Update frequency:** 1-2 major development articles per week during market activity.

**Verdict:** OK for weekly automation. RSS or email subscriptions available. Requires keyword filtering ("apartment", "multifamily", "Plano", "Richardson"). Broader coverage; lower signal-to-noise ratio for Plano/Richardson specifics.

---

## 9. Multi-Housing News

**Source:** https://www.multihousingnews.com/

**Fetched:** 2026-09-10

**Method:** Industry news site focused exclusively on multifamily development. Articles cover deals, groundbreakings, openings, market analysis.

**What it contains:** Developer names, unit counts, addresses, financing details, opening dates, rental rates, amenities. Very relevant to apartment tracking.

**Stage it reveals:** Deal → construction → opening/lease-up

**Machine-readable?** No API. HTML articles; can RSS subscribe.

**Update frequency:** 1-2 DFW multifamily articles per week.

**Verdict:** GOOD for weekly automation via RSS. High signal (apartments only). Low noise. Requires RSS parsing + keyword filtering for Plano/Richardson.

---

## Summary: Best Sources for Weekly Automation

**Tier 1 - Highly Recommended:**

1. **City of Richardson Open Data Hub (opendata-richardson.opendata.arcgis.com)** — ArcGIS API or CSV export; filterable by permit type and date. Most reliable, machine-readable, near-real-time.

2. **TDLR TABS Search + Zabalist (zabalist.com/projects)** — Structured project data, filterable by city; can script queries and parse results. Covers statewide registration; reliable for early-stage projects.

3. **Community Impact RSS (communityimpact.com)** — Weekly Plano/Richardson development articles; high relevance; requires keyword filtering but covers zoning through opening.

**Tier 2 - Secondary/Supplementary:**

4. **Plano Planning & Zoning Commission Agendas** — Official, predictable schedule; requires PDF parsing but authoritative.

5. **Richardson City Plan Commission Agendas** — Same as Plano; biweekly schedule.

6. **Multi-Housing News RSS** — Industry focus; low noise; supplement with geography filtering.

---

## Recommended Weekly Monitoring Stack

**Primary (Automated):**
- Query Richardson Open Data API for permits filed in past 7 days (filter: multifamily/residential)
- Query TDLR TABS for projects registered in past 7 days, city = Plano or Richardson
- Pull Community Impact RSS; flag articles with "apartment", "multifamily", "rezoning", "groundbreaking"

**Secondary (Manual Review):**
- Check Plano Planning & Zoning Commission agenda every Friday (before monthly/biweekly meetings)
- Check Richardson City Plan Commission agenda every Friday (before 1st & 3rd Monday meetings)
- Scan Plano Development Review List (PDF) first of each month for new projects under review

**Tertiary (Passive):**
- Subscribe to Multi-Housing News RSS; filter for Dallas-Fort Worth multifamily articles

---

## Caveats & Limitations

- **TDLR TABS** covers compliance/registration but may include non-apartment building types (office, retail, etc.).
- **Richardson Open Data** is the strongest automated source but requires API familiarity or CSV parsing.
- **Plano permit data** is less centralized; PDFs require OCR/text extraction for automation.
- **Community Impact** and news sources require keyword filtering to isolate Plano/Richardson apartments.
- **Leasing/opening announcements** often lag construction completion by weeks; RSS feeds not ideal for final "now leasing" stage.
