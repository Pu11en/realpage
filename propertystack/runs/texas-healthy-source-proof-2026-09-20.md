# Texas Healthy-Source Proof - S8/S9

Written 2026-09-20 for the Texas-only source audit. The question for every
source is: can someone selling software to apartment buildings call this lead
today? That requires a real building name, real street address, unit count, and
a genuinely recent date.

## Summary

- `tarrant-tad.json`: endpoint is not under-reading, but the recipe drops useful
  valuation and permit-detail fields. The source itself has name, address, unit
  count, city, and issue date.
- `tarrant-tad-sales.json`: endpoint is not under-reading. It is call-ready for
  sold apartment assets, but the source has no buyer, owner, phone, or city field.
- `arlington.json`: ArcGIS endpoint is measured healthy, but the city layer is
  data-thin. It publishes permit address/date/value, not a real project name or
  unit count, so it is not call-ready by itself.
- `tabs.json`: endpoint is not under-reading. Rows are statewide and generally
  call-ready when the detail page scope includes a unit count; some rows still
  have no units because TABS scope text does not always state them.
- `tdhca.json`: not under-reading, and the site does not present pure TDHCA rows
  as construction-started. These are planned affordable-housing awards and
  pipeline applications. The adapter drops several actionable date/contact fields,
  so the exact "why now" date is weaker than it should be.

## Source Counts And Freshness

### tarrant-tad.json

- Endpoint files checked: 2025 and 2026 Tarrant Appraisal District commercial
  permit ZIP workbooks.
- True endpoint rows across the workbooks: 10,859.
- Apartment rows in the endpoint: 767.
- Rows that are apartment, recent under the recipe window, and unit-qualified:
  235.
- Recipe output: 177 kept leads.
- Newest apartment issue date in endpoint: 2025-12-26.
- Verdict: no under-read finding. The kept count is lower than 235 because the
  lead merge collapses repeated same-building/same-address permit rows.

Fields the endpoint has that the lead output does not preserve:

- `Account`, `Site Number`, `Permit Number`
- `Permit Issued Value`
- `Total NLA`, `Total GBA`
- `Land-to-Building Ratio`, `Market Subarea`, `Neighborhood`
- `Site Class`, `Permit Type`, `Description`

Seller-needed fields:

- Kept: building name, street address, unit count, city, issue date.
- Dropped even though present: permit value and permit identifiers.
- Not present in the source: owner, owner contact, year built.

Independent row checks:

- `VENTURA APTS`, 2601 Furrs Street, Arlington, 476 units. Public listing:
  Northmarq transaction page for Ventura Apts lists 476 units at 2601 Furrs
  Street.
- `RIVERBEND`, 701 E Arkansas Lane, Arlington, 138 units. Public listing:
  ApartmentHomeLiving lists RIVERBEND at 701 E Arkansas Lane with 138 units.

### tarrant-tad-sales.json

- Endpoint files checked: 2025 and 2026 Tarrant Appraisal District commercial
  improved-sales ZIP workbooks.
- True endpoint rows across the apartment sheets: 176.
- Apartment rows with at least 20 units: 158.
- Rows since the recipe cutoff (`2024-09-01`) and not after today's date: 24.
- Recipe output: 24 kept leads.
- Newest sale document date in endpoint: 2025-09-30.
- Verdict: healthy. No count gap.

Fields the endpoint has that the lead output does not preserve:

- `PIN`, `Site Number`, `Neighborhood`, `Mapsco`
- `EYOC`, `Condition`, `Overall Rank`
- `NLA`, `GBA`, `Overall Physical Vacancy`
- `Sale Price per Unit`, `Sale Price per NLA`, `Sale Price per GBA`
- `SaleNOI`, `PGR per NLA`, `Sale Cap Rate`, `Reported Cap Rate`
- `Land SF`, `L:B`, `Proprietary`, `Multi-parcel Sale`, `RatioCd`,
  `Analysiscd`

Seller-needed fields:

- Kept: building name, address, unit count, sale date, sale price when present,
  deed document number.
- Dropped even though present: operating/valuation metrics such as vacancy, cap
  rate, price per unit, NLA/GBA, and appraisal identifiers.
- Not present in the source: buyer, owner, phone/contact, city, year built.

Independent row checks:

- `LANDMARK AT CROWLEY`, 305 W FM 1187, 267 units. Public listing: HAR lists
  Landmark At Crowley at 305 W FM 1187 with 267 units.
- `THE PARK AT ASHFORD`, 3500/3550 S Fielder Road, 144 units. Public listing:
  Live Here Housing and HAR list Park at Ashford with 144 units.

### arlington.json

- Endpoint checked: City of Arlington ArcGIS OpenData property layer query.
- True endpoint rows for the recipe query: 329.
- Apartment rows: 329.
- Aged-out rows: 129.
- Recipe output: 178 kept leads.
- Newest issue date in endpoint: 2026-09-02.
- Verdict: measured healthy, data-thin. The endpoint is not under-reading, but
  the rows are not call-ready without enrichment because the source publishes a
  permit address as `FOLDERNAME` and does not publish unit count or a real
  project/building name.

Fields the endpoint has that the lead output does not preserve:

- `ConstructionValuationDeclared`
- `FINALDATE`
- `SUBDESC`, `LandUseDescription`, `Structure`, `FOLDERCONDITION`
- `NameofBusiness`
- `PROPX`, `PROPY`, `PROPGISID1`
- `PlanningSector`, `ZoningUse`, `CouncilDistrict`, `Census`

Seller-needed fields:

- Kept: street address and issue date.
- Dropped even though present: construction value and final/CO date.
- Not present or not usable in the source: real building/project name, unit
  count, owner, contact, year built.

