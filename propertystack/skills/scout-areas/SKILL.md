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
- `data/raw/census/` cached Census downloads (S2, git-ignored): 12 monthly BPS CBSA files (5+ units, imputed) + ACS 1-year B25003 summary file (renters = E003). No API key: api.census.gov now requires one, the flat files do not.
- `data/scout/<date>/<metro>/sample.csv` + evidence JSON (S3, S4).
- `data/scout/<date>/areas.json`: numbers + evidence links only (S5).
- `data/scout/<date>/why.json`: `{slug: "3-line why this city"}`, written by the local Claude session after reading areas.json + evidence (no extra API model).
- `data/scout/<date>/cards.md`: top 5 rendered by run.py from areas.json + why.json (rerun `--from-saved <date>` after editing why.json; zero searches).
- `kind: "scout"` markers (top 5) in `site/data/reach.json`, older scout markers replaced, reach dots kept; a run log `runs/<ts>-scout-areas.json`.

## Tools
- crawl4ai at `http://localhost:11235` for reading pages (free, local).
- Jina **only for search**, counted by `SearchBudget`; at the cap the run stops cleanly and
  reports finished vs unfinished metros.
- `tooling/reddit_search.py` (read-only), `tooling/pms_detect.py` vendor rules.
- Vendor sample (`sample.py`): up to 8 searches per metro until 25 community sites are found
  (listing portals, operator brand sites, .gov/.edu/.org skipped), each classified via crawl4ai +
  `pms_detect.detect`. Key: `JINA_API_KEY` env var or the repo `.env`.
- Churn + pain (`churn_pain.py`): 4 news searches + 4 complaint searches per metro (counted).
  Keeps only items with a URL and a date in the last 24 months (date from URL/snippet, else the
  page's publish date via crawl4ai); listing portals and vendor-owned sites skipped. Reddit:
  5 free searches inside the city's subreddit (r/Tucson ...), kept only if a vendor + a
  portal/payment word appear. Writes `<metro>/evidence.json` (`churn`, `complaints` lists).

## Tests
`python3 -m pytest -q propertystack/skills/scout-areas/` (saved fixtures, no network).
