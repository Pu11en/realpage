# Progress: PLAN-realpage-site-library

## T1 Page list — done 2026-09-15
- Added `tooling/realpage-library/sitemap.py` (reads cms sitemap index + 13 sub-sitemaps, 1 req/sec, drops duplicates, `#` fragments and `/search`), writes `raw/realpage-site/urls.csv` (url,type,lastmod).
- Live run: 3,022 URLs — posts 1912, videos 373, pages 217, webcasts 178, episodes 93, ebooks 75, authors 57, testimonials 45, case-studies 42, management-team 12, hub-terms 8, account-managers 7, podcasts 3.
- Added `tooling/qa/check-realpage-library.sh` (offline pytest, keys unset) + fixtures/tests in `tooling/realpage-library/tests` — 3 passed.
- Open: none. Next is T2 crawler.

## T2 Crawler — done 2026-09-15
- Added `tooling/realpage-library/crawl.py`: Crawl4AI plain-HTTP fetch (no browser), own cleaner keeps `<main>` and drops menus/header/footer (`data-swiftype-index='false'`), cookie/OneTrust banners, scripts, icon glyphs; Crawl4AI turns it into markdown. Saves `raw/realpage-site/pages/<type>/<slug>.md` with a header (url, title, type, lastmod, crawled, source).
- Jina Reader fallback when Crawl4AI errors or text < 200 chars (key read from `.env`, never printed). 1 req/sec, one at a time, resumes by skipping saved files, failures to `failed.csv`. Flags: `--limit N`, `--only-failed` (for T3's retry), `--no-fallback`.
- Tests: `tests/test_crawl.py` + fixture `product-page.html`, fake fetchers — check script 9 passed. Live smoke of 2 pages into /tmp (not kept): both clean, readable.
- Open: nothing. T3 runs the real crawl.
