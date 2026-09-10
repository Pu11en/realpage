# Apartment Project Detection Tools & Data Sources Research

**Source:** Web research  
**Fetched:** 2026-09-10  
**Method:** WebSearch + WebFetch verification of endpoints  
**Confidence:** High (all URLs fetched or confirmed via official sources)

---

## 1. TDLR TABS (Texas Architectural Barriers)

**URL:** https://www.tdlr.texas.gov/tabs/search

**What it is:**  
Texas Architectural Barriers Online System. Registration required for most new construction and certain alterations in Texas. TDLR assigns TABS project numbers (format: TABS + 10-digit code, e.g., TABS2026003465).

**Stage caught:** Project registered (early; before permits issued)

**Machine-readable?** No bulk export or CSV found. Web portal only; no API endpoint discovered.

**Tested query result:**  
- Web UI searchable by city + project type
- Example URL pattern: https://www.tdlr.texas.gov/TABS/Search/Print/TABS2024024969
- Sample data: TABS2027000367 (Dollar Tree Tomball TX) shows permit status + completion dates

**Weekly automation:** Not viable without scraping web portal; no documented API or bulk export

**Bulk export available?** No

---

## 2. Zabalist.com/projects

**URL:** https://zabalist.com/projects (Texas Construction Intelligence Platform)

**What it is:**  
Third-party mirror of TABS and other Texas construction data. Indexes 150,000+ verified Texas contractors and 210,000+ projects with permit status, estimated completion, and project values.

**Stage caught:** Permit filed → approved → construction underway

**Machine-readable?** Site structure supports URL-based project queries (e.g., /projects/TABS2027000437). No documented REST API.

**Tested query result:**  
- Lavon Landing Flex Building (TABS2027000437): New construction, $5.2M, completion Apr 2027
- Dollar Tree Store (TABS2027000367): Renovation, completion Jan 2027
- Searchable by city (/projects/city/plano)

**Weekly automation:** Manual scraping or contact Zabalist; no public API documented

**Terms:** Free to view; commercial API/export unknown

---

## 3. City of Richardson Open Data Hub

**URL:** https://opendata-richardson.opendata.arcgis.com

**What it is:**  
Richardson's ArcGIS open data portal. Contains building footprints, parcel data, trees, floodplains, but no dedicated building permits layer found in search results.

**Stage caught:** Conceptually could track permits if layer exists (permit issued stage)

**Machine-readable?** ArcGIS FeatureServer REST API supports JSON queries. Example layer: https://opendata-richardson.opendata.arcgis.com/datasets/building-footprints

**Tested query result:**  
- Building Footprints layer exists with REST API access
- No Building Permits specific layer located
- Development Status Map exists (plano.gov reference) but not in open data hub

**Weekly automation:** Can script ArcGIS REST queries if permits layer added

**Verdict:** Incomplete; missing permits/zoning layer. Contact Richardson GIS department at https://www.cor.net/departments/geographic-information-services for permits endpoint.

---

## 4. City of Plano Open Data Portal & Legistar

**URLs:**
- Dashboard: https://dashboard.plano.gov/
- Legistar: https://plano.legistar.com
- Legistar API: https://webapi.legistar.com/v1/plano/matters

**What it is:**  
Plano uses Granicus Legistar for meeting agendas/zoning cases. Web API exposes Planning & Zoning Commission matters (agenda items, applications, approvals).

**Stage caught:** Zoning case filed → approved (via P&Z agenda items)

**Machine-readable?** Yes. Legistar Web API returns JSON with OData filtering.

**Tested query result:**  
**API endpoint works:**
```
https://webapi.legistar.com/v1/plano/matters?$top=1
→ HTTP 200
```
Sample response: Matter ID 1537, "P&Z - Consent Item", Status "Agenda Ready", Agenda Date "January 5, 2026"

Endpoint structure: `/v1/plano/matters`, `/v1/plano/events` (meeting dates), `/v1/plano/bodies` (commissions)

**Weekly automation:** Yes. Script can poll `/matters` with filters for "Planning & Zoning" body type, status "Agenda Ready" or "Approved". Legistar API documentation: https://webapi.legistar.com/Help

**Verdict:** High confidence. Requires API token for some clients; check with Plano or Granicus for token policy.

---

## 5. City of Richardson Zoning & Permits

**URLs:**
- Permits page: https://www.cor.net/departments/building-inspection
- GIS services: https://www.cor.net/departments/geographic-information-services
- Legistar: No richardson.legistar.com found

**What it is:**  
Richardson has online permit system and GIS services. No Legistar portal discovered; city may use alternative system (CivicClerk, CivicPlus, or internal system).

**Stage caught:** Permit filed (if publicly available)

**Machine-readable?** Unclear. No public ArcGIS building permits FeatureServer identified.

**Weekly automation:** Contact Richardson GIS or Planning department directly to request API access or building permits export.

**Verdict:** Incomplete data. No Legistar API. Recommend direct contact with https://www.cor.net/departments/development-services/maps

---

## Open-Source Tools & GitHub Solutions

### 1. python-legistar-scraper (OpenCivicData)
- **GitHub:** https://github.com/opencivicdata/python-legistar-scraper
- **What it does:** Scrapes Legistar HTML and exposes meeting agendas, legislation, persons, votes via Python library
- **Last update:** Active (commits in 2025)
- **License:** Open (Apache 2.0)
- **Use case:** Plano P&Z agenda tracking; call webapi.legistar.com/v1/plano directly, or use this if web scraping needed
- **Maintained by:** OpenCivicData

