# Lead finder tools v2 research (2026-09-14) — raw findings for the fix plan

## Arizona permit sources (tested live)
- Phoenix: ArcGIS https://maps.phoenix.gov/pub/rest/services/Public/Planning_Permit/MapServer/1 (~67k since 2015; no units; SCOPE_DESC='COMMERCIAL NEW' + PERMIT_NAME like APART/APT/MULTI/MF) — 360 rows. (CKAN "Building Permit Data" = 22 yearly summary rows, useless.)
- Mesa: Socrata https://data.mesaaz.gov/resource/dzpk-hxfb.json, type_of_work='Multi-Family Residential', units parsed from description "(11) unit apartment" — 157 since 2024-09.
- Tempe: ArcGIS https://services.arcgis.com/lQySeXwbBg53XWDi/arcgis/rest/services/building_permits/FeatureServer/0 — HousingUnits + COIssuedDate — 17 permits 20+ units since 2024-09.
- Scottsdale: https://maps.scottsdaleaz.gov/arcgis/rest/services/OpenData_Tabular/MapServer/12 PermitType IN ('APARTMENTS','MULTI-FAMILY DWELLING'), owner+builder — 39+29.
- Gilbert: https://maps.gilbertaz.gov/arcgis/rest/services/OD/Growth_Development_Tables_1/MapServer/3 PermitType='Commercial Multi-Family' AND WorkClass='New' — 38 (some mislabeled).
- Tucson: https://gis.tucsonaz.gov/public/rest/services/PublicMaps/PermitsCode/MapServer/84 multifamily layer, DwellingUnits (often 0) — 8 new/4 20+ since 2024-09.
- Maricopa County unincorporated: https://services.arcgis.com/ykpntM6e3tHvzKRJ/arcgis/rest/services/Building_Permits_(view)/FeatureServer/0 — 48 matches.
- Peoria: https://gis.peoriaaz.gov/arcgis/rest/services/Accela/Peoria_Building_Permit_All/FeatureServer/3 — weak (active only).
- Glendale: monthly Combined Permits PDFs (glendaleaz.gov Permit-Reports) — not read.
- Chandler, Goodyear: Accela Citizen Access only. Buckeye: SmartGov only.
- Sales: Maricopa County Assessor "Sales Affidavits" CSV (ArcGIS item f3484c72a938497286adc4e5de7e9963, updated 2026-09-03) join parcel file item 936bbba512bf4c368618cc6e79e64668.
## Discovery methods (best first)
1 ArcGIS Online search `https://www.arcgis.com/sharing/rest/search?q=title:permits "<place>"` 2 city ArcGIS hub search 3 Socrata catalog 4 CKAN package_search (+ row-count sanity) 5 detect Accela/Tyler/SmartGov → "no free data" 6 Census BPS place files for ranking 7 Shovels.ai free tier (500 credits/mo) for gaps.
- Rule: accept a dataset only if one real query returns permit-level rows (≥100 rows, address field).
## Near-Texas
- NM Albuquerque ArcGIS https://coageo.cabq.gov/cabqgeo/rest/services/agis/City_Building_Permits/FeatureServer/0 NumberofUnits — 9 20+ since 2024-09.
- LA New Orleans data.nola.gov rcm3-fn58; Baton Rouge data.brla.gov 7fq7-8j7r (filter TBD).
- CO statewide counts only; Denver unverified. OK Tulsa layer error; OKC none. AR/TN/NV/UT/GA: none found quickly.
## Search + enrichment
- Jina search: 10k tokens/search (~$0.50/1k searches, rate unverified). Backups: Serper.dev (Google results, ~$1/1k, 2,500 free; Places endpoint gives website+phone), Brave Search API ($5/1k, $5 free credit/mo, own index). Google CSE closing; Bing API retired.
- Website: Jina search → drop listing sites (zillow, apartments.com, rentcafe listing, apartmentguide, facebook) → official site first.
- Software: curl site → crawl4ai render → match links: Yardi *.securecafe.com/*.rentcafe.com; RealPage *.onlinesite.realpage.com, loftliving.com, activebuilding.com; Entrata *.residentportal.com; AppFolio *.appfolio.com; ResMan *.myresman.com. Verified: Marquee on 5th (Tucson) = Yardi; Bella Victoria (Mesa) = Yardi.
- Phones: Serper Places (~$1/1k) or Google Places ($35/1k, 1k free/mo); AZ ACC eCorp (agents, no phone); OpenCorporates poor value.
