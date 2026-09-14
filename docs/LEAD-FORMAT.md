# Lead record format

One record per apartment project/building, used by every part of the lead finder
(`propertystack/skills/lead-finder/record.py`, class `LeadRecord`). Saved/loaded as JSON,
one file per step, one list of records per file.

## Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `area` | string | State slug, e.g. `"az"`. Never a literal in code -- always data. |
| `city` | string | City name (or unincorporated county area). |
| `name` | string | Project/building name if known, else blank. |
| `address` | string | Street address as found. |
| `lat`, `lon` | float or null | Geocoded coordinates, null until geocoded. |
| `units` | int or null | Unit count. A project with unknown units is dropped by the permit step rather than kept as null (see PLAN-lead-finder-build.md 2.4/2.5). |
| `stage` | string | One of, in advancing order: `planned`, `permitted`, `under construction`, `leasing`, `sold`. |
| `permit_date` | ISO date string or `""` | When the building permit was issued. |
| `opening_date` | ISO date string or `""` | Expected/actual leasing opening. Blank if not public. |
| `sale_date` | ISO date string or `""` | Sale/refinance date, for `stage: sold`. |
| `buyer` | string | New owner, for `stage: sold`. |
| `developer` | string | Developer or current owner. |
| `office_phone` | string | Office contact number. |
| `website` | string | Project/developer website. |
| `software` | string | `"RealPage"`, a named competitor, `"not picked"`, or `"unknown"`. |
| `links` | dict | Any of `map`, `permit`, `agenda`, `news`, `website` -> URL. |
| `sources` | list of `{"fact": ..., "url": ...}` | One entry per sourced fact -- never guess, always cite. |
| `why` | string | One-line reason this is a lead (filled by `score-leads`). |

## Rules

- Never invent a fact. An unknown value stays blank/`null`/`"unknown"`; it does not get a
  guessed placeholder.
- Every fact this skill writes carries a `sources` entry with the URL it came from.
- `stage` only moves forward through `STAGE_ORDER` (`record.STAGE_ORDER`) during a merge --
  see `merge.py`. A planned project that gets a permit is upgraded to `permitted`, not
  duplicated as a second record.

## Merging (`merge.py`)

Two records describe the same building, and are merged into one, when either:

- their addresses normalize to the same string (`record.normalize_address` -- lowercases,
  collapses whitespace, expands/collapses common street-suffix abbreviations, and drops
  anything from a building/unit/suite qualifier onward, e.g. `"123 Main St"` and
  `"123 Main Street Bldg B"` both normalize to `"123 main st"`), or
- their geocodes are within 75 meters of each other **and** they share a developer/name
  word.

The merged record keeps the most advanced `stage`, and keeps every `source` and `link` from
both records (the kept record's links win on key clashes).

## Sample area

`propertystack/data/_sample/` holds a small, clearly fake state area (`area: "_sample"`) used
only by later parts' tests -- never built into the real site or shown to Drew as a real area.
