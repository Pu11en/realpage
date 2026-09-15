# PropertyStack: Texas round 2 (Williamson, Bexar, College Station, Fort Bend)

Written 2026-09-14 with Drew (answers: `/home/drewp/main-projects/handoffs/2026-09-14-texas-round2-answers.md`;
live-tested sources: `docs/2026-09-14-texas-round2-sources.md` -- read it first). **Starts only when Drew says
"go work"**, after the Texas build (`PLAN-lead-finder-texas.md`) and the map build are merged, and **before**
`PLAN-texas-weekly.md` (so the weekly run also covers these sources). All lead-finder rules apply: area-agnostic
code (place specifics only in recipe data files), never guess facts, data first + web search last (Jina, then
Brave; keys in `/home/drewp/main-projects/realpage/.env` or the build copy's `.env`; never commit), SearXNG
banned, Collin County never touched, RealPage-gap ranking (rank, don't ban), no quality gates, commit after each
source (build copies delete uncommitted files), localhost only, never push.
- **Lessons from the first Texas run (Drew 2026-09-14):** keep only NEW apartment buildings or real sales
  of 20+ unit properties -- never remodels, carports, repairs or finish-outs on existing complexes; one row
  per project/complex (group permits or accounts by parcel / owner + street + date), never one per building
  number; a real project name when any field has one; normalized city names ("HOUSTON" = "Houston").
- All new rows go into the existing `tx` area and merge with rows already there (same address or same name
  in the same city = one row with every source listed).
- **Pre-approved, don't ask:** free public downloads and API calls; Jina up to 300 searches for enrichment of
  the new rows (software on existing buildings, missing developer phones only); Brave under its 800/month cap.

Run with: `Do the next unticked task in PLAN-texas-round2.md, then tick it and stop.`
Check: `bash tooling/qa/check-lead-finder.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765 → Early Leads → Tx

## How to try it (30 seconds)
1. Early Leads → Tx, city filter: Round Rock, Georgetown, College Station, Sugar Land/Katy and San Antonio-area towns now show leads.
2. Open a Williamson or Bexar lead: real name or address, unit count or building size, and its public record link.
3. No carports, repairs or one-row-per-building duplicates in the new rows.

## Tasks

- [ ] **R1 Williamson County (Socrata, data.wcad.org).** Recipe (data) + adapter if needed: building permits
  table `fqhf-gyjx` since 2024-09 for new multifamily / apartment construction; property + characteristics
  (`ij43-xknu`, `cvyp-ab5t`) for the multifamily state class (read the layout PDF at
  `documents.wcad.org/DataDownloads/` to confirm the class code, likely B1/BCOM-MF), year built ≥ 2024 or
  new improvement value → new projects; sale table `pvyy-mm8r` since 2024-09 on multifamily accounts →
  sold (buyer, date). Drop under 20 units (or under the building-area cutoff when units are unknown). Live
  self-test ≥1 row. Pull, merge into `tx`, commit.
- [ ] **R2 Bexar County (ArcGIS, maps.bexar.org Parcels layer 0).** Recipe: `State_cd='B1'`, `YrBlt >= 2024`
  (new) → projects with owner, situs address, building area (`GBA`/`TOT_GBA`), stories; page past the
  layer's row limit; skip parcels already in the San Antonio permit rows (merge instead). Check whether
  the layer has a deed/sale date field; if yes, add recent sales, else note "Bexar sales: no field" in the
  source notes. Live self-test. Pull, merge, commit.
- [ ] **R3 College Station (Socrata, data.cstx.gov `hrbn-znt6`).** Recipe: issued since 2024-09,
  `upper(permit_description) like '%APARTMENT%'` (plus MULTI-FAMILY / MULTIFAMILY), new-construction work
  types only (drop remodels/repairs); one row per project; units from a field or the description text,
  else "Units: not public yet". Live self-test. Pull, merge, commit.
- [ ] **R4 Fort Bend County (FBCAD zip files, fbcad.org/data-files/).** Find the latest full certified
  export (not only a small supplement) and its layout; recipe for multifamily state class accounts that are
  new (year built / new value) → projects, and deed dates since 2024-09 → sold. Cache the zip under
  `propertystack/runs/cache/` (gitignored); re-download only when the file list changes. If only
  supplements exist, use them and note it. Pull, merge, commit.
- [ ] **R5 Enrich + rank the new rows.** Data-first enrichment for new rows only (software on existing /
  sold buildings, developer phone when no record has one), RealPage-gap ranking, then the Texas QA report
  (report only). Log per-source counts (rows kept, dropped as small, dropped as repairs, merged) in the
  progress log. Commit.
- [ ] **R6 Site + chat.** `bash tooling/dev.sh`; run the Check and `tooling/qa/check-answers.sh`. Commit.
  Recap in plain words for Drew: new Texas leads by county/city and by source, how many sold vs new, how
  many with units, phone and software, searches used.
