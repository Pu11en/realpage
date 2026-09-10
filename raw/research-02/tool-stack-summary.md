# Tool stack per skill — verified summary

Source: raw/research-02/find-apartments-validation.md, find-sales-tools.md, find-upcoming-tools.md + direct checks
Fetched: 2026-09-10
Method: three haiku research agents; key claims re-checked with direct API calls (main session)
Confidence: high where marked "verified", medium otherwise

| Skill | Tool / source | Status |
|---|---|---|
| find-apartments | Collin CAD 2026 on Socrata (`data.texas.gov/resource/5tkr-3759.json`) | verified; dataset updated 2026-09-08 |
| find-website | Jina Search (`s.jina.ai`); Crawl4AI as backup | proven by hand on ~40 |
| detect-software | Jina Reader + one hop (`tooling/pms_detect.py`); Crawl4AI backup | proven, 83% |
| find-sales (primary) | CAD year-over-year owner diff: 2026 `5tkr-3759` vs 2025 `vffy-snc6` (2024 `6dqt-e958` also exists) + `deedeffdate`/`deedtypecd` | verified datasets exist |
| find-sales (faster, later) | Collin/Dallas County Clerk deed search: free, no API, needs scraping, 3–10 day delay | unverified |
| find-upcoming (Plano) | Legistar Web API `webapi.legistar.com/v1/plano/matters` | verified API responds; the right filter for zoning/multifamily items still needs work ("multifamily" in title = 0 hits) |
| find-upcoming (both cities) | TDLR TABS: no export, scrape per project page; zabalist.com mirror | medium |
| find-upcoming (Richardson) | no Legistar; open-data permits layer unclear | open question |

## find-apartments filter fix (verified)
Old: `propcategorycode='B' AND imprvunits>=20` → misses **9 real apartment
properties** coded as commercial (F1) with use code MFU: Bel Air Oaks (474),
The Dayton (389), Jada Legacy Central (385), Steeplechase (368), Opal Legacy
Central (310), Latitude (304), K Avenue Lofts (226), Spring Pointe (208), Bel
Air on 16th (152).
New: `(propcategorycode='B' OR propusecode IN ('MFU','MFUSE')) AND imprvunits>=20`
(MFUSE = mixed-use, 2 parcels; check they're apartments.)
Excluded on purpose: HO (hotels), MO (motels), ALF (assisted living), MHP (mobile home parks).

## Corrections to agent reports
- The sales agent said the CAD data was last updated in July 2026. The actual `rowsUpdatedAt` is **2026-09-08**.
- The completeness estimate (~96%) covers only what the CAD itself miscodes. No independent full list was available to cross-check: OSM names are too messy, and the city registration list isn't public.
- The GitHub repos found are small or inactive. No mature open-source tool exists for this job; the building blocks (Socrata, Legistar API, Jina, Crawl4AI) are the reusable parts.
