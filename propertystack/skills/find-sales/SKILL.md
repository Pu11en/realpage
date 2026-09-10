---
name: find-sales
description: Skill 5 of PropertyStack. Find apartment communities that changed hands in the last 24 months, from Collin CAD deed records and owner-name changes across appraisal rolls. Use after find-apartments, to flag recent-sale leads (new owner = likely software re-evaluation).
---

# find-sales

**Reads:** `data/<area>/1-apartments.csv` (for `cad_prop_ids`) + Collin CAD appraisal
data (free public API, no key):
`https://data.texas.gov/resource/5tkr-3759.json` (2026 roll)
`https://data.texas.gov/resource/vffy-snc6.json` (2025 roll)
**Writes:** `data/<area>/5-sales.csv` (columns in `CONTRACTS.md`) + a run log in `runs/`

## Run
`python3 skills/find-sales/run.py --area plano-richardson`

## What it does
1. For every parcel (`cad_prop_ids`) of every community in `1-apartments.csv`, batch-fetches
   `ownername`, `deedtypecd`, `deedeffdate` from the 2026 roll and `ownername` from the 2025
   roll ($where=propid in (...), chunks of 100).
2. A parcel is a **sale trigger** if either is true:
   - the 2026 deed type is in the warranty-deed family (`WD`, `SWD`, `WDNL`, `SWDNL`) and
     `deedeffdate` is within the last 24 months (>= 2024-09-10), or
   - the owner name differs (normalized: uppercase, punctuation stripped, `LLC`/`LP`/`INC`/
     `CORP`/`LTD`/`CO` removed) between the 2025 and 2026 rolls.
3. A community is SOLD if any of its parcels triggers. One row per community, using the
   trigger with the most recent `deedeffdate`. `previous_owner` = the 2025 owner name if it
   differs, else `"unknown (same owner name in 2025 roll)"`.
4. Non-sale deed types (quitclaim `QCD`, correction `CORRD`, affidavit-family, plats, etc.)
   never trigger a sale on their own.

## Check after running
- Counts are printed and logged: communities checked, parcels checked, sold, sold-by-deed,
  owner-changed-without-deed, deed types seen, excluded deed types seen.
- Spot-check a few `source_url`s directly — they're single-parcel Socrata queries against the
  2026 roll and should match `sale_date`/`deed_type`/`new_owner` in the CSV exactly.

## Limits
- Collin County only (same limit as find-apartments).
- Only compares 2025 vs 2026 rolls; a sale that happened and reversed within one roll cycle,
  or an owner-name change that isn't actually a sale (internal entity rename), can't be told
  apart from a real sale by this method alone.
- `deedeffdate` from the CAD roll can lag the actual closing date.
