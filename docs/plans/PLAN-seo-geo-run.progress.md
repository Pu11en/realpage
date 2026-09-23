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
