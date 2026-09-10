---
name: find-website
description: Skill 2 of PropertyStack. Find each apartment community's official website via Jina Search, rejecting listing/aggregator sites. Use after find-apartments, before detect-software.
---

# find-website

**Reads:** `data/<area>/1-apartments.csv`
**Writes:** `data/<area>/2-websites.csv` (columns in `CONTRACTS.md`) + a run log in `runs/`

## Run
`python3 skills/find-website/run.py --area plano-richardson`

## What it does
1. For each community, searches Jina for `"<name>" <address> <city> TX apartments`.
   If nothing acceptable comes back, falls back to `"<name>" <city> TX apartments`.
2. Rejects listing/aggregator domains (apartments.com, zillow, rent.com,
   apartmentlist, trulia, redfin, realtor.com, hotpads, forrent, apartmentguide,
   apartmentfinder, craigslist, yelp, facebook, instagram, linkedin, loopnet,
   costar, bare rentcafe.com, padmapper, zumper, rentable, apartmentratings, bbb,
   mapquest, yellowpages, niche, google). Manager-company sites with a page for
   the community (camdenliving.com/..., udr.com/..., cortland.com/apartments/...)
   are accepted.
3. Confidence: **high** = domain or title contains the community's distinctive
   name words; **medium** = an accepted (manager-site) result whose URL contains
   the name; **low** = accepted but neither; **none** = nothing acceptable found.
4. Runs 5 requests in parallel (`--workers`, default 5).

## Check after running
- Counts by confidence are printed and logged (`runs/`).
- Spot-check a handful of "high" rows by opening the URL — manager sites with
  generic template titles can slip in as high if the name words are common.
- `low`/`none` rows still need a human look before Skill 3 will fetch them
  (Skill 3 skips low/none on purpose).

## Limits
- Search-only; no CAD address match or manual override yet (`website_source`
  is always `search`).
- The distinctive-word matcher is naive — very short or very generic community
  names (e.g. "The Park") are more likely to land at `low` even when correct.
- Jina Search result quality varies; a wrong domain that happens to contain a
  name word could be misclassified as `high`.
