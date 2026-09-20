# Fort Worth development permits — source audit, 2026-09-20

Recipe: `propertystack/recipes/tx/fort-worth.json`
Layer: `CFW_Open_Data_Development_Permits_View/FeatureServer/0`
Question every finding answers: **can someone selling software to apartment
buildings call this lead today?** (real building name, real street address,
unit count, genuinely recent date)

## 1. What the endpoint actually holds

| measurement | value |
| --- | --- |
| `returnCountOnly=true` on the recipe's own `where` | **2,227 rows** |
| rows our fetch retrieves (3 paged requests) | **2,227** — paging is correct, nothing is lost here |
| `outStatistics max(File_Date)` / newest row seen | **2026-08-25**, 26 days old — the feed is live, not frozen |
| rows that pass the apartment test (units ≥ 20) | **640** |

Before this audit the recipe produced **1 lead** from those 640 rows.

## 2. Where the other 595 rows went

`find_upcoming` was instrumented to count every drop reason. Measured live:

| reason | rows |
| --- | --- |
| aged out (permit older than 24 months, no CO) | 45 |
| no usable date at all | 0 |
| filed at a stand-in address (`<submittal no> FOR REVIEW ONLY WAY`) | 218 |
| junk permit (pool, carport, reroof…) | 0 |
| **merged into a single bogus building** | **595 → 1** |

**The finding.** `Full_Street_Address` is **null on every row of this layer**.
`_build_record` read it with `str(row.get(key, ""))`, which returns the literal
text `"None"` when the key exists and holds null. Every one of the 595 rows
therefore carried the address `"None"`, `normalize_address` turned all of them
into `"none"`, and `merge_records` — correctly doing its job — collapsed the
entire city into one lead.

A second finding compounded it: no `fields.name` was mapped, so every row fell
back to `Specific_Use`, which the `where` clause pins to `"Apartment"`. All 595
rows were named "Apartment" as well as sharing one address.

This is a silent, general failure mode: **any** source whose mapped address
column holds null would have collapsed the same way, and would have looked
"worked" in the run log.

## 3. Real columns the layer has, and what we were dropping

Full column list: `Unique_ID, Count_, Permit_No, Permit_Type, Permit_SubType,
Permit_Category, B1_SPECIAL_TEXT, B1_WORK_DESC, Addr_No, Direction,
Street_Name, Street_Suffix, Street_Suffix_Dir, Full_Street_Address, Zip_Code,
B1_LOT, B1_BLOCK, B1_TRACT, B1_LEGAL_DESC, Owner_Full_Name, File_Date,
Current_Status, Status_Date, Location_1, JobValue, Use_Type, Specific_Use,
Units, SqFt, ObjectId`.

Dropped facts a seller needs, now mapped:

- `Addr_No` / `Direction` / `Street_Name` / `Street_Suffix` / `Street_Suffix_Dir`
  — the real address, since `Full_Street_Address` is always null.
- `B1_SPECIAL_TEXT` — the real project name ("The Calhoun", "Hughes House
  Phase 2", "Alexan Copper Ranch").

Still dropped, deliberately, and worth revisiting later:

- `Current_Status` / `Status_Date` — "Plan Review", "Issued", "Finaled". This is
  how far along a project is, and it is better evidence than the permit date.
- `Zip_Code` — we rebuild the address without it.
- `B1_WORK_DESC` — free-text scope, e.g. "New construction 4-plex".
- `JobValue`, `SqFt` — project size/budget.

## 4. The fix (contained)

1. `_row_address` in `find_upcoming.py` reads the mapped address column with
   `row.get(key) or ""`, so a null column is blank, not the word "None".
2. New optional `fields.address_parts` builds the address from separate
   columns when there is no whole-address column. Generic, not city-specific.
3. New `PLACEHOLDER_ADDRESS_RE`: rows the feed itself files at a stand-in
   address are dropped rather than sold as a real street. A *genuinely blank*
   address is not treated as a placeholder — some sources legitimately have
   named projects with no street yet (10 such leads exist in AZ).
4. `fields.name` mapped to `B1_SPECIAL_TEXT`, and a plan-review routing tag
   ("`X TEAM /// Spring Hill East`") is stripped off the front of the name.
5. Drop reasons are now reported in `stats`: `noDate`, `placeholderAddress`,
   `junkDropped`, `built`, `mergedAway` — so a suspect source names its own
   cause instead of leaving someone to re-derive it.
6. `run_area._source_signal` judges the keep ratio on `built` (rows that
   survived every quality filter, **pre-merge**) when the adapter reports it.
   Judging post-merge `kept` against raw rows calls a healthy source broken:
   one project here files one permit per building.

## 5. Result

| | before | after |
| --- | --- | --- |
| leads | **1** | **126** |
| usable permits before merge | 1 | 377 |
| alarm | `suspect` | healthy, no flag |

No other state is affected: across all published data, exactly one lead (the
single Fort Worth one) matched the null-address or placeholder patterns, and
none matched the routing-tag pattern. `check_lead_data.py` passes on 4 states /
1,917 leads; 628 tests pass.

## 6. Two rows verified against independent public listings

| our lead | independent source | match |
| --- | --- | --- |
| **The Calhoun**, 1000 JONES ST, **310 units**, permit 2024-12-11 | Resia's own portfolio page for Resia Calhoun: 12-storey high-rise at 1000 Jones Street, Fort Worth, **310 units** | name ✅ address ✅ units ✅ |
| **Hughes House Phase 2**, 1401 ETTA ST and neighbours, **302 units**, permit 2024-10-23 | Fort Worth Report, 3 Aug 2024: Hughes House second phase, "**302** mixed-income units", "located between **Avenue G and Pollard-Smith Avenue**" | name ✅ units ✅ street names ✅ |

Sources: <https://www.liveresia.com/portfolio/resia-calhoun>,
<https://fortworthreport.org/2024/08/03/second-phase-of-east-fort-worths-hughes-house-to-start-construction-in-fall/>

## 7. Open finding — NOT fixed, because the fix is not contained

**A scattered-site project becomes many leads, each claiming the whole
project's unit count.** Hughes House Phase 2 is a single 302-unit development
spread over ~23 addresses on Etta / Avenue G / Pollard-Smith. The layer repeats
`Units = 302` on every one of its permits, so it appears as **23 separate
302-unit buildings**. Of 126 Fort Worth leads, **84 are distinct project
names** — 42 leads are extra rows of a project already listed, and their unit
counts are the project total, not that address's.

Why it was not fixed here: the only place to fix it is `merge_records`, which
every source shares. A "same name + same unit count = same building" rule is
unsafe while `find_upcoming` still falls back to the *permit type* for a name —
two genuinely different buildings both named "New Multifamily" with the same
unit count would silently merge. Doing this properly needs the record to carry
whether its name is real or a fallback, which is a change to `LeadRecord` and
to every adapter. That is its own task, and it affects Austin, San Antonio and
the Arizona sources as much as this one.

**Also note:** the 218 dropped stand-in-address rows include real projects
(Hughes House Phase 2's plan-review submittals among them). They are dropped
because the city has not sited them yet, not because they are fake. If a
future task wants them, the route is to join them to the sited permits by
project name — the same unresolved problem as above.
