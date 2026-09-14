---
name: lead-finder-sources
description: PropertyStack lead finder part 2.2. For any city, finds its building-permit data source (Socrata / ArcGIS catalog lookup) and saves a recipe describing how to query new multifamily permits from it.
---

# lead-finder-sources

Part 2.2 of the lead finder chain (see `propertystack/skills/lead-finder/SKILL.md`). Given a
city, asks the free **Socrata Discovery API** and **ArcGIS Hub search** for a matching
building-permits dataset, tests that the dataset really has recent multifamily-looking permit
rows, and saves the result as a recipe under `propertystack/recipes/<city-slug>.json`.

Area-agnostic: no city or state name is ever hard-coded here. City/state are always
caller-supplied arguments.

## Recipe format

`propertystack/recipes/<city-slug>.json`:

```json
{
  "city": "<city name>",
  "state": "<two-letter state>",
  "system": "socrata | arcgis",
  "endpoint": "<dataset query URL, e.g. the Socrata resource URL or ArcGIS FeatureServer query URL>",
  "fields": {"permit_type": "...", "issue_date": "...", "units": "...", "address": "..."},
  "date_tested": "<YYYY-MM-DD>",
  "completeness": "<free text: what the test found, e.g. 'has issue_date, units, address; 8 of 20 sample rows look multifamily'>"
}
```

A recipe is only saved once the dataset has been tested (`test_dataset`) and shown to actually
have recent rows that look like multifamily permits -- an untested or empty-looking dataset is
skipped, not saved.

## Catalog lookups tried, in order

1. Socrata Discovery API: `https://api.us.socrata.com/api/catalog/v1?q=building+permits&search_context=<domain>`
   (or `q=<city> building permits` when no known domain), looking for a dataset resource that
   answers as a Socrata (SODA) API.
2. ArcGIS Hub search: `https://hub.arcgis.com/api/search/v1/collections/dataset/items?q=<city>%20building%20permits`,
   looking for a FeatureServer/MapServer layer.

Both calls go through an injectable `http_get(url) -> dict` so tests never touch the network.

## Output

`find_sources(city, state, http_get)` returns the recipe dict (or `None` if nothing testable
was found) and, when a recipe is found, writes it to `propertystack/recipes/<city-slug>.json`.
A city with no catalog hit falls through to 2.3 (`find-sources` fallback: portal search).
