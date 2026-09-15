# Texas Round 2 — Free Data Source Live-Test (2026-09-14)

Method: real curl requests, no SearXNG. Jina used only for finding page URLs (well under 60 searches used).

## 1. Appraisal-district bulk downloads

| County (CAD) | Status | Endpoint | Fields / notes | Sample |
|---|---|---|---|---|
| Williamson (WCAD) | **WORKS** | `https://data.wcad.org` — full Socrata portal. Property export: `https://data.wcad.org/resource/ij43-xknu.json`; Improvement: `4d8i-sgri`; Property Characteristics: `cvyp-ab5t`; Sale: `pvyy-mm8r`; Building Permits: `fqhf-gyjx`. Also raw file layout PDFs at `documents.wcad.org/DataDownloads/*.pdf`. | Improvement dataset has `statecode`/`description` (Residential/Commercial/Mobile Home) but not multifamily-specific in the sample pulled; Property Characteristics has `actyrbuilt`, `sqftcur`, `segclass`. Full flat-file layout PDF documents state-class codes (not fetched in text form — worth a follow-up pull if unit-count filtering is needed). Updated per certification cycle (preliminary/certified/supplement files referenced in docs). | Property table: **319,477 rows** live via API. Building Permits table returns real rows with issue dates back to 2002 through 2026. |
| Fort Bend (FBCAD) | **WORKS** | `https://www.fbcad.org/data-files/` — static file list, e.g. `2025_01_02_...Orion-2024-Supplement-5-Export-Redatcted.zip` | Zip files (Orion export format), separate Commercial/Residential Segment files. No API — just periodic file drops (preliminary/certified/supplemental cycle, several per year). | Confirmed download: zip, **1,203,990 bytes**, `content-type: application/zip`. |
| Bexar (BCAD) | **WORKS (via county GIS, not BCAD's own site)** | `https://maps.bexar.org/arcgis/rest/services/Parcels/MapServer/0` — ArcGIS FeatureServer, no key required. | Fields include `State_cd` (TX property-use class code), `YrBlt`, `GBA`/`TOT_GBA` (building area), `Stories`, `Houses`, `Owner`, `Situs`, `TotVal`. Filter `State_cd='B1'` = multifamily. BCAD's own site (bcad.org) has no visible bulk-download page. | Total parcels: **710,772**. Multifamily filter `State_cd='B1'`: **7,346 parcels** returned live. |
| Montgomery (MCAD) | **REQUEST NEEDED / unclear** | `https://mcad-tx.org/appraisal-data-exports` returns 200 but is a JS single-page app (89-line shell, no links in raw HTML). Guessed Socrata subdomain `data.mcad-tx.org` also resolves 200 but serves a static S3/CloudFront shell, not a live API (catalog endpoint returns the SPA shell, not JSON). | Page clearly exists and is titled for data exports, but automated (non-browser) pulling failed — likely needs a real browser or a direct file-manager path not discoverable via curl. | n/a — needs manual browser check. |
| Denton CAD | **REQUEST NEEDED / unclear** | `https://www.dentoncad.com/data-downloads` returns 200 but is the same 89-line JS-shell pattern as MCAD. No working Socrata/ArcGIS subdomain found. | Same limitation as MCAD — page exists, content is client-rendered. | n/a |
| Travis (TCAD) | **NOT FOUND (bulk)** | `traviscad.org/data-downloads` = 404. TCAD's own site states its property search "is not intended for bulk transfer of data." Travis County's separate `open-data-portal` references `data.traviscountytx.gov`, which does not resolve (DNS failure). | No appraisal-account bulk export found for Travis. Would need to check Travis County's ArcGIS parcel viewer directly (not attempted — time-boxed). | — |
| Hays CAD | **NOT FOUND (CAD-specific); GIS parcels exist for the county** | `hayscad.com` returns 403 to curl (blocks non-browser UA). Hays County runs an ArcGIS Hub GIS portal (`hays-county-haysgis.hub.arcgis.com`) but its parcel search API path (`/api/feed/search`) 404'd on first try — would need the correct REST service name. | Not confirmed working in the time box. | — |
| Comal CAD | **NOT FOUND** | `comalad.org` loads (301→200) but no `/data-downloads` page (404); no GIS/export link surfaced. | — | — |
| El Paso CAD | **NOT FOUND (CAD); city has separate GIS, see below)** | `epcad.org` blocks curl with 403 on most paths; no bulk export surfaced. | — | — |
| Lubbock CAD | **NOT FOUND** | Site loads but no `/data-downloads` page; Jina search only surfaced general GIS-data-services page for the *city* of Lubbock, not the CAD. | — | — |
| Nueces CAD | **NOT FOUND** | `nuecescad.net` loads; no export/download page found (404 on guessed path, no GIS/export link in search results). | — | — |

