# New Mexico multifamily construction/sales data sources — verified 2026-09-19

Every URL below was actually fetched (curl/WebFetch) during this research and returned real data. Row counts, field lists, and sample rows are copied from live responses, not documentation. Dates in sample rows are Esri epoch-millisecond timestamps.

---

## 1. Albuquerque — City Building Permits (ArcGIS FeatureServer) — BEST source for ABQ

**System type:** arcgis

- **Query URL:**
  `https://coageo.cabq.gov/cabqgeo/rest/services/agis/City_Building_Permits/FeatureServer/0/query?where=1=1&outFields=*&f=json`
- **Multifamily filter that works today:**
  `where=TypeofStructure IN ('5-9 APT','10-19 APT','20-49 APT','GT50 APT','Apartment') AND TypeofWork LIKE '%New%'`
  (verified — returns real new-construction apartment permits)
- **Fields returned:** OBJECTID, PermitNumber, DateIssued, DateEntered, CalculatedAddress, FreeFormAddress, GeneralCategory, TypeofWork, TypeofStructure, Valuation, SquareFootage, NumberofUnits, Owner, Applicant, Contractor, DataSource, AGISLandUseUpdate, WorkDescription, created_date, last_edited_date, GlobalID
- **Example row (new-construction apartment permit):**
  ```
  PermitNumber: 201690169
  CalculatedAddress: 3600 CENTRAL AV SE
  TypeofWork: COMMERCIAL BUILDING NEW
  TypeofStructure: GT50 APT
  Valuation: 3,925,382
  SquareFootage: 60,180
  Applicant: THE CARLISLE CONDOMINIUM LLC
  Contractor: HB CONSTRUCTION OF ALBUQUERQUE INC - JASON HARRINGTON
  WorkDescription: "NEW BUILDING CARLISLE APARTMENTS 147 UNITS EPLAN..."
  ```
