---
name: lead-finder-sales-news
description: PropertyStack lead finder part 4.3. Finds apartment building sales for any city from Jina/Brave news search and the GDELT DOC API, turning them into sold-stage leads.
---

# lead-finder-sales-news (part 4.3)

A sold apartment building is a lead: it likely just got a new owner who hasn't picked
leasing software yet. This part searches the web (Jina first, Brave second -- see
`fetch.py`'s `WebHelper.search()`) for
`"<city>" apartments sold OR acquires OR acquisition units` across the full 24-month
window, and adds GDELT's free DOC API
(`https://api.gdeltproject.org/api/v2/doc/doc?mode=artlist&format=json`) as a
freshness add-on -- GDELT DOC only indexes roughly the last 3 months, so it's queried
in addition to the web search, not instead of it, to catch very recent sales
before they show up elsewhere.

A hit becomes a lead only when its title/snippet has a sale keyword (sold, acquisition,
acquires, acquired, purchased), a parseable "NN-unit" count of 20+, and a real
published date within the last 24 months -- any of the three missing and the hit is
dropped, never guessed. Buyer name is pulled from "acquired by X" / "sold to X" /
"X acquires" patterns when present; left blank otherwise. Results are deduped by
article URL across both sources.

Files:
- `sales_news.py` -- `news_query()`, `gdelt_url()`, `hit_to_record()` (one hit ->
  LeadRecord or None), `find_sales_news()` (end to end for one city, both sources).
- `tests/test_sales_news.py` -- fixture-only, no network.