### 2. city-scrapers (City-Bureau)
- **GitHub:** https://github.com/City-Bureau/city-scrapers
- **What it does:** Standardized framework for scraping local government meetings from websites. Uses python-legistar-scraper + custom parsers per city.
- **Last update:** Active (multiple regional forks updated July 2026)
- **License:** MIT
- **Use case:** Plano/Richardson P&Z commission meeting announcements; extensible template for city-specific scrapers
- **Template:** https://github.com/City-Bureau/city-scrapers-template

### 3. esri2gpd (PhilaController)
- **GitHub:** https://github.com/PhilaController/esri2gpd
- **What it does:** Python library to scrape ArcGIS REST FeatureServer endpoints and return Geopandas GeoDataFrame. Auto-pagination for large datasets.
- **Last update:** Active
- **License:** MIT
- **Use case:** Query Richardson ArcGIS building permits (if layer exists) or Plano permits via ArcGIS
- **Alternative (R):** esri2sf (https://github.com/yonghah/esri2sf)

### 4. permitgrab (PermitGrab platform)
- **GitHub:** https://github.com/wcrainshaw-eng/permitgrab
- **What it does:** Aggregates building permits from 770+ US cities. Pulls daily from Socrata, ArcGIS, CKAN, Carto, and normalizes to CSV/JSON.
- **Last update:** Active
- **License:** Permissive (commercial platform, source available)
- **Use case:** Monitor Plano + Richardson permits via single aggregator; daily updates
- **Note:** Commercial tool (permitgrab.com) offers paid API, but GitHub code shows ingestion patterns

### 5. texas-data-scraper (Chandra Bhanswami)
- **GitHub:** https://github.com/chanderbhanswami/texas-data-scraper
- **What it does:** Scrapes Socrata (data.texas.gov, data.austintexas.gov) and Texas Comptroller APIs. Supports GPU acceleration, deduplication, multi-format export (CSV, JSON, Excel).
- **Last update:** Recent (2025-2026)
- **License:** MIT
- **Use case:** Bulk query data.texas.gov for TABS or state-level permits if available; extensible to city APIs
- **Note:** Requires Socrata API key (free tier available at data.texas.gov)

---

## Recommended Stack

### Best 2-3 sources (in order):

1. **Plano: Legistar Web API** (`https://webapi.legistar.com/v1/plano/matters`)  
   - **Why:** Direct, machine-readable, weekly-automatable, early stage (zoning filed → approved)
   - **Tool:** Use raw HTTP polling or python-legistar-scraper
   - **Endpoint:** `/matters?$filter=BodyId eq PLANNING_AND_ZONING_ID`
   
2. **Zabalist.com** (`https://zabalist.com/projects/city/plano`)  
   - **Why:** Mirrors TABS data + completion timelines, covers both Plano & Richardson
   - **Tool:** Web scraper (BeautifulSoup/Scrapy) or permitgrab's ingestion logic
   - **Limitation:** No API; requires HTML parsing

3. **Richardson: Contact GIS / Direct Data Request**  
   - **Why:** No public API yet; city may provide ArcGIS endpoint or CSV export on request
   - **Contact:** https://www.cor.net/departments/geographic-information-services
   - **Fallback:** Use Zabalist + Legistar for Richardson (if they adopt Legistar later)

### Open-source tool recommendations:

- **For Plano Legistar agendas:** `python-legistar-scraper` or `city-scrapers-template` (use /v1/plano/matters endpoint directly to avoid scraping)
- **For ArcGIS-based permits (if found):** `esri2gpd` (Python) or `esri2sf` (R)
- **For Zabalist scraping:** `permitgrab` source code patterns (Scrapy-based)
- **For Texas-wide data:** `texas-data-scraper` (if Socrata dataset published)

### Weekly automation stack:

1. Python script: Poll `webapi.legistar.com/v1/plano/matters` → filter P&Z items → store + alert
2. Async scraper: Weekly fetch Zabalist `/city/plano` + `/city/richardson` → parse project updates
3. Fallback: Email subscription to Richardson planning + Plano P&Z agendas (manual check weekly)

---

## Key Findings

| Source | Coverage | API? | Automation | Weekly Viable? |
|--------|----------|------|-----------|----------------|
| TDLR TABS | TX-wide, early-stage | No | Web scrape only | Poor |
| Zabalist | TX-wide, mid-stage | No | Web scrape | Medium |
| Richardson OpenData | Richardson permits | Yes (ArcGIS) | If permits layer exists | TBD |
| Plano Legistar API | Plano zoning cases | Yes (REST) | HTTP poll | **YES** |
| Richardson (direct) | Richardson permits | Unknown | Request-based | Uncertain |

**Legistar client names:**
- Plano: `plano` (confirmed working)
- Richardson: No Legistar instance found; city may use Granicus CivicClerk or internal system

**TABS bulk export:** Not available; manual web search or third-party scraper required

---

## References

- [TDLR TABS Search](https://www.tdlr.texas.gov/tabs/search)
- [Zabalist Projects](https://zabalist.com/projects)
- [City of Richardson Open Data](https://opendata-richardson.opendata.arcgis.com)
- [Plano Legistar](https://plano.legistar.com)
- [Legistar Web API Help](https://webapi.legistar.com/Help)
- [python-legistar-scraper GitHub](https://github.com/opencivicdata/python-legistar-scraper)
- [city-scrapers GitHub](https://github.com/City-Bureau/city-scrapers)
- [esri2gpd GitHub](https://github.com/PhilaController/esri2gpd)
- [permitgrab GitHub](https://github.com/wcrainshaw-eng/permitgrab)
- [texas-data-scraper GitHub](https://github.com/chanderbhanswami/texas-data-scraper)
