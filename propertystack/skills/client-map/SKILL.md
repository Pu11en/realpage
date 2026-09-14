---
name: client-map
description: PropertyStack client map. Find apartment buildings that already use RealPage (their site links to a RealPage resident portal) in the 15 fastest-growing states, and count them per state and city so the lead finder can skip those places. Local harness only.
---

# client-map

Runs on Drew's computer only, never in the chat agent. Fast and cheap: under an hour.

## Proof of a RealPage client
The building's own website links to **loftliving.com**, **activebuilding.com** or
**onesite.realpage.com** (rules from `tooling/pms_detect.py`). `residentportal.com` is
Entrata and is rejected; realpage.com marketing pages are not proof.

## Budget
- Jina **only for search**, hard max **150 searches** per run, counted by `SearchBudget`.
  At the cap the run stops cleanly and keeps what it found.
- crawl4ai at `http://localhost:11235` (free) opens building sites; Census batch geocoder (free,
  OpenStreetMap backup) turns addresses into lat/lon.

## Steps
1. C2: `data/client-map/targets.json` = top 15 states by new 5+ unit permits (12 months), ~10
   biggest apartment cities each. Raw Census files cached in `data/raw/census/`.
2. C3: one search per city in state order -> confirm each hit's portal link -> name + address
   -> lat/lon -> remove duplicates (same portal subdomain or same address).

## Outputs
- `data/client-map/buildings.csv`: name, city, state, lat, lon, proof_url.
- `data/client-map/counts.json`: `{state: {"total": n, "cities": {city: n}}}`.
- `runs/<ts>-client-map.json`: searches used.
- Shown on `site/map.html` as shaded states (C4).

## Tests
`python3 -m pytest -q propertystack/skills/client-map/` (fixtures only, no network).
