# lead-finder-permits (part 2.4)

Rebuilds `find-upcoming` for any city, replacing the old single-city,
Legistar-only version. Input: a city, its state/area slug, and a recipe from
`lead-finder-sources` (2.2 catalog hit or 2.3 fallback). Output: one merged
`LeadRecord` (see `docs/LEAD-FORMAT.md`) per apartment project found in the
permit rows.

## Rules

- Only rows that look like apartments/multifamily (permit type/description
  match, or 20+ units) are kept.
- Stage comes from dates on the row, never guessed:
  - a certificate-of-occupancy issued in the last 6 months -> `leasing`
  - a permit issued in the last 24 months with no CO -> `permitted`
  - anything older, or with no usable date at all, is dropped
- Several permit rows for the same building are merged into one record
  (`lead-finder/merge.py`), keeping the permit link.
- Unknown units are kept as `None` for part 2.5 (`project-details`) to fill
  in -- never guessed here.

No place names anywhere in this code -- city/state/area are always
caller-supplied.
