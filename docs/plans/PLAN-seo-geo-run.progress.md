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
