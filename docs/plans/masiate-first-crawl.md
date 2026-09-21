# Masiate: First Lead Collection Plan

Check: `git diff --check`

This check validates this planning change only, not a scraper or live data.
Status: planning, 2026-09-20. No collection job, paid service, outreach or app build has started.

**Updated deliverable:** Drew now wants a deeply researched PDF of the top
properties, supported by the agent, rather than a PDF containing every lead.
Collect broadly, then rank and investigate the best candidates in more detail.
Agent follow-up stays in saved chats and does not change the PDF; separate
per-lead notes are canceled. This supersedes earlier complete-report wording
below. See [current decisions](masiate-decisions.md) for the authoritative scope.

## 1. What We Are Collecting

**Agreed:** a regular public section inside CraneSignal, shaped around Masiate Construction's work, with the same information available to the existing agent. This is not a separate app or a private customer area.

**The first outcome:** a broad, dated list of local projects that might need Masiate, with the evidence and the right business to approach. A permit is a reason to investigate, not proof that a job is still available.

[Masiate's website](https://masiateconstruction.com/) describes residential and commercial remodeling, custom homes, fencing, flooring, roofing, painting, concrete, siding, plumbing and lighting. Capture prospects across those services; rank them afterward instead of throwing away everything outside one trade. Actual capacity, minimum job size and licensed-trade arrangements are not yet confirmed.

### Area and dates

- **Area confirmed:** wider Brazos Valley: Brazos, Robertson, Burleson, Grimes, Leon, Madison and Washington counties. The founder's Hearne background does not establish the company's current base or driving limit.
- Cover all seven counties in the source inventory, including relevant city and unincorporated-area records. Verify each city's sources separately; do not assume a county feed covers city permits. Most source checks below currently concern Brazos and Hearne; the remaining jurisdictions still need discovery.
- First pass: the latest **90 days** of permits and business-opening signals, plus all currently open matching bids and currently pending planning projects.
- Backfill permits and registrations to **12 months**, and planning/development records to **24 months**, checking which older projects are still active. These are proposed collection windows, not claims about available archives.
- Keep earlier records as history, with their real dates. Do not label an old permit as new because the scraper just found it.
- Broad collection means residential, commercial, multifamily, renovations, additions, pools and related work. No apartment-only keywords or $3 million minimum.
- Proposed update rhythm after the initial run: daily checks for changing permits/bids, weekly agendas/development lists, and appraisal refreshes when new files are released. Scheduling is a later implementation step.

## 2. Where The Leads Come From

The following pages were inspected on 2026-09-20. **A source page being found does not mean its full scraper works.** Access, individual records and pagination still need source-by-source checks.

### First: construction and renovation records

- **College Station building permits:** [weekly issued-permit page](https://www.cstx.gov/your-government/departments/planning-development-services-department/building-permits-issued/). Look for houses, additions, remodels, commercial work and pools. The city confirms weekly updates; the current document list did not appear in the text-only response. Browser inspection of its file loader is the next access test.
- **College Station development plans:** [weekly new-development page](https://www.cstx.gov/your-government/departments/planning-development-services-department/new-development-list/). Earlier leads for concrete, framing and future building work. The city says drawings are available for some projects. Capture the actual application, address, applicant and stage, not just a monthly total.
- **Bryan permits:** [monthly reports](https://www.bryantx.gov/development-services/monthly-building-reports/) identify activity, but the [August 2026 PDF](https://media-002-us.cdn.govstack.com/bryantx-004-us/media/ngpoiwol/august-2026-building-report.pdf) contains totals, not individual addresses: 51 new single-family permits and 9 pool permits that month. Use these as a coverage cross-check only. Test public record search through the [official permitting route](https://www.bryantx.gov/development-services/online-permitting/); if individual records are unavailable, prepare a request for the existing electronic permit register. Do not turn summary counts into invented leads.
- **Bryan early plans:** the [Site Development Review archive](https://docs.bryantx.gov/planning_development/SDRC/2026%20SDRC/) has dated agendas and project attachments. Extract site plans, subdivisions, renovations and changes of use. Repeated hearings should update one project, not create duplicate leads. City case staff and engineers are not automatically the people hiring Masiate.
- **Hearne and other selected towns:** [Hearne's agenda center](https://www.cityofhearne.org/AgendaCenter) and [planning department](https://www.cityofhearne.org/217/Planning-and-Development) are confirmed starting points. A downloadable permit register has not been verified. Inspect the agenda files and request an existing permit export where needed; apply this same discovery step to each additional city and unincorporated county area.
- **Texas project registrations, TDLR TABS:** the [search page](https://www.tdlr.texas.gov/tabs/search) exposes county, city and registration-date filters. Use those filters and all relevant work types, including renovations/additions, then fetch each returned project's details. Verify the current search request and completeness before a run; do not guess sequential project IDs across Texas. TABS is complementary to local residential permits, not a replacement for them.

### Second: requests for work and upcoming openings

- **Public bids:** [College Station's bid page](https://www.cstx.gov/business-development/bid-opportunities/) links to the Brazos Valley e-Marketplace used by several local agencies. Look for fencing, painting, roofing, flooring, concrete and building repairs. Keep deadlines, addenda, site visits and eligibility requirements. A matching open bid is stronger evidence of available work than a permit. Some documents require supplier registration; record that dependency without signing Masiate up automatically. School district and university purchasing sources are expansion candidates needing their own access checks.
- **Construction stormwater records:** use [TCEQ Central Registry](https://www.tceq.texas.gov/permitting/central_registry) and its linked records for local construction authorizations. Confirm the construction-program filter and site-level detail route first. Match site/operator details to existing projects; do not assume the operator is the builder or that every small project appears here.
- **Restaurants and shops opening:** [TABC's instructions](https://www.tabc.texas.gov/static/sites/default/files/2022-10/public-inquiry-instructions-applications.pdf) describe county/city-filtered pending original applications with downloadable reports. Verify the current export, distinguish a new application from a renewal, and match it to building work before calling it a renovation lead.
- **New business locations:** the [Comptroller data catalog](https://comptroller.texas.gov/transparency/open-data/search-datasets/) includes sales-tax locations. Use local location records and meaningful opening dates where available, excluding irrelevant online/home-office registrations. Its [new-permit files](https://comptroller.texas.gov/data/openrec/requests/taxfiles.php) use an account-based download route; mark that separately from public datasets. Registration alone does not prove construction is needed.
- **Health permits, occupancy and change-of-tenant records:** investigate these after core construction sources. [Brazos County's food-establishment guidance](https://health.brazoscountytx.gov/wp-content/uploads/2025/11/New-Establishment-Info_0-accessible.pdf) confirms a plans/permit process, but a usable public record export is not yet verified. An already-open business is generally a later-stage prospect, not proof of an unfinished build-out.

### Third: identify owners and repeat buyers

- **Property matching:** [Brazos CAD's certified downloads](https://brazoscad.org/certified-data-downloads/) provide ZIP files and a layout reference; [Robertson CAD](https://robertsoncad.com/) links to property search. Use parcel IDs, addresses and owner entities to clarify projects. Verify Robertson bulk access separately. Annual appraisal data can lag ownership changes.
- **Ownership changes:** county deed records are an optional follow-up for an already promising property, with access still to be checked. Buying property alone is a weak remodeling signal. Do not collect the entire county merely to pad the lead count.
- **Builders, pool companies, developers and property managers:** take organizations named on projects, then check their own business websites for trade contacts, supplier pages and current projects. Keep this as a repeat-buyer list linked to actual projects, not an extra count of project leads.
- **Lower-priority repair signals:** public code-repair records or official storm reports may suggest further investigation. Neither proves damage to a particular roof or intent to buy. These require separate discovery and fit checks; exclude personal court/distress filings and unrelated oil, medical or license lists from this construction run.

## 3. Tools And Collection Order

**Use the existing Python project and proven readers, with one adapter per source.** An adapter is simply the piece that knows how to read one website's format.

### Tools selected for the plan

- Start with official CSV, JSON, ZIP or spreadsheet downloads and direct requests using the existing Python HTTP approach. This is easier to count, resume and verify than clicking every page. [Python HTTP documentation](https://docs.python.org/3/library/urllib.request.html).
- Use the existing HTML collectors for ordinary pages. Use [Playwright](https://playwright.dev/python/docs/network) when a public document list or search form needs a browser; inspect its normal network requests before deciding whether direct downloads are possible.
- Use `pdftotext` for ordinary PDF text and [pdfplumber](https://github.com/jsvine/pdfplumber) for tables, keeping page numbers. Scanned documents need a separate OCR check; save uncertain readings for review.
- Reuse existing Crawl4AI/Scrapling helpers only where their output is suitable. Their presence in the repository is not proof they work on these local sites. Do not cycle tools to defeat an access restriction.
- Prefer deterministic field extraction. Any later model-assisted extraction must retain the supporting passage, label uncertainty and have a separately agreed usage limit. No paid model/search run is authorized by this plan.
- Use web search to locate official sources and fill gaps about a specific business; it is not a complete permit database.

### Existing code worth reusing, with limits

- `propertystack/skills/lead-finder-tabs/tabs.py` and `propertystack/recipes/tx/tabs.json`: search/detail parsing exists, but the recipe currently requires apartment keywords, new construction and at least $3 million. Add a Masiate-specific profile instead of changing the existing apartment product's filters.
- The TABS code currently hides some search/detail errors and can infer construction from an estimated start date. The new collection must report partial failures and keep an estimated date distinct from verified work on site.
- `lead-finder-permits`, `lead-finder-agendas`, `lead-finder-civic`, `lead-finder-contact` and `lead-finder/fetch.py`: reusable patterns for collection, contacts, caching and pacing. Each needs local fixtures and a real access check before being described as ready.
- `lead-finder/record.py`: existing records focus on apartment leads, and address normalization removes suites/building labels. A shop renovation must retain its unit and project phase so separate jobs are not merged together.

### Proposed run sequence

1. Inventory every selected city/county and source: exact URL, type of records, available dates, access requirements and whether it contains individual projects or only totals.
2. Read a few real records from each accessible source. Save the original response and prove the parser extracts the same values. If it fails, mark that source as blocked or needing work and continue other sources.
3. Collect recent local permits, TABS records, early plans and open bids. Follow every results page within the chosen area/date range, recording how far the run got.
4. Backfill the agreed history, then add TCEQ and business-opening signals. Expand city-by-city after the first sources are proven.
5. Match projects to properties and businesses; add public business contacts and useful trade tags.
6. Remove duplicate appearances, check status/dates, review a sample and produce the public/agent-ready dataset plus a coverage report.

### Reliable running

- Save progress after every page/file, with a run ID, source URL, fetch time, original bytes, content hash and parser version. Resume failed sources without downloading everything again.
- Start with one request at a time per host and at least two seconds between requests, or a slower published limit. Respect retry instructions; pause repeated failures. Separate hosts can be worked on independently.
- Set a visible page/time limit per source before the run. Reaching a limit means **partial**, not complete or no results. Do not promise a fixed number of leads before seeing the records.
- Handle maintenance, empty results, unexpected HTML and login pages as different outcomes. Never treat an error page as a valid fixture.
- Refresh with overlapping date windows and compare document hashes to catch corrections. Track missing/withdrawn records without silently deleting history.
- Where exports are unavailable, draft a request for existing electronic records, including IDs, dates, addresses, work descriptions, status and applicant/contractor fields already held. Sending a request or creating an account is a separate action.

## 4. What Counts As A Useful Lead

**Keep these three things separate:** the project, the organization to approach, and whether work is actually available.

### Information to keep

- Stable project ID; source-specific record IDs; city/county; full address including suite; parcel ID and map location when supported.
- Description, property type, work type, stated cost and size when present. Whole-project cost is not Masiate's potential contract value.
- Application, issue, expected start, expected completion and actual status dates as separate fields; preserve the source's date precision.
- Owner, developer, applicant, architect and main contractor as distinct roles. A city planner or accessibility reviewer is not a buyer by default.
- Relevant Masiate trades, a short reason for each match, and whether the need is explicitly stated or inferred.
- Public business contact and the page supporting it, when found. Missing means missing; do not invent email addresses or relabel an owner's personal phone as an office number.
- Record URL, document/page reference, supporting text, source publication date, collection time and last successful check.
- Lead status: **open bid**, **possible subcontract**, **early project to follow**, **repeat-buyer prospect**, **closed/awarded**, or **needs checking**. These labels must be driven by evidence, not a guessed sales probability.

### Match and rank

- Same source ID means an update. Across sources, require compatible location/parcel, project description and timing; keep uncertain matches for review.
- Keep suites, phases and distinct permits. One subdivision, its individual houses and its builder are related records, not interchangeable duplicates.
- First rank active, local, clearly relevant opportunities with a reachable decision-maker. Keep promising records without a contact in a research queue so lack of a phone does not erase coverage.
- Fencing/concrete around new houses or pools, finishing trades in commercial renovations, and direct repair bids are useful examples. A permit for a roof may show a roofer already hired; an issued house permit may still support subcontract outreach rather than winning the whole build.
- Keep expired bids, completed jobs, unrelated filings and uncertain records out of the active shortlist, while retaining their reason/history.

### Prove the run worked

- Report records downloaded, parsed, rejected, deduplicated, matched to Masiate, still active, and with business contacts. Do not add those categories together as if they were separate leads.
- For each source, show the requested and actually covered dates, pages/files read, errors and access gaps. Compare to published totals only where categories and dates genuinely match.
- Review up to ten records per source, including low-confidence entries, and the first twenty highest-ranked results. A bad parser fails its source even if the code runs successfully.
- Verify every published lead has an identity, service reason, dated evidence and status; separate unknown from no results. Re-running the same files must not create duplicate projects.
- Initial success is a checked sample plus honest coverage, followed by complete collection of the agreed accessible sources. It is not a claim to have found every job in the region.

## 5. Same Facts In The Public Section And Agent

**One checked dataset feeds both.** The public section can show opportunities filtered for Masiate's work; it does not need a private Masiate login or a separate application.

- Proposed collection path: `propertystack/runs/masiate/<run-id>/`; reviewed output: `propertystack/data/masiate/`. These are planned paths, not files already produced.
- Keep raw evidence outside public exports. Publish useful project facts and verified business contacts; do not automatically republish personal homeowner contact details or private outreach notes.
- Produce a section JSON export and matching agent CSV tables for projects, evidence, business contacts and source coverage, all carrying the same dataset version. These are ordinary files the current app/agent can read.
- The current agent plugin at `chatbot/hermes-profile/plugins/propertystack/__init__.py` loads CSV files into a read-only database at startup. `chatbot/Dockerfile` explicitly selects which data ships. A new crawl folder alone will not teach the live agent anything.
- Later integration must add explicit data packaging, table descriptions and citation instructions, then reload/rebuild the agent normally. Keep these records out of automatic apartment/state totals unless explicitly intended; the existing Dockerfile collects files named `chat-leads.csv` across areas.
- The agent should answer: "Which local projects might need fencing?", "Who should Masiate approach?", "What is the evidence?", "Is this an open bid or a guess?", and "Which towns/sources are missing?"
- Test site/agent agreement on project IDs, counts under identical filters, status, source links and last-update times. Evidence from source pages is data, never instructions for the agent to follow.
- The collection run prepares these exports. Building the public page and wiring the live agent are following stages, not work silently included in this planning turn.

## 6. Small Steps And The Next Decision

This is a collection design, **not a runnable /gowork plan**. Implementation needs small tasks with real executable checks as each adapter is defined. Do not launch a monolithic crawl/build task from this document.

### Proposed task queue

Each item should fit roughly 15-30 minutes; split unfamiliar sources into access discovery, parsing and collection tasks when necessary.

- [ ] Confirm area and create the source inventory; outcome: each jurisdiction has a source or an explicit gap.
- [ ] Save a College Station issued-permit file and prove a parser; outcome: checked rows from one real document.
- [ ] Collect College Station's agreed permit window; outcome: dated results and completeness report.
- [ ] Resolve Bryan's individual-permit access; outcome: tested public search/export or a drafted records request, not summary totals presented as leads.
- [ ] Parse and collect Bryan permit records once accessible; outcome: checked project rows with preserved IDs.
- [ ] Parse one Bryan development agenda and its project links; outcome: stage, applicant and source page verified.
- [ ] Collect Bryan's agreed planning window; outcome: revisions update existing projects.
- [ ] Parse and collect College Station new-development lists; outcome: early projects with dated source evidence.
- [ ] Adapt and test the TABS Masiate profile; outcome: local renovations and smaller relevant projects are retained, failures are visible.
- [ ] Collect the agreed TABS window; outcome: county/date pagination audited and details saved.
- [ ] Prove Hearne's agenda route and permit availability; outcome: real records or a documented access gap.
- [ ] Repeat one city/source at a time for each additional jurisdiction chosen; outcome: separate coverage receipts.
- [ ] Collect matching public bid notices; outcome: deadlines and access requirements retained, expired awards separated.
- [ ] Prove and collect construction stormwater records; outcome: local sites linked to projects, unrelated program records excluded.
- [ ] Prove and collect pending TABC applications; outcome: new applications distinguished from renewals.
- [ ] Prove and collect relevant sales-tax location records; outcome: business-opening signals kept separate from confirmed construction needs.
- [ ] Check health/occupancy record access; outcome: usable local source or drafted export request.
- [ ] Match Brazos parcels and owners; outcome: exact/uncertain matches distinguished and certification date retained.
- [ ] Match Robertson or each additional county separately; outcome: county-specific verification and access report.
- [ ] Enrich a bounded batch of projects with business contacts; outcome: every contact has a source and role; repeat for further batches.
- [ ] Consolidate and rank the collected records; outcome: no duplicate counting, unexplained stages or invented availability.
- [ ] Review source samples and produce matching public/agent exports; outcome: one dataset version and a plain-English coverage report.

### How to try it when collection is ready

1. Open one suggested job and compare its address, date and description with the linked original record.
2. Pick a trade such as fencing and see why each result matches, who to approach and whether anyone has confirmed the work is available.
3. Ask the agent about that same project and check that it gives the same facts, source and missing-information warning.

There is no new local server to start yet: this turn produces a plan only.

### Decision still needed

Collection boundary is confirmed as **all seven Brazos Valley counties**. It is a research boundary, not a verified company travel policy. The next interview decision concerns one-time versus recurring collection and PDF editions.

After the area is settled, the next planning decision is how to run the small implementation tasks: /gowork or a normal session. No agent workers, schedules or paid crawls have been started.
