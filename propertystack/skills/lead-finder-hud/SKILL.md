---
name: lead-finder-hud
description: PropertyStack lead finder part 3.1. Downloads HUD's free FHA multifamily firm-commitments/endorsements spreadsheet and filters it to one state's new-construction and refi/sale leads.
---

# lead-finder-hud

Part 3.1 of the lead finder chain (see `propertystack/skills/lead-finder/SKILL.md`), first
of Part 3's early-signal sources.

Downloads and caches HUD's free "FHA Multifamily Firm Commitments and Endorsements Database"
spreadsheet (published at https://www.hud.gov/hud-partners/multifamily-data, updated
quarterly) and filters its "Firm Commitments" sheet to one state's rows: 20+ units, in the
last 36 months, and only the two program codes the plan cares about:

- **221(d)(4)** (new construction) -> stage `permitted`
- **223(f)** (refi/purchase of an existing building) -> stage `sold`, why says
  "HUD refi or sale"

The program code shows up in the "Program Subcategory" column in a few spellings ("221(d)(4)",
"221D4", "221 (d)(4)"), so the match is a loose regex rather than an exact string.

Area-agnostic: no state or city name is hard-coded; state is always a caller-supplied
argument, and city names come straight from the spreadsheet's own data.

## Functions

- `fetch_workbook_bytes()` -- downloads the workbook once into
  `propertystack/data/raw/hud/` (gitignored) and reads from the cache after that.
- `load_sheet_rows(workbook_bytes)` -- parses the "Firm Commitments" sheet into
  `[{column_name: value}]`, skipping the title block above the real header row.
- `parse_hud_rows(rows, state, min_units=20, months=36, today=None)` -- the pure filtering
  logic, tested without touching the network or openpyxl.
- `find_hud_loans(state, ...)` -- the end-to-end entry point other steps call.

Never guesses a missing units count or activity date -- rows missing either are dropped, not
kept with a placeholder.
