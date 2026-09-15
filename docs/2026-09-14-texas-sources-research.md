# Texas lead-finder sources (live-tested 2026-09-14)

## Statewide
- TDLR TABS: POST https://www.tdlr.texas.gov/TABS/Search/SearchProjects (form: draw=1&start=0&length=100&ProjectName=apartment&RegistrationDateBegin=09/01/2024&DataVersionId=900001) → JSON (ProjectNumber, ProjectName, FacilityName, City/County codes, TypeOfWork 9001=New Construction, EstimatedCost, EstimatedStart/EndDate, ProjectStatus). Detail HTML: GET /TABS/Search/Project/<ProjectNumber> → address, scope, sq ft, owner name/address/phone, design firm. 51,061 regs since 2024-09; "apartment" 203, "multifamily" 35, "lofts" 29, "senior living" 24. 100 rows/page. Current to the day. No unit field (units from scope text/sq ft only; never estimate).
- TDHCA HTC inventory: tdhca.texas.gov/sites/default/files/multifamily/docs/HTCPropertyInventory_2.xlsx (3,297 rows; units, address, lat/long, construction type; 200 new-construction approved since 2024). 4% status log: .../htc-4pct/2026260803-4HTC-StatusLog.xlsx (41 deals, applicant phone). Affordable only.
## Cities / counties (permits)
- Austin Socrata data.austintexas.gov/resource/3syk-w9eu.json: permittype='BP' AND work_class='New' AND housing_units>=20 → 176 permits / 13,713 units since 2024-09. Daily.
- San Antonio CKAN datastore_search_sql data.sanantonio.gov; resources c21106f9-…7512 (2025+), c22b1ef2-…aab (2020-24); "PERMIT TYPE"='Comm New Building Permit' + project-name keyword → 65 apartment-like (2025-26). No units.
- Fort Worth ArcGIS services5.arcgis.com/3ddLCBXe1bRt7mzj/.../CFW_Open_Data_Development_Permits_View/FeatureServer/0: Permit_SubType='New' AND Specific_Use LIKE '%partment%'; Units (text), owner, status; 569 with 20+ units in first 1,000 rows (page!).
- Arlington gis2.arlingtontx.gov/agsext2/rest/services/OpenData/OD_Property/MapServer/1: MainUse LIKE 'Apartments%' AND WORKDESC='New Construction' → 216 since 2024-09. No units.
- Houston weekly "Sold Permits" xlsx from houstonpermittingcenter.org/sold-permits-search (e.g. files/2026-09/Sept%207-13.xlsx): Zip, Date, Type, Project No, Address, Comments; filter NEW + R2/R-2/APART. No units. ~32 weekly files.
- San Marcos smgis.sanmarcostx.gov/.../CoSM_BuildingPermits/FeatureServer/0 TYPE='New'.
- Tarrant County (all cities) TAD tad.org/content/data-download/2026CommPermits.zip: Intended Use "Apartments", Total Units, value, description, city → 381 apartment rows.
- Stale/unusable: Dallas Socrata (ends 2019; Accela only), Irving (Feb 2025), McKinney (2023), Denton County (Jul 2025). Not found: Frisco, Denton city, Round Rock, Georgetown, Katy/Harris, Travis/Williamson. Skip Collin (already done). "Grand Prairie Permits" on ArcGIS = Grande Prairie, Alberta — exclude.
## Sold (non-disclosure state)
- TAD 2026CommImprovedSales.zip "Apartment" sheet: 48 sales with price, units, $/unit, cap rate, deed doc #. Best TX sold source (also 2025 file).
- DCAD DCAD2026_CURRENT.ZIP (195MB, dallascad.org/DataProducts.aspx): DEED_TXFR_DATE, owner+mailing, COM_DETAIL NUM_UNITS, PROPERTY_NAME, PCT_COMPLETE → 680 apartment deed transfers since 2024-09 (no price) + 107 new/under-construction 20+ unit complexes (21,118 units) = Dallas pipeline.
- HCAD download.hcad.org/data/CAMA/2026/Real_acct_owner.zip (212MB): deeds.txt (dos, doc id), real_acct state_class B1 multifamily, new_own_dt, new_construction_val, permits.txt → 663 B1 deeds since 2024-09. Filter by building area to drop duplexes.
- TCAD 403 to curl (unverified). News (DBJ/Bisnow) via search for prices.
