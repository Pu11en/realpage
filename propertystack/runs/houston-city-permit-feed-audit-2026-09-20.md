# Houston City Permit Feed Audit

## Decision

- **Keep Houston city permits enabled.**
- The feed is **not under-reading** after the contained fix: it reads all posted weekly spreadsheets and reports every missed file.
- Live result on **2026-09-20**: **34 posted files**, **34 read**, **13,780 raw permit rows**, **28 apartment-building rows kept**, **newest permit 2026-08-10**.
- Against `propertystack/data/tx/leads.json`, all **28 current city permit rows are unique versus HCAD** by normalized address.
- The useful value is narrow: the city feed adds **permit dates and building-level permit descriptions** that HCAD does not carry.
- The feed stays weak for sellers because it has **no owner/contact/valuation field**, and only **4 of 28 current rows include a unit count** in the permit comment.

## Comparison To Existing Texas Leads

- Existing Texas data file has **18 Houston city permit leads** and **378 HCAD-linked leads**.
- The current cleaned city feed produces **28 Houston apartment-building permit rows**.
- **0 of 28 overlap HCAD** by normalized street address.
- **16 of 28 overlap an existing non-HCAD city-feed row** in the current data file.
- **12 of 28 are new to the current data file** if the data is regenerated with this fixed reader/filter.
- The 28 city rows should not be compared as a replacement for HCAD's county file. HCAD supplies units for existing county-account buildings; this city feed supplies newer city permit events.

## Fields Kept And Dropped

- Kept from the city spreadsheet:
  - **Address** from `Address`
  - **Permit date** from `Permit Date`
  - **Permit description / lead name** from `Comments`
  - **Units** only when `Comments` states a pattern like `65 UNITS`
  - **Source week URL** internally while parsing
- Dropped or unavailable:
  - **Owner/contact**: not present in the weekly city permit spreadsheet.
  - **Developer/builder**: not present.
  - **Permit valuation**: not present.
  - **Structured building name**: not present; the recipe uses permit description text as the lead name.
  - **Reliable total project unit count**: not present except when the permit comment itself says units.

## Unit Count Findings

- The 13 no-unit Houston city rows already in `propertystack/data/tx/leads.json` are missing units because the city spreadsheet has **no unit-count column** and those permit comments do **not** state a unit count.
- Three of those old 13 are now removed by the tighter filter because they are not new apartment-building leads:
  - `2125 YALE ST` - generator at apartment.
  - `6007 MEMORIAL DR` - generator at apartment.
  - `1919 W MAIN ST` - apartment electrical service.
- One old no-unit row gained units from another source in the built data:
  - `1117 BLAND ST` - city comment lacks units, but TDHCA inventory supplies **103 units**.
