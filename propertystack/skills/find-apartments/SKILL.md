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
3. Writes one row per community: name, address, city, zip, units (summed),
   year built (earliest), owner, parcel count, all parcel ids.

## Check after running
- Count per city is printed and logged. Plano+Richardson (Collin) ≈ 200 communities.
- Skim for near-duplicates the merge missed (e.g. "Breckinridge Point" vs
  "Breckenridge Point"). Note them for the eval golden set; don't hand-edit the CSV.

## Limits
- Collin County only. Richardson's Dallas County side needs Dallas CAD (not built).
- Excludes hotels, motels, assisted living, mobile-home parks on purpose.
