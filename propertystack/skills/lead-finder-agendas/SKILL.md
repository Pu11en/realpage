---
name: lead-finder-agendas
description: PropertyStack lead finder part 3.3. For any city, finds its planning commission agenda page and identifies which meeting-management system it runs, so later parts know how to read it.
---

# lead-finder-agendas (part 3.3)

Planning/zoning commission agendas mention rezonings and site plans before a permit is
ever pulled, so they're an early-lead source -- but every city hosts them on a different
system. This part searches `"<city>" "<state>" planning commission agenda`, then matches
the first useful result's URL (or, if the URL doesn't give it away, the fetched page's
HTML) against known system fingerprints: `legistar.com`, `/AgendaCenter`, `granicus.com`,
`primegov.com`, `civicclerk.com`, `boarddocs.com`, `escribemeetings.com`, `iqm2.com`.

The identified system + agenda URL is cached per city as a recipe
(`propertystack/recipes/agendas-<city>.json`) so 3.4 (Legistar reader) and 3.5 (other
systems + PDFs) know which reader to use without searching again. A city with no
identifiable agenda system online is reported skipped with a reason, never guessed at.

Files:
- `agendas.py` -- `find_meeting_system()` (search + identify + save recipe),
  `identify_system()` (pattern match against URL or HTML), `slugify()`.
- `tests/test_agendas.py` -- fixture-only, no network.