- **Has:** address (yes, two fields), date (DateIssued/DateEntered), unit count (NumberofUnits — populated on some but not all rows; unit totals often live in WorkDescription free text instead), valuation (yes), applicant/owner/contractor names (yes, all three).
- **Coverage:** 45,382 total rows. Covers 2009–present (KIVA system 2009–2016, POSSE LMS 2016–present).
- **Caveats:** `Owner` field is frequently blank on commercial records (owner sits in `Applicant`/`Contractor` instead). `NumberofUnits` is inconsistently populated — cross-check `WorkDescription` text for unit counts on big multifamily jobs.
- **Access limits:** No API key. Standard Esri `resultRecordCount` / pagination applies (default page ~1000-2000 records depending on server config; use `resultOffset` to page through all 45k). No published rate limit, but a public city GIS server — be polite (batch, don't hammer).
- **Note:** There is also a flat CSV mirror at `https://data.cabq.gov/business/buildingpermits/BuildingPermitsCABQ-en-us.csv` (62,310 rows, confirmed downloadable, ~20MB) with fields ApplicationPermitNumber, SiteNumber, SiteStreet, SiteStreetType, SiteStreetDirectional, SiteZip, PlanCheckValuation, TypeofWork, Lot, Block, Subdivision, Description, TotalSquareFeet, OwnerName, ContractorName, NumberOfUnits, IssueDate, Status. This CSV's `TypeofWork` only has 4 broad buckets (Building Commercial / Building Residential / Solar / Swimming Pool Permit) — you must string-search `Description` for "APARTMENT"/"MULTI-FAMILY" to filter, and `OwnerName`/`IssueDate` are blank on most rows. **Use the FeatureServer above instead** — it has the clean `TypeofStructure` apartment-tier filter and is far more reliable.

---

## 2. Bernalillo County (Albuquerque) — Assessor Tax Parcels (ArcGIS MapServer)

**System type:** arcgis (county-assessor-flat-file style data served via Esri)

- **Query URL:**
  `https://coageo.cabq.gov/cabqgeo/rest/services/agis/AddressReport/MapServer/4/query?where=1=1&outFields=*&f=json`
- **Fields (59 total):** OBJECTID, UPC, TAXYR, OWNER, OWNHSENUM/OWNSUBNUM/OWNADDIR/OWNSTR/OWNSTRTYPE (owner mailing address parts), OWNCITY, OWNSTATE, OWNZIPCODE, SITUSNUM/SITUSSTR/SITUSSTRTY/SITUSCITY/SITUSSTATE/SITUSZIP (property address parts), TAXDIST, LEGALDESC, DOCNUM, PROPCLASS, LANDVALUE, IMPTVALUE, TOTVALUE, NETTAXABLE, ACREAGE, CalculatedGISAcres, Shape, etc.
- **Example row (trimmed):** UPC parcel with OWNER="AGUIRRE SOLEDAD S"-style owner name, SITUSADD site address, TOTVALUE/NETTAXABLE assessed dollar values, PROPCLASS property class code.
- **Has:** owner name (yes), property address (yes, situs fields), assessed value (yes) — but **no sale date or sale price**, and **no new-construction/multifamily filter field** (this is a parcel/ownership snapshot, not a permit or sales-transaction feed).
- **Coverage:** 257,283 parcels, updated twice yearly (spring/fall) by the Assessor's Office.
- **Access limits:** No API key. Standard Esri paging.
- **Sales/transfer data caveat:** Bernalillo County does NOT publish a free machine-readable sales/transfer feed. The Assessor's official position is "Data for Sale" (`https://www.bernco.gov/assessor/data-for-sale/` — paid bulk data). Actual recorded deeds/transfers live in the County Clerk's records system, which is a search UI, not an API. **Recommended recipe:** use this parcel layer for ownership + assessed value, and treat sale price/date as unavailable for free automated pulls.

---

## 3. Las Cruces — Building Permits (ArcGIS MapServer)

**System type:** arcgis

- **Query URL:**
  `https://maps.las-cruces.org/gis/rest/services/Information_Services/MapServer/1/query?where=1=1&outFields=*&f=json`
- **Multifamily filter field:** `PropUseGrp` — confirmed distinct values include `APARTMENT`, `TOWN HOUSE`, `DUPLEX`, `TRIPLEX`, `FOURPLEX`, `CONDOMINIUM` (plus dozens of unrelated commercial/residential categories). Combine with `RecTypeGrp`/`Proposed_Use` to isolate new construction.
- **Fields:** Permit_Type, Permit_Number, Permit_Location, Project, Project_Valuation, Contractor_Business_Name, Contractor_Name, IssueMonthNo, Issued_Month, Issue_Year, Issued_Date, Owner_Name, Proposed_Use, PropUseGrp, RecTypeGrp, recTypeOrd, Total_SQFT, PSFEE, PAFEE, UTFEE, CDFEE, TotalFeeInvoiced, X, Y, Zoning, OBJECTID.
- **Example rows (verified live):**
  ```
  Permit_Number: 16OC5600016
  Permit_Location: 4317 PASEO DEL ORO CIR
  Owner_Name: TIERRA DEL SOL ASSET & HOLDING LLC
  Issue_Year: 2016, Issued_Month: OCT
  ```
- **Has:** address (yes), date (Issued_Date/Issue_Year/Issued_Month), unit count (no direct unit-count field — would need to infer from PropUseGrp category or Project text), valuation (Project_Valuation, yes), owner name (Owner_Name, yes), contractor (yes).
- **Coverage:** 82,961 total rows. Point layer, near-city-wide extent (roughly Doña Ana County bounding box).
- **Access limits:** No API key. Standard Esri paging; a plain `resultRecordCount` cap applies per request (use `resultOffset` to page through all 82,961 rows). `returnDistinctValues=true` fails if geometry is also requested — must set `returnGeometry=false` when doing distinct-value lookups (confirmed by testing).

---

## 4. Doña Ana County (Las Cruces) — Assessor Parcels (ArcGIS FeatureServer)

**System type:** arcgis (county-assessor-flat-file via Esri)

- **Query URL:**
  `https://gis.donaana.gov/server/rest/services/Parcels/FeatureServer/0/query?where=1=1&outFields=*&f=json`
- **Fields:** OBJECTID, MAP_CODE, ACCOUNTNUMBER, PARCELNUMBER, OWNERNAME, CAREOFNAME, MAILADDR1, MAILADDR2, CITY, STATE, ZIP, DEEDHOLDER, SITUSADDRS, LOT, BLOCK, SUBNAME, NEIGHBORHOOD, SCHOOLDISTRICT, TAXAREA, TOTALACRES, TOTALSQFT, BLDGVALUE, LANDVALUE, GlobalID, created_date, last_edited_date, Shape__Area, Shape__Length.
- **Has:** owner name (OWNERNAME, yes), mailing address (yes), situs/property address (SITUSADDRS, yes), building + land value (yes) — **no sale date/price field, no permit/new-construction flag** (parcel snapshot, same limitation pattern as Bernalillo).
- **Coverage:** not row-counted in this pass (service confirmed live and returning full field schema); reasonably assumed county-wide (Doña Ana County has ~100k+ parcels historically).
- **Access limits:** No API key observed. Standard Esri paging.
- **Recommended recipe:** pair with the Las Cruces Building Permits layer (#3) — permits give you the "new multifamily construction" event, this parcel layer gives you the owner/mailing address to reach them.

---

## 5. Santa Fe County — Parcels (ArcGIS FeatureServer)

**System type:** arcgis (county-assessor-flat-file via Esri)

- **Query URL:**
  `https://gis.santafenm.gov/server/rest/services/Neighborhood_Associations_MIL1/FeatureServer/2/query?where=1=1&outFields=*&f=json`
- **Fields (~90 total, trimmed):** OBJECTID, UPC, situs_city, situs_zip, situs_line_1/2/3, owner_name, owner_care_of, owner_line_1/2/3, owner_city, owner_state, owner_zip, subdiv_name, property_class, current_market_land_res/comm, current_market_imp_res/comm, current_assessed_land, current_assessed_imp, current_exemption, is_affordable_housing (flag), neighborhood_name, etc.
- **Has:** owner name + full mailing address (yes), situs/property address (yes), assessed land + improvement values split by residential/commercial (yes, more granular than Bernalillo) — **no sale date/price, no permit/new-construction field.**
- **City of Santa Fe building permits:** Searched the city's own GIS server (`gis.santafenm.gov/server/rest/services/EnerGov_MIL1/MapServer` and `Public_Viewer/MapServer`, both confirmed live with 34 layers). **No building-permit layer exists in either service** — only Short Term Rentals, Address Points, Parcels, Fire Hydrants, Zoning, Historic Buildings, Overlay Districts, and Code Enforcement layers. The city's actual permit system (`santafenm.gov/land-use/building-permits`) is a plain web page, not a queryable API.
- **Recommended alternative for Santa Fe permits:** none found as machine-readable. Closest fallback is the NM MFA LIHTC award list (#6, statewide, names specific Santa Fe projects when they get tax credits) or manually checking the city's permit search page.
- **Access limits:** No API key. Standard Esri paging.

---

## 6. Statewide — NM Mortgage Finance Authority (MFA) LIHTC / Housing Tax Credit Awards

**System type:** flat-file (Excel download, not an API)

- **URLs (all confirmed live, .xls/.xlsx downloads):**
  - `https://housingnm.org/uploads/documents/2001-2026_Housing_Tax_Credit_Awards_05.22.2026.xlsx` (cumulative award list, 2001–2026)
  - `https://housingnm.org/uploads/documents/2001-2026_4__LIHTC__Applications__Updated_08.28.2026.xls` (4% credit applications)
  - Prior-year equivalents also live at the same path pattern (`2001-2025_...`, `2001-2024_...`).
- **What it contains:** award year, project name, city/county, developer/sponsor name, unit count, credit amount — this is the one source that **names specific upcoming apartment projects and their developers before/as they break ground**, statewide, not filtered to any one city.
- **Has:** address/city (yes, project location), date (award year), unit count (yes, typically), valuation (credit dollar amount, not construction valuation), developer/owner name (yes — this is the strongest "who to call" field of any source here).
- **Access limits:** No API, no key — it's a downloadable Excel workbook, updated periodically (several times a year as award rounds close) rather than live-queryable. Treat as a periodic manual/scripted download-and-parse, not a real-time feed.
- **Recommended recipe:** ckan/flat-file pattern — download the current-year xlsx on a schedule (e.g., monthly), diff against the last pull, alert on new rows.

---

## Cities/sources with NO usable machine-readable feed found

- **Rio Rancho building permits:** No open-data or ArcGIS feed exists for permits. The city only publishes GIS layers for Parcels/Streets/Zoning/Parks/etc. as shapefile/KMZ downloads (`rrnm.gov/2334/GIS-Data-Download`) — no permit layer among them. Permits are handled through **Accela Citizen Access** (`https://aca-prod.accela.com/CITYOFRC/Cap/CapHome.aspx`), which is a search-and-browse ASP.NET portal with no public JSON API (confirmed by fetching the page — it's a stateful web form, not a REST endpoint). **Closest alternative:** Sandoval County Parcels (below) for ownership, or manual/scraped Accela search as a last resort (not recommended — no stable query URL).
- **Rio Rancho / Sandoval County parcels (partial substitute):** `https://services3.arcgis.com/CkhxOCyQmitz4nLa/arcgis/rest/services/Sandoval_County_Parcels/FeatureServer/0/query?where=1=1&outFields=*&f=json` — confirmed live, 151,990 rows, service name `AssessorGIS_PROD.DBO.sc_parcels`. Fields: OBJECTID, Account_No, Owner_List, Lat, Long, Block, Unit, Sub, Lot, Tract, Parcel, Parcel_ID, Acrage, Model_Cond, Reception_ (recording number), Shape__Area/Length. **Limitation: no situs street address field** — only Lat/Long plus legal-description fields (Block/Lot/Tract/Sub), so you'd need to reverse-geocode Lat/Long to get a street address. Has owner name (Owner_List) but no permit/new-construction flag and no sale date/price.
- **New Mexico Construction Industries Division (CID), statewide permits:** No open-data portal found. Confirmed CID only administers commercial permits statewide and residential permits in areas without their own building department — Albuquerque, Santa Fe, Las Cruces, and Rio Rancho all administer their own permitting locally (this is why the four city-level sources above are the real path, not a CID statewide feed).

---

## Recommended recipe summary

| Source | Type | Best for |
|---|---|---|
| ABQ City Building Permits FeatureServer (#1) | arcgis | New multifamily construction leads in Albuquerque — richest filter (`TypeofStructure` apartment tiers) |
| Bernalillo County Assessor Parcels (#2) | arcgis / county-assessor-flat-file | Owner name + assessed value lookup for any ABQ parcel (no sales/permit data) |
| Las Cruces Building Permits (#3) | arcgis | New multifamily construction leads in Las Cruces (`PropUseGrp` filter) |
| Doña Ana County Parcels (#4) | arcgis / county-assessor-flat-file | Owner/mailing address lookup to pair with #3 |
| Santa Fe County Parcels (#5) | arcgis / county-assessor-flat-file | Owner/value lookup only — no permit feed exists for Santa Fe |
| NM MFA LIHTC Awards (#6) | flat-file (Excel) | Statewide pipeline of named upcoming apartment projects + developer contacts, including Santa Fe and Rio Rancho when they win credits |
| Sandoval County Parcels | arcgis | Weak substitute for Rio Rancho — owner name only, no address, no permits |
