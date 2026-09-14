---
name: score-leads
description: lead-finder part 4.5. Rank any area's LeadRecords (part 1.2 format) into one ordered list and write a facts-only one-line "why" per lead. Use after software detection and sales/contact lookups, right before the site build.
---

# score-leads (part 4.5)

Pure code, no place names, no agent judgment call -- every `why` line is built only
from that record's own fields, so there's nothing to fabricate.

## Order

1. **Active** leads (`permitted` / `under construction` / `leasing`):
   soonest `opening_date` first, then more `units`, then a lead whose `software`
   isn't decided yet (blank / `unknown` / `not picked`) over one already on a named
   competitor. A lead with no `opening_date` ranks after every lead that has one,
   and among themselves by oldest `permit_date` (longest in the pipeline, so
   likeliest to open soonest) -- shown as "opens: not public yet".
2. **Sold** leads: newest `sale_date` first; no date sorts last.
3. **Planned** leads: soonest `opening_date` first (shown as "expected: not public
   yet" when blank), then more `units`.

## Files

- `score_leads.py` -- `score_and_rank(records: list[LeadRecord]) -> list[LeadRecord]`,
  the only entry point. Sorts and fills in `why`; does not fetch or invent facts.
- `tests/test_score_leads.py` -- fixture-only, no network.

## Limits

- `why` only ever quotes fields already on the record -- if a fact (e.g. opening
  date, buyer) is blank, the line just says so rather than guessing.
