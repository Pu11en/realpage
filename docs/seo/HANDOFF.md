# SEO/GEO handoff — 2026-09-25

Both hosts are **live and verified**. `app.cranesignal.com` and `cranesignal.com` now share
one Organization identity. The work is done; what remains is measurement and the optional
items at the bottom.

## Where things stand

**Live on `app.cranesignal.com`** (PR #1, merged 2026-09-25):

- `robots.txt`, `sitemap.xml`, `llms.txt`, `llms-full.txt` — all were 404 before, all serve 200 now.
- **18 static pages** under `/leads/`: 4 metro pipeline reports (Dallas–Fort Worth, Houston,
  Austin, San Antonio), 2 state pages, 10 city pages, and 2 dated lists. Each carries an
  extractable answer paragraph, per-place analysis computed from its own rows, the building
  table with a public source link on every row, a data-derived FAQ, and
  `Dataset` + `ItemList` + `BreadcrumbList` + `FAQPage` schema.
- Unique title, description, canonical, Open Graph and a 1200×630 share card on every page.
- `noindex` on `property.html`, `404.html`, `master-table.html`.
- `/` serves directly instead of answering 302.
- 21 URLs pushed to Bing via IndexNow (HTTP 202).
- Search Console verified by DNS TXT; sitemap submitted. Bing imported from GSC.

Crawler's-eye check on the live site: `/leads/tx/houston.html` returns **3,905 body words**
with exactly one script tag, and that one is the JSON-LD. Before this it returned nothing.

**Landing page: merged, not deployed.** Now at https://github.com/Pu11en/cranesignal-landing,
PR #1 merged. It deploys by Railway CLI from local, so it needs one `railway up` run — see below.

## What is left to do

### 1. The landing page — done, live 2026-09-25

DrewAI found it at `/home/drewp/main-projects/realpage/business` (already a git repo, no
remote) and pushed it to **https://github.com/Pu11en/cranesignal-landing**. PR #1 merged and
deployed. `robots.txt`, `sitemap.xml`, `llms.txt` and the JSON-LD all verified live.

**One trap worth remembering:** the landing page's Dockerfile copies an explicit file list,
so the three new files were in the repo but never reached the container and would all have
404'd silently. DrewAI caught it and added them to that COPY line (commit `9feb80e`). Any
future file added to `marketing/landing/` needs the same.

Two other notes from doing it: the repo's `index.html` carries a `{{LEAD_SUMMARY}}`
placeholder that `server.py` fills at request time, so patch the repo file rather than a copy
of the live HTML. And `tools/test_landing.py --offline` gives results identical to `main` —
the same 6 pre-existing failures, three of them a `file://` summary URL that does not resolve
on Windows and one a real "no em dashes" failure that predates this work.

### 2. Re-measure on 2026-10-09 — two weeks after deploy

```bash
python3 tooling/seo/sample.py          # both engines, ~28 questions, resumable
```

Compare against `docs/seo/answer-share/2026-09-23/report.md`. Also pull Search Console
impressions, which should exist by then.

### 3. One Organization identity — done 2026-09-25

Both generators now reference `https://cranesignal.com/#org`, declared on the landing page,
rather than each host minting its own. This fixed a real dangling reference, not just tidiness:
validation showed every `/leads/` page naming `app.cranesignal.com/#org` as its creator while
declaring no Organization node on that page, so the reference resolved to nothing. A test now
asserts both hosts name the same `@id`, so a later edit cannot quietly re-split the entity.

## The baseline, so the next session knows what "better" looks like

From `docs/seo/answer-share/2026-09-23/` — 28 questions a CraneSignal buyer would ask, asked
of Claude (`claude -p`, web search) and Gemini (2.5-flash, Google Search grounding). 56
answers, no failures.

- **CraneSignal named in 0 of 56.**
- CoStar 61%, Yardi Matrix 55%, RealPage 48%. Apartments.com 32% and Zillow 20% — those two
  showing up means some questions read as renter intent.
- "Go read the public records yourself" 27%. That answer is one step from citing a site that
  has already read them, which is what the new pages are.
- By intent: *sales* is the most locked up (CoStar 90%); **free-data is the clearest opening**
  — engines name paid tools 70% of the time even when asked for free ones, because no free
  source exists; *prospecting* is the least winnable today because contact data is our
  weakest column (144 phone numbers out of 1,861 buildings).
- The engines read yardimatrix.com, multihousingnews.com, realpage.com, mmgrea.com,
  northmarq.com, cushmanwakefield.com, costar.com, reddit.com, therealdeal.com, credaily.com,
  census.gov, houstontx.gov. Trade press and public data sit alongside the vendors, which says
  our own pages are necessary but not sufficient.

## How the tooling works

Run order after any data refresh:

```bash
python3 site/data/build_data.py        # existing: the JSON
python3 tooling/seo/build_pages.py     # the 18 static pages + the home page block
python3 tooling/seo/build_seo_files.py # robots, sitemap, llms.txt, llms-full.txt, schema
bash    tooling/qa/check-seo.sh        # offline tests + live check
python3 tooling/seo/indexnow.py --changed-since HEAD~1   # push only what changed
```

Every generator has a `--check` mode that fails if its output is stale, and tests enforce it,
so the sitemap date and llms.txt counts cannot silently drift from the data.

| File | What it does |
|---|---|
| `tooling/seo/build_pages.py` | The 18 pages. Thresholds: 25 buildings minimum per page, 400 rows maximum. |
| `tooling/seo/build_seo_files.py` | robots/sitemap/llms/llms-full + the home page's JSON-LD. |
| `tooling/seo/sample.py` | Asks both engines, writes one JSON per answer, resumable, Claude capped at 60 calls. |
| `tooling/seo/indexnow.py` | Pushes URLs to Bing. Refuses anything not yet live. |
| `tooling/seo/make_og_image.py` | The share card. Run by hand, not by the builders. |
| `tooling/qa/check-seo.sh` | `--live-required` to fail on live gaps. |

Tests: `test_seo_files.py`, `test_seo_pages.py`, `test_seo_sample.py` — 524 passing overall.
None call an engine or the network. One test asserts CraneSignal appears in **zero** answers;
when it fails, the work has landed and the baseline note needs updating, not the test.

## Decisions worth not re-litigating

- **18 pages, not 1,861.** Google's March 2026 update demotes sites for mass-produced thin
  pages and the demotion is sitewide. Per-building pages are off the table until the current
  set proves out.
- **Metro "market report / construction pipeline" phrasing, not "new apartments in Dallas".**
  Autocomplete showed the latter is renter intent — wrong audience, unwinnable against
  Apartments.com. Evidence in `docs/plans/PLAN-seo-geo-strategy.md`.
- **The question bank measures lead-finding, not property-management software.** An earlier
  version asked which PMS to buy, which measures RealPage's market rather than ours. A test
  now fails if such a question creeps back.
- **The home page title must not claim state coverage.** `test_g3_t3_data_note.py` and
  `test_g3_freshness.py` both assert "Texas &amp; Arizona" is absent from `index.html`. It is
  a deliberate product rule; work around it rather than changing the tests.
- **No FAQ schema without a visible FAQ.** Structured data that states something the page does
  not show risks a spam verdict. The `/leads/` pages have both; the landing page has neither,
  so none was added.
- **No backlink buying.** The measurement already showed what earns citations here: trade
  press, city and census data, and vendor documentation.

## Known gaps, honestly

- **Contact data.** 144 phone numbers for 1,861 buildings, and zero websites. Prospecting
  questions go to ZoomInfo and CoStar. This is a product gap, not an SEO one.
- **No `sameAs` entity links** beyond the two hosts — no wiki, GitHub or social presence
  exists to link. LLMO depends on those surfaces.
- **No blog, RSS or question backlog.** The agency-retainer half of the skill's playbook. Real
  gap, but it needs a publishing decision rather than code.
- **Per-page share images.** One card for the whole site. Per-page cards need a TTF vendored
  into the repo; the only fonts here are woff2, which Pillow cannot read.
- **`/static/*` routes to the chat app, not the site.** Pre-existing: every page's favicon is
  served by Open WebUI. Worth checking which icon a search result actually shows.
- **Pre-existing test failures**, present before this work and untouched: 7 failures
  (`test_af_t3_filter_disclosure`, `test_build_c_lead_pack`, `test_build_c_new_leads` ×2,
  `test_fu2_unlock_csv_sample` ×2, `test_a6_menu_footer`) and 7 errors that need Caddy via
  Docker, which is not installed on David's machine.
  `tooling/check-no-realpage-target.sh` reports 2 violations in
  `docs/2026-09-20-maintenance-software-icp.md`, also pre-existing.

## Expectations

Search Console data appears 2–3 days after verification and will be near zero at first — that
is the baseline, not a failure. Bing indexes within days thanks to IndexNow. Google takes
weeks. Rankings for "<metro> multifamily construction pipeline" take two to three months. AI
citations are slowest of all, and Perplexity or Gemini will show up before ChatGPT.

## The paper trail

| Document | What is in it |
|---|---|
| `docs/plans/PLAN-seo-geo-strategy.md` | Why these pages and not others — search-demand evidence, Google's 2026 thin-page limits, the do-not-build list. |
| `docs/plans/PLAN-seo-geo-run.progress.md` | What was built, in order, with the problems hit and how they were resolved. |
| `docs/seo/2026-09-25-audit.md` | The open-source `fire-your-seo-agency` audit: lane scorecard, what it caught, what was deliberately skipped. |
| `docs/seo/answer-share/2026-09-23/report.md` | The baseline, plus all 56 raw answers as JSON. |
| `docs/seo/GOOGLE-SETUP-GUIDE.md` | Click-by-click Search Console, Cloud Console, Bing. Parts 1–3 and 5 are done. |
| `docs/seo/LANDING-PAGE-FIXES-FOR-DREW.md` | The landing audit and the reasoning behind each fix. |
| `docs/seo/landing-page-ready/` | The four finished files. |

The audit skill is cloned to `.claude/skills/fire-your-seo-agency` and gitignored — it carries
its own `.git`, so re-clone it rather than expecting it in a fresh checkout:
`git clone https://github.com/leopard627/fire-your-seo-agency.git .claude/skills/fire-your-seo-agency`
