# Dallas County (Richardson) sources for v2 — research notes, 2026-09-10

Scope: extending find-apartments / find-sales from Collin CAD (Socrata API) to
Dallas CAD (DCAD) for the Dallas County part of Richardson.

## 1. DCAD property data (apartments/multifamily)

- **Data Products page** (verified live, fetched 2026-09-10):
  https://www.dallascad.org/dataproducts.aspx
  Free bulk downloads, ZIP files, two formats: **comma-delimited** and **fixed
  format**. Covers current + historical appraisal rolls (2022-2027), certified
  rolls, BPP detail, ARB records. No pricing shown = free. "Unable to provide
  technical support" for using the data.
- **GIS Data Products** (verified live): https://www.dallascad.org/gisdataproducts.aspx
  Shapefiles only (parcels, boundaries, subdivisions). No mention of an API
  (no Socrata/REST endpoint found — UNVERIFIED that one exists; unlike Collin
  CAD, I found no `data.texas.gov` Socrata resource for Dallas CAD in search).
- **No API confirmed**: the find-apartments/find-sales pattern relies on Socrata
  `$where`/`$select` querying against `data.texas.gov`. I could not find a
  Dallas CAD equivalent. **UNVERIFIED / likely does not exist** — v2 code would
  probably need to download and parse the DCAD bulk ZIP/CSV instead of querying
  an API.
- **Property use/category codes**: DCAD (like all Texas CADs) follows the state
  Comptroller PTAD classification: apartments/multifamily = **Category B**
  (same code Collin CAD uses; confirmed via PTAD Property Classification Guide
  and DCAD's own PTAD cross-reference PDF at
  https://www.dallascad.org/ViewPDFs.aspx?type=1&id=...PTAD_PROP_CLASS.pdf —
  page fetched but content is a binary PDF stream I could not read as text;
  its existence and filename were confirmed via search results, contents
  **UNVERIFIED**). Hotels/motels are Category F1, not B — so the same
  category-B filter used for Collin should carry over in principle.
- **DCAD's own use-code equivalents to Collin's `MFU`/`MFUSE`**: **UNVERIFIED** —
  did not find DCAD's internal use-code list; the bulk-download reference docs
  (bundled inside each ZIP, per the Data Products page) would define this and
  were not accessible without downloading.
- **File format details** (field names, whether a `situscity`/`imprvunits`-type
  schema exists): **UNVERIFIED** — only obtainable by downloading the ZIP.

## 2. Dallas County deed/sale records

- **Official portal** (verified live, and verified linked from the official
  Dallas County Clerk page): https://dallas.tx.publicsearch.us/
  Linked from https://www.dallascounty.org/services/record-search/ (verified
  live) as "UCC / Personal Property / Deeds."
  Searchable by grantor/grantee, subdivision, doc type, doc #, and date range;
  "Search Index Only" or "Search Index & Full Text (OCR)"; records certified
  through 09/08/2026 (site's own label at fetch time). Free to search (no
  paywall on the search step; certified copies are paid, per
  https://www.dallascounty.org/government/county-clerk/recording/, not
  independently re-verified here).
- This is a **document-level index/search UI, not a bulk dataset or API** — no
  evidence of a machine-readable export/download or Socrata-style endpoint.
  **UNVERIFIED** whether it has any API; find-sales-style batch querying by
  parcel ID would not work against it as-is.
- **Does DCAD's own property data include sale/deed dates?** **UNVERIFIED**.
  Collin CAD's Socrata rolls expose `deedtypecd`/`deedeffdate` per parcel,
  which is what find-sales relies on instead of touching deed records
  directly. Whether DCAD's downloadable roll includes equivalent fields is
  unknown without opening the ZIP's reference docs — this is the single most
  important unresolved fact for porting find-sales.

## 3. Mapping to existing skills / code changes needed

- **find-apartments** (`propertystack/skills/find-apartments/run.py`): hardcodes
  the Collin CAD Socrata endpoint (`5tkr-3759`) and its field names
  (`propid`, `dbaname`, `situsconcatshort`, etc.). If DCAD has no Socrata API,
  this cannot be a drop-in second `--area`/`--cities` run — it needs either
  (a) a new DCAD-specific fetch path that downloads/parses the DCAD bulk
  CSV/fixed-format file and re-maps its columns to the same output schema, or
  (b) confirmation a DCAD Socrata resource actually exists (not found here).
- **find-sales** (`propertystack/skills/find-sales/run.py`): depends entirely on
  Collin's two-Socrata-roll diff (`deedtypecd`/`deedeffdate` across 2025 vs
  2026). If DCAD's bulk data lacks those fields, find-sales for the Dallas
  side would instead have to query the Dallas County Clerk portal per-parcel
  (grantor/grantee or address search) — that portal has no confirmed batch/API
  access, so this would likely require per-parcel manual/scripted lookups
  rather than the current 1-2 bulk API calls, a materially different (slower,
  possibly rate-limited or ToS-restricted) approach.
- Both skills' SKILL.md already flag this gap explicitly: "Collin County only.
  Richardson's Dallas County side needs Dallas CAD (not built)."

## Bottom line / open questions for a build task

1. Confirm (by downloading one DCAD Data Products ZIP) whether it has a
   Socrata-equivalent schema, includes deed date/type per parcel, and what its
   use-code values are for apartments — this determines whether find-apartments
   can reuse the Socrata-query pattern or needs a file-download-and-parse path.
2. Confirm whether dallas.tx.publicsearch.us (or a paid layer like TexasFile /
   CourthouseDirect) exposes any batch/API access, since the free public UI
   appears to be single-record search only.
