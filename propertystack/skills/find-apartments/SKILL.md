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
- Collin County only. Richardson's Dallas County side needs Dallas CAD (not built).
- Category `B`/`MFU`/`MFUSE` filtering relies on Collin CAD's own categorization to
  exclude hotels/motels/assisted-living/mobile-home parks — there's no explicit
  exclude clause in `run.py` for those, so a CAD miscategorization would pass through
  uncaught.
