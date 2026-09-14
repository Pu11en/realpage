---
name: lead-finder-legistar
description: PropertyStack lead finder part 3.4. For a city that runs Legistar (identified in 3.3), reads the last 12 months of Planning/Zoning/Council meeting matters via the free Legistar Web API and turns multifamily-related items into planned-stage leads.
---

# lead-finder-legistar (part 3.4)

Legistar (`<client>.legistar.com`) publishes a free, no-key web API at
`https://webapi.legistar.com/v1/<client>/`. This part uses it to find planning
activity before a permit is ever pulled:

1. `bodies` -- find the Planning / Zoning / Council body IDs (name match).
2. `events?$filter=EventDate ge datetime'<12-months-ago>'` -- meetings of those
   bodies in the last year.
3. `events/<id>/eventitems` -- each meeting's agenda items; keep items whose
   matter title mentions multifamily/apartments/a unit count/rezoning/site plan.
4. Each surviving matter becomes one `planned`-stage `LeadRecord` (address and
   unit count pulled from the title when present, case number folded into the
   `why` line, agenda link points at `LegislationDetail.aspx?ID=<matterId>`).
   Matters seen across multiple meetings are deduped before merging.

Some cities' Legistar instance requires an API token even though the public
site is free to browse; those, and any city whose API doesn't respond, or has
no Planning/Zoning/Council body, are reported as a skip note with a reason --
never guessed at.

Files:
- `legistar.py` -- `find_legistar_matters()` (bodies -> events -> eventitems ->
  LeadRecords, via `merge.py`); CLI entry point behind `if __name__`.
- `tests/test_legistar.py` -- fixture-only (fake `http_get`), no network.
