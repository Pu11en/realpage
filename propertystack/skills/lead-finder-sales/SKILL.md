# lead-finder-sales (F5: recently sold, from the county's sales file)

Not the same as `lead-finder-sales-news` (news-based sale mentions). This skill
reads a county assessor's own sale-affidavits flat file, joined to its parcel
file, to find apartment properties (20+ units) that actually sold in the last
24 months, with buyer/seller/date/price straight from the county record.

Input: an area slug, and a recipe from `propertystack/recipes/<area>/*.json`
describing the two source files, their field names, the apartment
type/use-code value(s), the join key, and the unit-count and recent-sale
thresholds (see `maricopa-county-sales.json`). Output: one `LeadRecord` (see
`docs/LEAD-FORMAT.md`) per qualifying sale, stage `"sold"`.

## Rules

- The apartment/multifamily signal always comes from the recipe's
  `type_code` field + `apartment_type_codes` list -- never guessed or
  hardcoded in this file. Maricopa County's own file spec prints the human
  label right next to the code (`PROPERTYTYPECODE=E` ->
  `PROPERTYTYPEDESCRIPTION="Apartment Building"`), confirmed live.
- Units almost never live in the sales file itself -- they're looked up in a
  second "parcel" file via `parcel_fields.parcel` == `sales_fields.parcel`
  (the recipe's join key). A sale with no unit count on file, or fewer than
  `min_units`, is dropped, never estimated.
- Only sales within `recent_months` (default 24) of "today" are kept; older
  or undated rows are dropped.
- Code here is entirely area/county-agnostic: field names, use codes, URLs
  and thresholds all come from the recipe. Any other county with a sales file
  + a parcel file (joinable by parcel number) can add a recipe with no code
  changes.
- `find_sold()` takes an injected `fetch_rows` callable (same DI shape as
  `find_upcoming`'s `http_get`) so the pytest suite stays network-free.
  `default_fetch_rows` (real zip-download-and-parse) is only used by
  `live_self_test.py`.

No place names anywhere in `find_sold.py` -- county/state/field names/codes
are always caller-supplied via the recipe.
