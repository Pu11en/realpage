---
name: lead-finder-awards
description: PropertyStack lead finder part 3.2. For any state, finds its housing agency's tax-credit/bond award list and turns new-construction awards into planned-stage leads.
---

# lead-finder-awards (part 3.2)

For any state, its housing finance agency publishes tax-credit (LIHTC) and bond award
lists -- these are projects that got funding but are not permitted yet, so they surface
leads well before permits or agendas do.

There's no single free API for this (unlike HUD's spreadsheet), so this part searches:
`"<agency name> housing tax credit awards 2025"` / `2026` and `"<agency name>" "bond" "awards"`,
using the NCSHA member directory / Novogradac state pages as a starting point for the
agency's name when we don't already know it. The first search result that is a PDF or
spreadsheet with a recognizable project table is saved as a recipe
(`propertystack/recipes/awards-<state>.json`).

Award lists are read with pdfplumber (PDF tables) or openpyxl (spreadsheets) --
never OCR guessing. Rows become leads only when they have a units count and an award
date; awards older than 36 months, under 20 units, or explicitly marked
rehab/preservation are dropped (this part only wants new construction). A state with
no award list found online is reported skipped with a reason, not guessed at.

Files:
- `awards.py` -- `find_award_recipe()` (search + identify + save recipe),
  `load_pdf_table_rows()` / `load_xlsx_rows()` (dumb table readers), `parse_award_rows()`
  (rows -> LeadRecords, all the filtering), `find_awards()` (end to end).
- `tests/test_awards.py` -- fixture-only, no network.