Independent row checks:

- City row `300 E STEPHENS STREET`/`340 E STEPHENS STREET`; public listing:
  JPI lists `Jefferson Stephens`, 300 E Stephens St, Arlington, with 324 units.
  This proves the address points to a real apartment project, but the source
  itself does not carry the name or unit count.
- City row `9584 EDEN ROAD`/neighboring Eden Road building permits; public
  listing: Stonehawk Capital lists `The Dawson`, 9584 Eden Road, Arlington, with
  273 units. This again proves the address is real, while the source still drops
  the seller-needed name/unit facts.

### tabs.json

- Endpoint checked: TDLR TABS search form, all configured keywords since
  2024-09-01.
- Keyword total rows reported by TABS: apartment 204, apartments 181,
  multifamily 35, multi-family 13, lofts 30, residences 12, flats 5, senior
  living 25.
- Unique rows across keywords: 319.
- Qualifying rows after type-of-work and cost filters: 130.
- Recipe output: 126 kept leads.
- Newest registration date found: 2026-09-17.
- Verdict: healthy. The small gap is not an under-read finding; keyword overlap
  and merge behavior explain why output is slightly below qualifying rows.

Fields TABS has that the lead output does not fully preserve:

- Search row: `EstimatedCost`, `ProjectStatus`, raw city/county codes,
  `DataVersionId`, `ProjectId`.
- Detail page: square footage, owner address, design firm address/phone, RAS
  data, full scope text.

Seller-needed fields:

- Kept when present: building/project name, address, city/county, registration
  date, estimated start/end dates, owner/developer name, owner phone, units when
  the scope text says units.
- Dropped even though present: estimated cost, square footage, owner address,
  design-firm details, RAS details, current project status.
- Weakness: not every detail page states a unit count in parseable text, so some
  TABS leads are real but not fully call-ready.

Independent row checks:

- `Floyd Casey Development VM-2 Retail/Apartments`, 914 S Valley Mills Dr,
  Waco, 32 units. Public listing: Zabalist lists a 3-story, 32-unit apartment
  building for this project.
- `Stargaze Apartments`, Brownsville, 206 units. Public listing:
  ApartmentHomeLiving lists Stargaze Apartments with 206 units, and the TDLR
  project detail says seven 3-story buildings totaling 206 units.

### tdhca.json

- Endpoints checked: TDHCA HTC Property Inventory workbook and the 2026-08-03
  4% HTC status-log workbook.
- HTC inventory total rows: 3,356.
- HTC inventory new-construction rows: 565.
- HTC inventory new-construction rows since `since_year` 2024: 200.
- Newest HTC inventory award year: 2027.
- Status-log total rows: 43.
- Status-log new-construction rows: 22.
- Status-log file date: 2026-08-03.
- Recipe output after merge: 212 kept leads.
- Verdict: not under-reading. These are planned affordable-housing awards and
  4% HTC pipeline applications, not proof that construction has started.

TDHCA presentation check:

- Raw TDHCA records are emitted with `stage="planned"`.
- Pure TDHCA site rows display `Planned (not permitted yet)`, not
  under-construction wording.
- Some final Texas site rows with TDHCA links display `permitted`,
  `under construction`, or `sold` only after merge with a separate source such
  as TABS or a sales source. That is merge enrichment, not TDHCA itself claiming
  construction started.

Fields TDHCA has that the lead output does not fully preserve:

- HTC inventory: `TDHCA#`, `Program Type`, `LIHTC Amt Awarded`, `LIHTC Units`,
  `Population Served`, `Project County`, `Zip Code`, `CMTS_ID`, `Notes`,
  `Latitude`, `Longitude`, `Date Added`, `Last Modified`, `Region`.
- Status log: `Full Application Submission Date`, `Board Meeting Date`,
  `Determination Notice Issuance Date`, `Application Status`,
  `Bond Reservation Date`, `Bond Expiration Date`, bond issuer contact/phone,
  applicant contact/email, requested/recommended HTC amounts, requested/
  recommended bond amounts, direct-loan and property-tax-exemption flags.

Seller-needed fields:

- Kept: building/development name, address, city, unit count, planned stage,
  applicant phone when coming from the status log.
- Partly kept: award year appears in the raw `why` text for inventory rows, but
  not as a structured date field.
- Dropped even though present: application/board/determination/bond dates,
  applicant email, contact names, affordability unit mix, funding amounts,
  latitude/longitude.
- Weakness: the source is usable as a planned-project feed, but many rows do not
  carry a precise seller-action date in the final site data. That is a real
  data-richness finding, not an under-read finding.

Independent row checks:

- `Huntington Place Senior Living Garland`, Garland, 204 units. Public listing:
  After55/Homes.com list Huntington Place Seniors Garland at 1540 Edgefield
  Drive with 204 units.
- `The Arboretum at Woodland Hills`, Houston/Humble area, 366 units. Public
  listing: Houston Chronicle affordable-housing listing names The Arboretum at
  Woodland Hills with 366 units; RentCafe lists the renamed/leasing property
  `Tapestry Woodland Hills` with 366 apartments.

## Bottom Line

No S8/S9 source is silently under-reading in the Dallas-style way. The largest
real caution is not count loss; it is seller usability:

- Arlington has live, recent permit volume but lacks unit count and real project
  names.
- TDHCA is correctly treated as planned awards, but drops exact action-date and
  funding/contact fields that would make those planned leads easier to call.
- Tarrant and TABS sources are broadly usable, with TABS unit counts dependent on
  how clearly the detail-page scope text is written.
