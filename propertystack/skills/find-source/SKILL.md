---
name: find-source
description: Find and verify a replacement apartment-permit source for a city when no saved recipe works, then save an auto-found recipe or record that the city still needs a source.
---

# Find a source

Use this only for cities whose normal permit recipes are missing or no longer work. Pass every
city in the run to one command so the run-wide search limit is enforced:

```bash
python3 propertystack/skills/find-source/find_source.py "<city>" <state> ["<city>" <state> ...]
```

The runner uses the lead finder's already-configured search service and never asks for a new
key. It searches in this order: the city's open-data portal, Socrata, ArcGIS, Accela/Citizen
Access, then the county. The batch command owns one shared `SearchBudget`, enforcing hard limits
of 20 searches per city and 100 searches for the whole run; after search 100, remaining cities
are recorded as needing a source without starting search 101.

A URL from search is only accepted after its live response yields at least five distinct
apartment projects with a street address, a usable date, and either 20+ units or an explicit
apartment/multifamily description. The resulting leads must also pass
`tooling/qa/check_lead_data.py`. Never construct or guess a dataset URL from a portal page.

Successful recipes are written under `propertystack/recipes/<state>/`, carry
`"source": "auto-found"`, and retain the exact tested endpoint. If nothing passes or a search
limit is reached, the command adds the city to `propertystack/runs/needs-a-source.md` and exits
successfully so the wider run can continue. Any run summary must name every auto-found source.

For deterministic/offline checks, pass `--recorded <responses.json>`; the recorded file
contains stage search results plus exact fetched responses and performs no network calls.
