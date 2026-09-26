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

## What was checked first, so the plan is not a guess

| Question | Answer |
|---|---|
| Can the scrapers run on David's Windows machine? | **Yes.** `httpx`, `pdfplumber`, `PyMuPDF`, `crawl4ai`, `scrapling`, `weasyprint` all install. Previously assumed to need Drew's Linux box. |
| Are the contacts findable? | **3 of 3** on a random sample, one web search each. Apartments.com, HAR and Yelp index apartment buildings by street address, including one with no name in our data at all. |
| How many searches? | **178.** Texas, 50+ units, opening soon or sold in the last 12 months. 108 Dallas–Fort Worth, 55 Houston, 15 rest of Texas. All 178 have a name or address to search on. |
| Is the opening-soon list already fine? | **Yes.** 26 of 28 big ones have phones. The entire gap is in *sold in the last year*. |

## The six hours

### Phase 1 — are the sources still alive? (30 min, and it is the gate)

12 Texas recipes in `propertystack/recipes/tx/`: Arlington, Austin, Dallas DCAD, Fort Worth,
Houston, Houston HCAD, San Antonio, San Marcos, TABS, Tarrant TAD, Tarrant TAD sales, TDHCA.
Each was last live-tested 2026-09-14. Install the libraries, run each source's live self-test,
write the result to `propertystack/runs/source-health.json`.

**This is first because everything after it is built on it.** A dead source found in hour five
wastes hours two through four. If more than three are dead, stop and report rather than
building on a partial refresh.

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

- the real community name (many rows currently carry only a street address)
- the leasing office phone
- the management company, where the search names one — **this is the more valuable field**,
  because the management company buys software and the leasing office does not
- the URL it came from, and today's date

Appended to `propertystack/data/tx/contacts-found.csv` after **every batch of ten**, so a lost
session costs one batch and not three hours.

**Checkpoint after the first 15.** If the hit rate holds near 80%, keep going — that is ~140
new leads. If it comes in under 50%, stop and report before spending the afternoon. Three out
of three is encouraging and it is also n=3.

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