**Ranking for this category:** Williamson (WCAD) is the best new find — a full Socrata API with property, improvement, sale, and building-permit tables, freely queryable with SoQL filters. Bexar's county ArcGIS parcel layer is nearly as good and gives an instant multifamily filter via `State_cd`. Fort Bend already has usable static file exports. Montgomery and Denton CAD clearly have download pages but need a real browser session to extract links. The rest (Travis, Hays, Comal, El Paso, Lubbock, Nueces) turned up nothing usable in a time-boxed pass — not proof they don't exist, just not found via curl/Jina today.

## 2. City permit feeds (last 24 months, ≥100 rows with address+date)

| City | Status | Endpoint | Multifamily filter | Sample |
|---|---|---|---|---|
| College Station | **WORKS** | `https://data.cstx.gov` (Socrata). Datasets: `hrbn-znt6` (Permits - Master Dataset), `7vts-9bqr` (Permits - Type and Year), `6npd-u87q` (Inspections). | `upper(permit_description) like '%APARTMENT%'` | Last 24 months (`issued_date > '2024-09-14'`): **10,833 permits**. Apartment-description filter: **1,043 rows**. Well over the 100-row bar. |
| El Paso | **PARTIAL / WORKS (dashboard, not raw API)** | ArcGIS Hub `city-of-el-paso-open-data-coepgis.hub.arcgis.com`; DCAT feed lists a dataset titled **"New construction 2024-2026"**, but its only distribution is an ArcGIS Experience Builder dashboard app (`experience.arcgis.com/experience/...`), not a directly queryable REST feature layer found in the time box. | Dataset title itself is the filter (new construction only). | Not row-counted — would need to find the underlying feature service ID from the dashboard, which requires opening it in a browser. |
| Denton (city) | **NOT FOUND** | Guessed `data.cityofdenton.com` domain resolves but is an unrelated/expired ArcGIS Hub site (404 on search, empty DCAT feed). | — | — |
| Sugar Land | **NOT FOUND** | Same pattern as Denton — domain resolves to a generic ArcGIS Hub shell with 0 datasets in the DCAT feed. | — | — |
| Corpus Christi | **NOT FOUND** | Search surfaced only a static "Building Permits" info page on corpuschristitx.gov, no open-data portal link. | — | — |
| Lubbock (city) | **NOT FOUND** | Search surfaced a GIS/data-services page (`mylubbock.us/318/GIS-Data-Services`) but no permit dataset or portal confirmed live. | — | — |
| Round Rock, Georgetown, Frisco, New Braunfels, Killeen, Waco, Pflugerville, Conroe, League City | **NOT FOUND (unverified)** | Guessed standard ArcGIS Hub subdomain patterns (`data-<city>.opendata.arcgis.com`, `gis-frisco.opendata.arcgis.com`) all return HTTP 200 but are generic/empty ArcGIS Hub landing shells (0 datasets in each DCAT feed) — i.e., wrong subdomain guesses, not confirmation the city lacks a portal. Stopped here per the "don't chase dead ends" instruction; a per-city Jina search would likely find the real subdomain but wasn't run to stay within the lean budget. | — | — |

**Ranking for this category:** College Station is the clear winner — a real, actively-updated Socrata feed with a built-in text filter for apartments and 10x the row-count bar. El Paso has a promising "New construction" dataset but it's wrapped in a dashboard app rather than a raw feed, so it needs one more manual step to unlock. Everything else tested came back empty; most of those cities almost certainly have *some* open-data presence, but the exact subdomain wasn't found in this pass.

## 3. Other free statewide/regional feeds

| Source | Status | Notes |
|---|---|---|
| H-GAC interactive web applications | **NOT FOUND (not multifamily-specific)** | `h-gac.com/interactive-web-applications` lists dashboards but nothing apartment/development-tracker specific surfaced in one search. Not pursued further. |
| NCTCOG / CAPCOG development trackers | **NOT FOUND** | No hit in the same search; not checked individually due to time budget. |

## Summary ranking (most useful first)

1. **Williamson CAD (WCAD)** — full Socrata API, 319K+ property rows, live SoQL queries, includes a building-permits table.
2. **Bexar County parcels (ArcGIS, via maps.bexar.org)** — 710K parcels, live multifamily filter (`State_cd='B1'` → 7,346 hits), no key needed.
3. **College Station permits (Socrata)** — 10,833 permits/24mo, apartment filter gives 1,043 rows.
4. **Fort Bend CAD (FBCAD)** — confirmed static zip exports (~1.2MB), updated multiple times per year.
5. **El Paso "New construction" dataset** — real dataset exists but needs manual dashboard drill-down to get raw rows.
6. **Montgomery CAD / Denton CAD** — data-download pages confirmed to exist but are JS-rendered; need a browser (not curl) to extract file links.
7. Everything else checked today (Travis, Hays, Comal, El Paso CAD, Lubbock CAD, Nueces CAD, and 11 of the 15 target cities) — no working free bulk/API source found in this pass; treat as open questions, not confirmed dead ends.
