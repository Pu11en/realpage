# Masiate: Tools For Finding The Best Properties

## What We Will Reuse

- **Confirmed direction:** use the tools CraneSignal already has, including paid services already available, plus useful open-source software; no new purchases.
- **Jina AI:** find relevant pages and turn pages into readable text for research; CraneSignal already has both search and page-reading code, and a Jina key is configured without exposing its value. [Official Jina project](https://github.com/jina-ai/reader).
- **Brave Search:** existing backup when Jina results are missing or poor; a key is configured, but remaining allowance and billing status are not verified. [Official Brave API](https://brave.com/search/api/).
- **Crawl4AI, Scrapling and Playwright:** already present in the shared collector and installed in the checked Python environment; use the appropriate reader for ordinary pages and public forms that need a browser. Installation does not prove a browser launches or any county site works. [Crawl4AI](https://github.com/unclecode/crawl4ai), [Scrapling](https://github.com/D4Vinci/Scrapling), [Playwright](https://playwright.dev/python/docs/network).
- The existing Jina search/read client is `propertystack/lib/jina.py`; the shared collector is `propertystack/skills/lead-finder/fetch.py`; the agent's Jina and read-only data tools are in `chatbot/hermes-profile/plugins/propertystack/__init__.py`.

## Free Tools For Documents And The PDF

- **Direct official downloads first:** read government spreadsheets, record exports and public data feeds directly where available; avoid spending search calls rediscovering every row.
- **Already available:** HTTPX for downloads, Beautiful Soup for page text, openpyxl for spreadsheets, and pdftotext/pdfplumber for PDF text and tables; keep the original document and page number behind each claim. [pdfplumber documentation](https://github.com/jsvine/pdfplumber).
- **Possible free addition:** Tesseract for scanned documents that are pictures rather than searchable text; it was not found on the checked command path, and nothing was installed. Add only if actual source documents require it, then review uncertain names and numbers. [Tesseract project](https://github.com/tesseract-ocr/tesseract).
- **PDF creation already exists:** `site/js/lead-pack.js` uses bundled jsPDF and AutoTable; investigate reusing those pieces for a detailed, fixed report rather than buying a PDF service. The current exporter is not yet a Masiate report template. [jsPDF project](https://github.com/parallax/jsPDF).
- No reason found to add a new paid scraping platform, contact database, proxy subscription or report service at this stage; reconsider only if an actual source exposes a gap, without purchasing automatically.

## How These Tools Produce Leads

1. List the relevant public sources in all seven selected Brazos Valley counties, including local permits, planning records, open bids and state construction records.
2. Test a few individual records from each source, then collect the agreed date range and all its result pages; distinguish an empty search from a failed one.
3. Join related permits, plans and ownership records into properties, preserving separate suites and project phases; summary permit counts are not individual leads.
4. Rank the properties by relevant work, recent evidence and usable business contacts; research the strongest ones further using official sources and the businesses' own websites.
5. Produce the fixed PDF with addresses, work descriptions, owners and other project participants, public business contacts, dates, known budgets, source links and explicitly missing information.
6. Give the agent the same collected information; let it research more on request without rewriting the PDF, and retrieve the person's earlier findings from their own saved chats.

Search tools help discover and enrich records; they cannot prove that every permit was found or that a property is hiring Masiate's services.

## Limits To Check Before Running

- **Already paid does not mean unlimited:** verify remaining credits, subscription allowances and whether requests can cause automatic top-ups or extra charges; do not change billing settings or buy more.
- Existing code's Brave limit of 800 monthly calls is a local rule, not proof of the account's present entitlement; provider/account limits must be checked before reuse.
- Existing counters are not a reliable shared spending limit across all processes; the initial run needs one coordinated allowance, call logging and stop conditions before paid endpoints are used.
- Jina's helper counts requests but does not provide a dollar spending limit; requests and tokens are not interchangeable cost measures.
- Shared page caching reduces repeat work, but a URL-only cached page does not establish freshness; record the retrieval date and deliberately recheck pages for live follow-up.
- Keep requests paced, record incomplete sources, and use legitimate public access; do not bypass logins, paywalls or access restrictions with another tool.
- Existing collectors are apartment-focused; create a separate Masiate collection profile so homes, renovations and smaller commercial jobs are included without changing apartment leads elsewhere.
- Verify installed browser dependencies, real source pagination, contact accuracy, PDF readability and user-scoped chat retrieval before describing the feature as working.

## What Was Actually Checked

- Checked on September 20, 2026: repository integration code, installed package presence, configured key presence without showing secrets, and primary tool documentation.
- The checked Python environment contains HTTPX, Beautiful Soup, Crawl4AI, Scrapling, Playwright, pdfplumber, openpyxl and Pillow; pdftotext is on the command path.
- No provider balance was inspected, no paid Jina/Brave request was made, and no Masiate collection, package installation, feature build or PDF generation was started.
- **Result:** a concrete reuse-first tool plan, not a claim that all sources work or that a report already exists.
