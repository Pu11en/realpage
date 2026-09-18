---
name: lead-finder-cities
description: Rank a state's cities (and unincorporated county permit areas) by new 5+ unit apartment permits, from the free Census Building Permits Survey place-level files. Part 2.1 of lead-finder.
---

# lead-finder-cities

Given any state (two-letter code), ranks every city -- and any unincorporated county area that
issues its own permits -- by new 5+ unit apartment permits over the last 12-24 months, using the
free Census Building Permits Survey **place-level** files (`https://www2.census.gov/econ/bps/Place/`).

Area-agnostic: no state or city name is hard-coded; everything comes from arguments and data files.

## Output

`propertystack/data/<state-slug>/cities.json` (state-slug = lowercase two-letter code):

```json
{
 "state": "TX",
 "window": "2025-08..2026-07",
 "source": "https://www2.census.gov/econ/bps/",
 "cities": [
   {"city": "Dallas", "is_county_area": false, "permits_5plus": 3377}
 ]
}
```

Sorted by `permits_5plus` descending. `is_county_area` is true for an unincorporated-county
permit area (place-file rows naming a county, e.g. "Collin County (unincorporated area)").

## Run

`python3 rank.py --state TX [--months 12]`
