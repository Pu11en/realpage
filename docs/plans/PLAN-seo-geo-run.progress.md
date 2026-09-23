# Progress: SEO/GEO build (branch `seo-geo-week1`)

Plan: `PLAN-seo-geo-run.md` · Strategy: `PLAN-seo-geo-strategy.md`

## Step 1 — plumbing and metadata ✅ 2026-09-23

Shipped on the branch (not deployed):

- `tooling/seo/build_seo_files.py` generates `site/robots.txt`, `site/sitemap.xml`,
  `site/llms.txt` and the home page's JSON-LD from the real data. `--check` mode fails if
  they drift, so the sitemap's `lastmod` and llms.txt's counts cannot go stale silently.
- `robots.txt`: explicit allow for GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot,
  Claude-Web, anthropic-ai, PerplexityBot, Perplexity-User, Google-Extended,
  Applebot-Extended, CCBot, Bingbot. Sitemap line. `master-table.html` disallowed.
- `llms.txt`: what the data is, where it comes from, real coverage (Texas 1,587 buildings /
  146 cities / 259,251 units; Arizona 274 / 22 / 31,875), page list, and a note on citing.
- `sitemap.xml`: the three indexable pages, `lastmod` from `areas/index.json` (2026-09-20).
  Picks up `/leads/*.html` automatically once step 2 generates them.
- Per-page metadata: unique title, unique description, canonical, Open Graph and Twitter
  card on `index.html`, `under-the-hood.html`, `privacy.html`.
- `noindex,follow` + canonical on `property.html`, `404.html`, `master-table.html`.
  `property.html` is one template behind `?id=` and renders empty without JavaScript, so
  indexing it would add a thin near-duplicate per building — exactly what Google's
  March 2026 update punishes.
- JSON-LD on the home page: `Organization`, `WebSite`, and a `Dataset` stating 1,861
  buildings / 291,126 units / 2 states, `dateModified`, `temporalCoverage`,
  `isAccessibleForFree`, `spatialCoverage`, `variableMeasured`.
- `site/Caddyfile`: serves `/robots.txt /sitemap.xml /llms.txt` before any sign-in logic,
  serves `/leads/*`, and `/` is now served directly instead of answering 302.
- Tests: `tooling/qa/fixes_tests/test_seo_files.py` (15 tests) and
  `tooling/qa/check-seo.sh`, which also curls the live site and reports what is not
  deployed yet without failing the run.

Notes and decisions:

- **Home page title cannot claim state coverage.** `test_g3_t3_data_note.py` and
  `test_g3_freshness.py` both assert `"Texas &amp; Arizona"` is absent from `index.html`
  — a deliberate product rule. First draft of the title broke both; retitled to
  "Multifamily Construction Pipeline and Recent Apartment Sales | CraneSignal".
- **Test baseline on this machine:** 7 failed, 279 passed, 5 skipped, 7 errors, both before
  and after this step — so nothing was broken. The 7 errors are `test_e1_signin.py` and
  `test_t4_not_found.py` needing Caddy via Docker, which is not installed here. The 7
  failures pre-date this work (`test_af_t3_filter_disclosure`, `test_build_c_lead_pack`,
  `test_build_c_new_leads` ×2, `test_fu2_unlock_csv_sample` ×2, `test_a6_menu_footer`).
- Had to `pip install pytest phonenumbers` — neither was present on this machine.
- The Fire Your SEO Agency audit was skipped: it installs as a Claude Code plugin via a
  slash command, which a scripted session cannot invoke, and the fixes it would recommend
  were already identified by direct inspection plus the research in the strategy file.

## Step 2 — the ~25 pages ⏳ next

## Step 2 — the static pages ✅ 2026-09-23

`tooling/seo/build_pages.py` generates **18 pages** under `site/leads/` from the built JSON.
Not 25: the strategy file's estimate assumed more cities would clear the 25-building floor
than actually do. Everything that clears it has a page; nothing thin was padded to hit a number.

What exists:

- **4 metro pages** — Dallas–Fort Worth (810), Houston (443), Austin (83), San Antonio (43).
  These target the phrase the research found real demand for: "<metro> multifamily
  market report / construction pipeline".
- **2 state pages** — Texas (1,587), Arizona (274).
- **10 city pages** — Dallas, Arlington, Fort Worth, Garland, Grand Prairie, Irving, Plano
  in Texas; Phoenix, Mesa, Scottsdale in Arizona. Arizona has no metro grouping in the data
  (`propertystack/data/az/metros.json` does not exist), so Phoenix is a city page, not a metro
  one. Adding that file would also change the live app's metro buttons, so it is Drew's call.
- **2 cross-cutting lists** — buildings expected to open in 2027–2028 (105), and complexes
  that changed owner in 2025 (626). Listicles are the format answer engines cite most.

Each page carries: a facts strip, a 40–60 word answer block written from its own numbers,
per-place breakdowns (stage, opening year, sale year, busiest cities, largest projects), the
building table with a source link on every row, internal links up and sideways, `Dataset` +
`ItemList` schema, and the data date. No JavaScript is needed to read any of it.

Decisions and problems hit:

- **Metro/city slug collision.** "Houston" the metro and "Houston" the city wrote to the same
  file, silently overwriting three metro pages. The metro page wins (it contains the city's
  buildings plus the suburbs); a namesake city no longer gets its own page. This also avoids
  two of our own pages competing for one phrase.
- **Stylesheet paths were wrong on every page** — `"../" * depth` was off by one. All links
  are now root-relative (`/css/styles.css`, `/leads/...`), which cannot drift with depth.
