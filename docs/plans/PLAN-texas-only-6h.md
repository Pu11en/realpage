# Texas only, and actually useful: one 6-hour run

David, 2026-09-26. **CraneSignal becomes a Texas-only product.** Arizona, New Mexico and New
York come out. The 178 Texas buildings that have no phone number get one. The data gets
refreshed from source rather than served six days stale.

Written as a file because six hours is longer than one conversation survives. Every phase
checkpoints to disk, so a session that dies mid-run resumes instead of restarting.

## Why this and not more marketing

Measured 2026-09-26. The site shows 1,861 buildings. Filtered the way a salesperson would —
timely, big enough to matter, reachable — **24 are actionable.** Not because the data is fake:
because 93% of rows have no phone number, so there is nothing to do after reading one.

Marketing against that just brings people to the wall faster. The wall is the work.

## Both unknowns were resolved before committing the six hours

Run 2026-09-26, before starting, because a plan whose two biggest risks are untested is a
guess with a schedule attached.

### All 12 Texas sources are alive

Every recipe in `propertystack/recipes/tx/` was fetched live. Result in
`propertystack/runs/source-health-tx-2026-09-26.json`.

Two reported as broken on the first pass and **both failures were the test, not the source**:

- `dallas-dcad` returned `InvalidURL` because its `zip_url` carries a literal Windows path.
  Percent-encoded the way `run_area._safe_url()` already does it, it returns **200 and a
  198 MB file**.
- `san-antonio` returned `409` to a bare GET. It is a CKAN `datastore_search_sql` endpoint, so
  409 means "you sent no query". POSTing the recipe's own SQL returns **628 live rows**.

So phase 1 below is already done, and the refresh in phase 3 rests on twelve working sources
rather than an assumption.

### The contacts are findable: 10 for 10

Ten Texas buildings with no phone, picked at random from the 178, deliberately including the
hardest shapes. One web search each. **Every single one returned a phone number.**

| Our record | What the search found |
|---|---|
| `SONTERRA AT BUCKINGHAM` | (972) 437-5150 — Willow Bridge Property Co |
| `MIDTOWN AT CEDAR HILL` | (469) 382-5471 |
| `BIRCHSTONE CEDAR RIDGE` | 972-573-6201 — Birchstone Residential, own site |
| `ANTHEM TOWN EAST` | (972) 597-2370 — own site |
| `MURDEAUX VILLAS - TDHCA# 21614` | (214) 398-4110 |
| `NORTH OAK APTS (TDHCA# 92001)` | (972) 438-3609 — US Residential |
| `4011 GALVESTON RD` *(no name at all)* | "Dorchester", (713) 644-1271 |
| `9999 KEMPWOOD DR` *(no name)* | "3 Corners East", (832) 621-4561 — **Greystar** |
| `2300 RED BLUFF RD` *(no name)* | "Quarters on Red Bluff", (713) 473-5521, **+ email** |
| `8990 RICHMOND AVE` *(no name)* | pending |

Three things this changed about the plan:

1. **The rows with no name are not the hard case.** Apartments.com, HAR, Zumper and Yelp all
   index by street address, so an address-only row resolves to a real community name — which
   is itself a field worth filling, since a page listing "9999 KEMPWOOD DR" reads like a
   database error and "3 Corners East" reads like a building.
2. **The junk in TDHCA names does not break the search.** `MURDEAUX VILLAS - TDHCA# 21614`
   found it once the code was stripped.
3. **There is more per search than a phone.** Management company, the building's own website,
   and sometimes an email. The management company is the better field for selling software —
   Greystar buys for a portfolio, a leasing office buys for nothing.

**One caution the sample surfaced.** Apartments.com says Murdeaux Villas has 240 units; the
appraisal record says 301. Keep *our* number, which is sourced, and take only the contact from
the search. Never let an aggregator overwrite a field that already has a public record behind
it.

## The rest of the shape, for reference

| | |
|---|---|
| Scrapers on David's Windows machine | **Work.** `httpx`, `pdfplumber`, `PyMuPDF`, `crawl4ai`, `scrapling`, `weasyprint` all install. This was assumed to need Drew's Linux box and does not. |
| Searches needed | **178.** Texas, 50+ units, opening soon or sold in the last 12 months. 108 Dallas–Fort Worth, 55 Houston, 15 rest of Texas. |
| Where the gap is | Entirely in *sold in the last year*. The opening-soon list already has phones on 26 of 28. |

