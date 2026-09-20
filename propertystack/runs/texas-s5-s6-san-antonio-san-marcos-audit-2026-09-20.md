# Texas S5 And S6 Audit

## Bottom Line

- ✅ **San Antonio was a broken query, not a frozen feed.** The city permit feed is live through 2026-09-18, but the old recipe looked only for apartment words and missed the city's `AFF -` affordable-housing apartment filing code.
- ✅ **San Marcos was a contained query miss plus per-unit row granularity.** The old recipe read only `TYPE='New'`; the live layer also uses `TYPE='New Commercial'` for real multi-family projects.
- ⚠️ **Both sources still carry a seller risk.** Neither endpoint has a reliable aggregate unit-count field, so the leads are better than before but still not fully call-ready by the "building name + street address + units + recent date" standard.

## San Antonio Evidence

- ⏳ **True endpoint holdings:** the current San Antonio resource holds **143,731 rows** with newest `DATE ISSUED` **2026-09-18**; the 2020-2024 resource holds **368,297 rows** ending **2024-12-31**.
- ⬜ **Old recipe result:** the old apartment-word query returned **156 rows**, **154 apartment rows**, **2 kept leads**, **0 aged out**, newest **2025-11-24**.
- ✅ **Contained fix:** the recipe now also matches `PROJECT NAME ILIKE 'AFF -%'` in both CKAN resources and strips that filing prefix from lead names.
- ✅ **Current recipe result:** live run now returns **628 endpoint rows**, **628 apartment rows**, **29 kept leads**, **397 aged out**, **2 no-address rows dropped**, newest **2026-08-05**.
- ✅ **Why rows still collapse:** many permit rows are one building or one filing inside the same apartment project, so address merging is expected; the remaining suspect flag is not proof of lost paging.
- ⚠️ **Fields still dropped that a seller would want:** `AREA (SF)`, `DECLARED VALUATION`, `PRIMARY CONTACT`, and `PERMIT #`.
- ⚠️ **Unit-count gap:** the permit endpoint has no unit field. The city's separate affordable-housing-bond materials do publish unit counts for several `AFF -` projects, but that is a separate source and was not wired into this contained fix.
- ✅ **Independent checks:** `AFF - 1231 E COMMERCE ST - Central at Commerce` matches Central at Commerce at **1231 E. Commerce St.** with **279 units**; `AFF - 6210 SUN VALLEY DR / 6415 SW 410 - Heritage Estates at Medina` matches Heritage Estates at Medina with **86 units**.
- ✅ **Verification links:** Central at Commerce unit count was checked against Opportunity Home/TAAHP reporting (`https://homesa.org/`, `https://taahp.org/`); Heritage Estates at Medina was checked against TDLR/Zabalist public project references (`https://www.tdlr.texas.gov/`, `https://www.zabalist.com/`).

## San Marcos Evidence

- ⏳ **True endpoint holdings:** the layer holds **51,308 rows** total and **3,360 multi-family rows**; newest multi-family `ISSUED` is **2026-09-17**.
- ⬜ **Old recipe result:** `TYPE='New'` returned **168 rows**, **168 apartment rows**, **4 kept leads**, **1 aged out**, newest **2026-06-12**.
- ✅ **Contained fix:** the recipe now uses `(TYPE='New' OR TYPE='New Commercial')`, with the URL percent-encoded.
- ✅ **Current recipe result:** live run now returns **284 endpoint rows**, **284 apartment rows**, **8 kept leads**, **1 aged out**, newest **2026-07-16**.
- ✅ **What the added type found:** `New Commercial` added **116 rows** since 2024-09-01, including San Marcos Student Housing / Lindsey St Apartments and The Heritage at Cottonwood Creek.
- ✅ **Why rows still collapse:** the feed is per unit or per building, not per apartment project. The Village at Centerpoint Station alone contributes **161 apartment-number rows** at one building, so address merging makes kept leads much lower than raw rows.
- ⚠️ **Fields still dropped that a seller would want:** `PERMITID` and `PROJECTNUMBER` are useful source identifiers; `SQUAREFEET` exists but is per-unit floor area, not a project unit count or building size, so it remains unmapped.
- ⚠️ **Unit-count gap:** the layer has no aggregate unit count, owner, or contact field.
- ✅ **Independent checks:** San Marcos Student Housing / Lindsey St Apartments matches public reporting for the McLain student-housing development at Lindsey/North/Comanche; The Heritage at Cottonwood Creek matches public listings for **4530 Hwy 123** and **233 units**.
- ✅ **Verification links:** The Heritage at Cottonwood Creek unit count was checked against Community Impact and ApartmentFinder public listings (`https://communityimpact.com/`, `https://www.apartmentfinder.com/`).

## Code Changes

- ✅ `find_upcoming` can now use a recipe-specific apartment regex, so a city-specific filing code can be matched without hard-coding a city into shared code.
- ✅ `find_upcoming` now parses timestamp strings shaped like `2021-09-21 00:00:00`, so old rows are counted as aged out instead of disappearing as unparseable dates.
- ✅ `find_upcoming` drops rows whose address is blank, `None`, or `NULL`, so the run no longer creates impossible-to-call leads with a literal address of `None`.
- ✅ Regression tests cover all three behaviors and both recipe changes.

## Remaining Risk

- ⚠️ San Antonio and San Marcos are improved but still not fully seller-ready because the sources do not provide a real unit count on every emitted lead.
- ⚠️ San Antonio's separate affordable-housing PDF or another city source may be worth a later enrichment task, but that would be a new source integration rather than this contained fix.
- ⚠️ San Marcos may need a later project-level summarizer if Drew wants one row per development with inferred unit counts; this task deliberately did not infer units from permit-row counts.
