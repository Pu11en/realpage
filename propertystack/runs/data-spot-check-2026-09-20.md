# Spot check of the published lead data — 2026-09-20

Scope: the 498 `stage: sold` leads and the freshness of every lead now on the site
(1,464 rows across tx/az/nm/ny). Verified against the live sources, not against our
own copies.

## Verdict

The sold leads are real. Three of three sampled buildings checked out against
independent public listings, including an exact unit-count match:

| our row | reality |
| --- | --- |
| `4030 N 44TH AVE`, 256 units, sold 2026-08-01, buyer LEGACY MULTIFAMILY HOLDINGS LLC | Cove on 44th, 256 units, sold for $22.6M on 2026-08-14 |
| `100 DETERING ST 383`, buyer VIRAGE APARTMENTS OWNER LLC, sold 2024-12-09 | Virage, 100 Detering St, Houston — real apartment community |
| `9757 WINDWATER DR 150`, buyer HM WINDMILL LAKES JV LLC, sold 2025-09-18 | Compass at Windmill Lakes, 9757 Windwater Dr, **150 units** |

No fabricated or non-apartment rows were found. The problems below are presentation
and freshness, not invented data.

## Confirmed defect: Houston addresses carry a unit count

HCAD's `real_acct.txt` builds `site_addr_1` as street address + `str_unit`. Verified by
range-reading the zip's central directory and inflating the first 6 MB of
`real_acct.txt` (no full 212 MB download): of 903 `state_class=B1` rows in that chunk,
875 have `str_unit` filled and **875 of 875 match the trailing number in
`site_addr_1` exactly**. Building area divided by that number lands at
940–1,110 sqft per unit on the large properties — apartment-sized.

So `str_unit` is the unit count for Houston multifamily, and it is glued onto the
address we display.

- **372 Texas leads** (324 sold, 48 under construction) show an address with a unit
  count stuck on the end: `803 DUNSON GLEN DR 36`, `1315 NASA RD 1 490`.
- **All 372 of them report `units: null`** while the number sits in the string we
  already publish, and in a column of a file we already download.

Fix: split the trailing integer off `site_addr_1` for `B1` rows, or read `str_unit`
(column index 16) directly, and use it as the unit count. `houston-hcad.json` states
"There is no NUM_UNITS-equivalent column in this file at all" — that is wrong for B1
rows and should be corrected with the recipe.

## Confirmed defect: "just" is doing too much work

The site hero reads *"N buildings just filed permits, N just sold"*. Measured against
today (2026-09-20):

- Sold leads: **16 of 498** sold within 180 days. Median age **479 days** (~16 months),
  oldest **744 days**.
- Texas sold: **0 of 359** within 180 days; the newest Harris County sale in our data is
  2025-12-30, about 9 months old.
- Arizona sold: 16 of 139 within 180 days.
- Permit-stage leads with a date: **123 of 653** within 180 days, median **468 days**.
  313 permit-stage leads carry no date at all.

Either the window narrows, or the wording stops saying "just".

## Confirmed defect: Arizona sale dates claim a precision they do not have

All 139 Arizona sale dates fall on the 1st of a month — the county file is month-level.
Cove on 44th is stored as `2026-08-01`; it actually sold `2026-08-14`. Showing a day
overstates what the source knows. Say "August 2026".

## Confirmed defect: the hero numbers do not match the files

`site/data/summary.json` says 1,462 tracked / 936 permits / 526 sold. The area files
hold **1,464** leads, **966** non-sold, **498** with `stage: sold`.

- The 526 counts `signalType == "Sold"`, which includes **28 legacy Plano/Richardson
  rows that have no `saleDate` at all** (their signal is free text like "Sold Jun 2026"
  or "Owner changed to …").
- `newLast7Days` is **1,462** — every lead. `firstSeen` is being stamped on the whole
  set, so "new this week" means nothing.
- summary.json is also stale by 2 rows; it was not rebuilt after the last area build.

## Smaller items

- `Breckinridge Point Apartments` and `Breckenridge Point Apartments` are both listed —
  one building, two spellings, not merged.
- 41 site leads have no `stage`.
- 358 of 359 Texas sold leads and all 139 Arizona sold leads have no office phone.
- Texas gained exactly 1 lead in the last run (a San Antonio permit). No junk was added.