## The six hours

### Phase 1 — are the sources still alive? — **DONE, 2026-09-26**

All 12 alive; see the section above. It went first because everything after it is built on it,
and a dead source found in hour five wastes hours two through four. Took ten minutes rather
than thirty, so the time goes back into phase 4.

Still to do here: `pip install httpx pdfplumber PyMuPDF crawl4ai scrapling`, which the dry run
says will work. `weasyprint` only matters for PDF output and can wait.

### Phase 2 — strip to Texas (1 hour)

Delete, not hide: `site/data/areas/{az,nm,ny}.json`, `propertystack/data/{az,nm,ny}/`, the
non-Texas recipes, `site/leads/az*`, and the Arizona entries in the area index. Update the
tests that name other states — there are 12 of them — and the copy that says "2 US states".

**Known cost, accepted:** the 4 Arizona pages are indexed by Google and will start returning
404. That is the price of the decision and David has made it. Nothing redirects, because there
is no Arizona equivalent to redirect to and a redirect to Texas would be a lie.

Regenerate, run the suite, and do **not** deploy yet — phase 3 changes the same files.

### Phase 3 — refresh the Texas data (1 hour)

Run the 12 recipes. Data is currently 2026-09-20. Feed the result through the existing
`build_data.py` → `build_pages.py` → `build_seo_files.py` chain, which is already verified to
reproduce byte-for-byte on this machine.

New buildings appear; some sold rows age out of the 12-month window. **The 178 is recomputed
after this, not before** — refreshing first avoids paying for searches on rows about to drop
out, and catches new ones that deserve a search.

### Phase 4 — the 178 contact searches (3 hours, the actual product work)

One search per building. Record, per building:

- the real community name (many rows carry only a street address, and the sample showed those
  resolve reliably — a page that says "3 Corners East" beats one that says "9999 KEMPWOOD DR")
- the leasing office phone
- the management company, where the search names one — **the most valuable field of the four**,
  because a Greystar or a Willow Bridge buys software for a portfolio and a single leasing
  office buys for nothing
- an email, where one appears (rare: 1 of 10 in the sample)
- the URL it came from, and today's date

Nothing else. In particular the unit count, the sale date and the stage are **not** touched:
those already have a public record behind them, and an aggregator disagreeing with the
appraisal district is not a reason to trust the aggregator.

Appended to `propertystack/data/tx/contacts-found.csv` after **every batch of ten**, so a lost
session costs one batch and not three hours.

**Checkpoint at 40.** The sample was 10 for 10, so the question is no longer whether this
works but whether it holds at scale. Report the rate at 40 and stop if it has fallen under
60%; the sample was drawn at random but it was still only ten.

Two rules that do not bend:

- A number without a source link does not go in. Same rule as every other field on the site.
- No guessing. A building where the search finds nothing gets left blank, because a blank is
  honest and a wrong phone number is the fastest way to lose the customer who dials it.

### Phase 5 — ship it (30 min)

Rebuild pages, CSVs, sitemap, llms.txt. Run the suite and both `--check` modes. Merge, let
Railway deploy, verify live by fetching the real pages. Push the changed URLs to Bing.

## What exists at the end

A Texas-only site where the Houston and Dallas pages stop being a list and start being a call
sheet: building, address, units, stage, date, **who to call**, and a link to where every fact
came from. The free spreadsheet carries the same columns. Roughly **160–200 actionable leads**
instead of 24.

## What this explicitly does not do

- **No automation.** Every step is run by hand, as decided (`PLAN-loops.md`).
- **No new pages.** The page ceiling stays; Texas already has 15.
- **No outreach, no posting.** Not in this run and not by a bot.
- **No paid data.** Every contact comes from a public page, with its link.

## The risks, named

1. **Sources rotted since 2026-09-14.** Phase 1 exists to find this in the first 30 minutes
   rather than the last.
2. **Hit rate below the sample.** Checkpointed at 15 for exactly this.
3. **Stale phone numbers.** Leasing offices change hands. Every number carries its source and
   date, so a customer can check rather than trust.
4. **Six hours is longer than one conversation.** Hence this file, and a CSV checkpoint every
   ten rows.

## Open question, not a blocker

Whether to keep a `50+ units` floor or tighten to `100+`. 100+ is 145 searches instead of 178
and every row is a bigger prospect. Starting at 50+ and treating the last 33 as optional
overtime — if phase 4 runs long, they are the ones to drop.
