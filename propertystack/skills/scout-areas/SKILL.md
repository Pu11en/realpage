---
name: scout-areas
description: PropertyStack scout. Score ~25 Sun Belt metros (excluding Dallas-Fort Worth) for untapped apartment-software demand and write 3-5 area cards Drew picks the next area from. Local harness only.
---

# scout-areas

Runs on Drew's computer only, never in the chat agent.

## Inputs
- `metros.csv`: slug, name, state, CBSA code, lat, lon (~25 rows, **no DFW**).
- `--metros a,b` (default all), `--limit-searches N` (default and hard max **1,500**).

## Per metro (three part-scores, 0-100 each; total = rounded mean)
1. **Growth + weakness** = 40 x min(5+ unit permits per 1k renter households / 20, 1)
   + 20 x min(renter households / 300k, 1) + 40 x (1 - RealPage share of the site sample).
2. **Churn** = 100 x min(recent apartment sales / management changes (24 months) / 20, 1).
3. **Competitor pain** = 60 x (Yardi + Entrata share of sample) + 40 x min(complaints / 10, 1).

## Outputs
- `data/raw/census/` cached Census downloads (S2).
- `data/scout/<date>/<metro>/sample.csv` + evidence JSON (S3, S4).
- `data/scout/<date>/areas.json`: numbers + evidence links only (S5).
- `data/scout/<date>/cards.md`: top 5, written by the local Claude session from areas.json (S5).
- `kind: "scout"` markers in `site/data/reach.json`; a run log in `runs/`.

## Tools
- crawl4ai at `http://localhost:11235` for reading pages (free, local).
- Jina **only for search**, counted by `SearchBudget`; at the cap the run stops cleanly and
  reports finished vs unfinished metros.
- `tooling/reddit_search.py` (read-only), `tooling/pms_detect.py` vendor rules.

## Tests
`python3 -m pytest -q propertystack/skills/scout-areas/` (saved fixtures, no network).
