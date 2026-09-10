# Manual spot-check — 2026-09-10 — area: plano-richardson

Method: opened each URL with `Jina().read()` and read the fetched page content
(not just the domain) to confirm it matches the community / vendor.

## Round 1 (before fixes) — 10 random `confidence=high` website rows
9/10 pass, 1 fail:
- FAIL `354556` Pleasant Park Apartments → `chamberofcommerce.com` business-directory
  listing page, not the community's own site.
Also found by domain-frequency scan (not random sample) before this round:
har.com, umovefree.com, averagejoeslocating.com, apartmenthomeliving.com,
aptamigo.com, safebutler.com, waze.com, oasissenioradvisors.com, rentersvoice.com,
forrentuniversity.com, sulekha.com, maps.apple.com, cortera.com — all
aggregator/locator/review/map/directory domains being misclassified as `high`
confidence "official" sites. Fixed by adding all of the above (plus a generic
`locating`/`locator` substring rule) to the `REJECT_DOMAINS` list in
`skills/find-website/run.py`, then re-running skill 2.

## Round 2 (after first fix pass) — 10 more random `confidence=high` rows + 10 random identified software rows
Website: 9/10 pass, 1 fail:
- FAIL `2873065` Twin Rivers At Collin Creek Senior Living → `health.usnews.com`
  senior-living directory page, not the community's own site. Fixed by adding
  `usnews.com`, `caring.com`, `seniorliving.org`, `aplaceformom.com` to
  `REJECT_DOMAINS` and re-running skill 2 → skill 3 → skill 4 (final numbers
  below reflect this run).

Software (`3-software.csv`, `signal=portal|hop-portal|asset`): 10/10 pass.
Every `proof_url` opened to a real resident-portal / login page on the expected
vendor's domain or product name:
- RealPage: `*.onlineleasing.realpage.com`, `*.loftliving.com` (Loft, a RealPage
  product), `*.activebuilding.com`
- Yardi: `*.securecafe.com`, `*.securecafenet.com`
- Entrata: `*.residentportal.com`
- AppFolio: `*.appfolio.com`
No false-positive string matches found (e.g. no "yardi" hit inside an unrelated
analytics/script URL).

## Net result
Both fails were the same class of bug: aggregator/directory/locator/review
sites that happen to contain the community's exact name in the URL or title,
which the naive distinctive-word matcher scored as `high` confidence. Not a
software-detection bug — detect-software's vendor matching held up 10/10 in
both spot-check rounds.

## Biggest problem left
`REJECT_DOMAINS` is a manually maintained blocklist, not a real "is this an
aggregator" classifier — it will keep leaking new locator/directory/review/map
sites we haven't seen yet (this session alone found ~25 distinct leaked
domains across 4 iterations). A domain-category heuristic (e.g. penalize any
domain whose page title/description reads like a directory listing rather than
a property's own marketing copy) would generalize better than a growing list.

## Final counts (after all fixes, from `build-table` run log)
in_area=207, website_found=140 (high+medium), checked=140, identified=104,
unknown=103 (no-website=67, no-portal-link=35, in-house-portal=1)
software: Yardi=56, RealPage=17, Entrata=13, ResMan=6, MRI/RentManager=4,
AppFolio=3, Yotta=2, in-house:Camden=2, in-house:UDR=1