- Current cleaned city feed has **24 rows without units**, all for the same reason: the comment describes a new apartment building but does not state unit count.
- Current no-unit city rows:
  - `16200 GALVESTON RD BLD 7` - `33303 SF NEW APTS BLDG#7 1-1-5-A2-B 21'IBC (10/13)`
  - `13350 PARK ROW DR BLD 1` - `NEW 38,878SF APT BLD W/AMENITY(2/19)1-4-5-R2/B/A3-A '21 IBC SP/FA`
  - `7900 EASTHAVEN BLVD BLD A` - `(M/5) 34,542 NEW APRTMNT BLDG W/SITEWRK 1-3-5-R2-B '21 IBC 13R SPK`
  - `7900 EASTHAVEN BLVD BLD B` - `(2/5) 20,376 NEW APARTMENT BLDG 1-3-5-R2-B '21 IBC 13R SPK/FA`
  - `7900 EASTHAVEN BLVD BLD D` - `(3/5) 20,376 NEW APARTMENT BLDG 1-3-5-R2-B '21 IBC 13R SPK/FA`
  - `7900 EASTHAVEN BLVD BLD C` - `(4/5) 20,094 NEW APARTMENT BLDG 1-3-5-R2-B '21 IBC 13R SPK/FA`
  - `7900 EASTHAVEN BLVD BLD E` - `(5/5) 20,094 NEW APARTMENT BLDG 1-3-5-R2-B '21 IBC 13R SPK/FA`
  - `1117 BLAND ST` - `NEW 99137 SF APARTMENT BUILDING/SITE 1-4-5-R2-A 21IBC SP/FA (M/3)`
  - `2611 SAINT CHARLES ST` - `77,578 SF/ NEW APARTMENT W/SITEWRK (M/3)1-4-5-R2/A3-A/21 IBC/SPK13`
  - `9149 BLACKHAWK BLVD BLD1` - `(M/6) 28,296 SF NEW SENIOR LIVING APT BLD. 1-3-5-R2-A '21 IBC SPK`
  - `3910 OLD SPANISH TRL BLD A` - `(M/6) 48,220 SF NEW APT BLD 1-4-5-R2-A '15 IBC NFPA13`
  - `3910 OLD SPANISH TRL BLD B` - `112,809 SF NEW APT BLD (2/6) 1-4-2-R2-B '15 IBC NFPA13`
  - `1415 ENCLAVE PKY BLD 3` - `(M/15) 101,916 SF NEW APARTMENT 1-4-5-R2-A 15'IBC SPK13`
  - `1415 ENCLAVE PKY BLD 4` - `(2/15) 65,630 SF NEW APARTMENT 1-4-5-R2-A 21'IBC SPK13`
  - `1415 ENCLAVE PKY BLD 5` - `(3/15) 88,023 SF NEW APARTMENT 1-4-5-R2-A 21'IBC SPK13`
  - `1415 ENCLAVE PKY BLD 1` - `(4/15) 55,551 SF NEW APARTMENT 1-4-5-R2-A 21'IBC SPK13`
  - `1415 ENCLAVE PKY BLD 2` - `(5/15) 120,638 SF NEW APARTMENT 1-4-5-R2-A 21'IBC SPK13`
  - `13704 PARK ROW DR BLD 4` - `64,482SF NEW APT BLD(M/22)1-4-5-R2-A '21 IBC SP/FA`
  - `13704 PARK ROW DR 1B` - `39,164SF NEW APT BLD(3/22)1-4-5-R2-A '21 IBC SP/FA`
  - `13704 PARK ROW DR BLD 2` - `54,552SF NEW APT BLD(4/22)1-4-5-R2-A '21 IBC SP/FA`
  - `13704 PARK ROW DR BLD 3` - `69,558SF NEW APT BLD(5/22)1-4-5-R2-A '21 IBC SP/FA`
  - `13704 PARK ROW DR BLD 5` - `73,516SF NEW APT BLD(6/22)1-4-5-R2-A '21 IBC SP/FA`
  - `13704 PARK ROW DR BLD 6` - `69,371SF NEW APT BLD(7/22)1-4-5-R2-A '21 IBC SP/FA`
  - `13704 PARK ROW DR BLD 7` - `81,614SF NEW APT BLD(8/22)1-4-5-R2-A '21 IBC SP/FA`

## Independent Checks

- **Washington Center Residences**: public pipeline listing reports `Washington Center Residences`, `3028 Center Street`, **169 units**, under construction; a newer public pipeline listing reports `3026 Washington Ave`, **341 units**. The city feed's four January permits for `3028 Center/Washington` carry **65 + 104 + 102 + 70 = 341 units**, matching the newer total and confirming these are real apartment-building permit rows.
- **1117 Bland St / New Hope Housing Wheatley**: public notices describe `1117 Bland Street` as a new construction supportive housing development with **103 apartment homes**. The city feed has the permit row but no unit count; the built data correctly fills **103 units** from TDHCA inventory instead of inventing it from the city feed.

## Code Changes Made

- Unwrapped weekly spreadsheet viewer URLs so the parser downloads the actual `.xlsx` file, not a viewer page.
- Added retry handling for rate-limited or transient spreadsheet downloads.
- Recorded posted files, read files, failed files, and raw row totals so missing weekly files become visible in source health.
- Let recipes provide local apartment vocabulary such as `APT`, `APTS`, and `R-2`.
- Tightened junk-permit filtering so garage apartments, generators, electrical service, condo buildouts, amenity centers, and common laundry/dining work do not become apartment-software leads.

## Remaining Risk

- This source is a rolling weekly spreadsheet feed, so older city permit history can disappear from the public page.
- Most current rows are not directly callable alone because **24 of 28 lack units** and **all 28 lack owner/contact fields**.
- The feed still adds useful lead timing, but S10 should mine county and bulk files for stronger seller fields.
