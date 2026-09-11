---
name: find-apartments
description: Skill 1 of PropertyStack. List every apartment community (20+ units) in an area from county appraisal records, the complete denominator for everything else. Use when starting a new area or refreshing the apartment list.
---

# find-apartments

**Reads:** Collin CAD 2026 appraisal data (free public API, no key):
`https://data.texas.gov/resource/5tkr-3759.json`
**Writes:** `data/<area>/1-apartments.csv` (columns in `CONTRACTS.md`) + a run log in `runs/`

## Run
`python3 skills/find-apartments/run.py --area plano-richardson --cities PLANO,RICHARDSON`

## What it does
1. Pulls parcels in the cities with 20+ units that are either category `B`
   (multifamily) or use code `MFU`/`MFUSE` (multifamily the county coded as
   commercial; the old filter missed 9 of these, e.g. Bel Air Oaks, The Dayton).
2. Merges parcels of one community by normalized name + city (strips
   "Apartments", "Phase II", "Building E"…). `apt_id` = the lowest parcel id.
3. **Fallback merge (added 2026-09-10, see evals/review-weak-spots.md):** if two
   name-groups in the same city share the exact same normalized street address,
   they're merged into one community even though their names differ (e.g. "Bridge At
   Heritage Creek" / "...Creekside" at 1550 W Plano Pkwy; "Cortland Prairie Creek" /
   "...Villas Ii" at 3560 Alma Rd; "Link At Plano" / "Bel Air K Station" at 1013 15th
   Pl — the last one is a confirmed rebrand, same site, verified live). This only
   fires on an exact address match, not name/owner similarity — a shared owner and
   deed date can also mean two genuinely separate sites sold together in one
   portfolio transaction, which is NOT a reason to merge.
4. Writes one row per community: name, address, city, zip, units (summed),
   year built (earliest), owner, parcel count, all parcel ids.

## Check after running
- Count per city is printed and logged. Plano+Richardson (Collin) ≈ 200 communities.
- Skim for remaining near-duplicates (same/similar name, no address match) the
  fallback merge doesn't catch. **Not an example of one:** "Breckinridge Point"
  (4250 E Renner Rd) vs "Breckenridge Point" (3500 North Star Rd) — investigated
  2026-09-10, confirmed via live search to be two different addresses/streets with
  no evidence of a shared site; left unmerged on purpose despite the near-identical
  name and same owner/deed date (portfolio sale, not a duplicate parcel).

## Limits
- Category `B`/`MFU`/`MFUSE` filtering relies on Collin CAD's own categorization to
  exclude hotels/motels/assisted-living/mobile-home parks — there's no explicit
  exclude clause in `run.py` for those, so a CAD miscategorization would pass through
  uncaught.

## Dallas County mode (Richardson's Dallas County side)

Dallas CAD (DCAD) has no Socrata/REST API (unlike Collin CAD) — only free bulk ZIP
downloads at https://www.dallascad.org/dataproducts.aspx. `run_dallas.py` downloads
and parses that ZIP directly instead of querying an API. See
`skills/find-apartments/run_dallas.py`'s docstring for the DCAD schema details
(SPTD code `B11` = MFR-Apartments, joined across `ACCOUNT_APPRL_YEAR.CSV` /
`ACCOUNT_INFO.CSV` / `COM_DETAIL.CSV`).

### Run
```
# 1. Download the current-year DCAD bulk ZIP (~186MB; not committed to git):
mkdir -p propertystack/data/raw/dcad
curl -sL -o propertystack/data/raw/dcad/DCAD2026_CURRENT.ZIP \
  "https://www.dallascad.org/ViewPDFs.aspx?type=3&id=%5C%5CDCAD.ORG%5CWEB%5CWEBDATA%5CWEBFORMS%5CDATA%20PRODUCTS%5CDCAD2026_CURRENT.ZIP"

# 2. Run it:
python3 skills/find-apartments/run_dallas.py --area plano-richardson --city RICHARDSON \
  --zip-path data/raw/dcad/DCAD2026_CURRENT.ZIP
```

**Writes:** `data/<area>/1-buildings-dallas.csv` — same columns as `1-apartments.csv`
plus a `county` column (Collin's file has none, since it's Collin-only; this file is
always `county=Dallas`). Kept as a separate file, not merged into `1-apartments.csv`.

**Result for plano-richardson (2026-09-10):** 52 communities, 10,648 units. Spot-checked
5 names/addresses/unit-counts live (Camden Buckingham, La Mirada, Junction at Galatyn
Park, Cutter's Point, Prestonwood Apartment Homes) — all confirmed real Richardson
communities at the listed address; Prestonwood's unit count (194) matched exactly.
Checked for overlap with `1-apartments.csv` by name+address and by name alone — none.

### Limits (Dallas mode)
- Only covers `--city RICHARDSON` (DCAD's `PROPERTY_CITY` field) — not a full-county run.
- No fallback for hotel/senior-living miscategorization under SPTD `B11`, same caveat
  as Collin mode (one row in the output, "Twin Rivers Senior Living", is senior housing
  that DCAD itself categorizes as B11 apartments — left in since the CAD source codes
  it as multifamily, same policy as the Collin skill leaving CAD miscategorizations
  uncaught).
- DCAD's own `NUM_UNITS` field lives on `COM_DETAIL.CSV` per building/component within
  an account; parking garages/retail components have `NUM_UNITS=0` and are excluded
  from the sum but not from the merge (they don't create phantom communities since
  they're dropped before merging).
