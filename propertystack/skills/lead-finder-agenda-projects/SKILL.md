---
name: lead-finder-agenda-projects
description: PropertyStack lead finder part 3.6. Turns 3.4 (Legistar) and 3.5 (CivicPlus/Granicus/PrimeGov/CivicClerk) agenda hits into planned-project LeadRecords, keeping only items with an address or case number and merging Planning & Zoning plus Council hits for the same case into one project.
---

# lead-finder-agenda-projects (part 3.6)

3.4 and 3.5 each surface raw text near a multifamily/rezoning keyword hit in a planning
agenda. This part turns that text into a real "planned" LeadRecord: an item is kept only
if it has an address or a case number (a bare keyword mention with neither is too weak
to trust); name, address, developer, units and case number are pulled out of the text;
hits for the same case (Planning & Zoning and Council both discuss the same rezoning) or
the same address are merged into one project rather than counted twice.

Files:
- `agenda_projects.py` -- `agenda_hits_to_projects()` (the main entry point: takes any
  iterable of hit-like objects with `.url` and `.text`, works for both 3.4's Legistar
  matters and 3.5's civic `AgendaHit`s), `hit_to_project()` (one hit -> one LeadRecord or
  `None`).
- `tests/test_agenda_projects.py` -- fixture-only, no network.