- **Row cap at 400.** The Texas page was 492 KB of HTML. Rows sort largest-first, the cap keeps
  the most notable buildings, and the page states plainly that it is showing 400 of 1,587.
  Largest page is now ~150 KB.
- **County records arrive SHOUTED.** `pretty()` title-cases them while keeping LLC, LP, III and
  similar intact: "PECOS HOUSING FINANCE CORP" reads as "Pecos Housing Finance Corp". Where a
  sale record has no building name the name field holds the address, so the address column is
  left blank rather than printing it twice.
- **Counties never become pages.** "Tarrant County" is in the data as a place; a page titled
  that way would read as a bug, and nobody searches it.
- **`build_data.py` was not extended after all.** The earlier plan said to put this inside it.
  That script is 1,432 lines and owns the data; this one owns presentation and copies none of
  its logic, so a separate script in `tooling/seo/` is the smaller change and matches
  `build_seo_files.py`. Run order is `build_data.py` → `build_pages.py` → `build_seo_files.py`
  (the sitemap and llms.txt discover the generated pages from disk).
- **Home page.** `index.html` now carries a `SEO-STATIC` block inside the app shell: a real
  heading, the totals, and a link to every generated page. `renderShell()` overwrites it the
  moment `app.js` runs, so a visitor never sees it, but a crawler that does not run JavaScript
  gets content and, more importantly, links.

Tests: `tooling/qa/fixes_tests/test_seo_pages.py`, 118 checks — readable without JavaScript,
enough rows and words, under 260 KB, a source link on every building row, unique titles and
descriptions across all 18, valid schema, in the sitemap, linked from the home page, no
county titles, no RealPage text.

Full suite: **412 passed**, with the same 7 failures / 7 errors as the pre-work baseline.
`tooling/check-no-realpage-target.sh` reports 2 violations both before and after this work
(`docs/2026-09-20-maintenance-software-icp.md`), so they are pre-existing and untouched.

## Step 3 — the "before" measurement ⏳ next

## Step 3 — the "before" measurement ✅ 2026-09-23

`tooling/seo/questions.csv` (25 questions: 15 Set A, 10 Set B) and `tooling/seo/sample.py`,
which asks both engines and writes one JSON per question per engine so a stopped run
resumes without re-asking. **50 answers, no failures.** Saved in
`docs/seo/answer-share/2026-09-23/` with `report.md`.

The numbers that matter:

- **CraneSignal is named in 0 of 30 Set A answers.** That is the before-picture, and the
  point of taking it.
- **Set A (how do I find buildings) is owned by Yardi 83%, CoStar 63%, RealPage 47%.**
  The engines answer "which tool should I buy" when someone asks "where do I find this
  data" — which is the opening: none of them hand over an actual list.
- **Set B (what should I buy) is RealPage 95%, Yardi 85%, AppFolio 80%, Entrata 65%,
  Buildium 60%.** This is the answer-share view, and it is demo-able today.
- **The engines cite vendor sites and market-report publishers**, in this order:
  realpage.com (17), appfolio.com (11), mmgrea.com (9), yardimatrix.com (8), then
  multihousingnews, yardi.com, matthews.com, reddit.com, mrisoftware.com,
  cushmanwakefield, multifamilydive, credaily, buildium.com, g2, capterra. This is the
  most actionable output of the whole run: it names the surfaces a new page has to sit
  beside, and it says that trade press and review sites matter as much as our own pages.

Implementation notes:

- Each Claude question runs a fresh `claude -p --model sonnet --setting-sources ""` with
  `cwd` set to the home directory, so this repo's files and instructions cannot leak into
  an answer and flatter us. 25 calls, well under the 60-call cap.
- Gemini uses `gemini-2.5-flash` with Google Search grounding, key read from `.env.seo`
  and never printed. Grounding links are Vertex redirect URLs that hide the real site, so
  `host_of()` reads the domain out of the chunk title instead.
- Both engines are labelled in every record and in the report as API/CLI, **not** the
  consumer apps. `claude -p` with web search is not what a person sees in the Claude app,
  and the Gemini API is not the Gemini app.
- Claude took ~35s per question (~15 min for 25); Gemini ~7s.

Tests: `tooling/qa/fixes_tests/test_seo_sample.py`, 15 checks, none of which call an
engine or the network. One of them asserts CraneSignal appears in **zero** Set A answers —
when that test fails, the SEO work has started to land, and the baseline note needs
updating rather than the test.

## Step 4 — IndexNow ✅ 2026-09-23

`tooling/seo/indexnow.py` pushes new and changed URLs to Bing, Yandex, Seznam and
DuckDuckGo. Free, no account, no approval — and Bing's index is what ChatGPT search and
Copilot read, so it is the shortest path from "page published" to "an engine can cite it".
Google does not participate and gets the sitemap instead.

- `--init` created `site/indexnow-7774e206da914a60a8f0806be55b8e59.txt`. The key is public
  by design: the engines fetch that file to prove whoever submits controls the host. The
  Caddyfile now serves `/indexnow-*.txt`.
- `--changed-since HEAD~1` submits only what a commit touched, so the weekly data refresh
  does not re-submit all 21 URLs every time.
- The script refuses to submit anything that is not live, including the key file itself:
  an engine that fetches a 404 learns the page does not exist. Nothing has been submitted
  yet, because nothing is deployed. `--dry-run` shows 21 URLs ready to go.

Full suite after steps 3 and 4: **427 passed**, same 7 failures / 7 errors as baseline.
