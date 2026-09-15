# Progress: PLAN-realpage-site-library

## T1 Page list — done 2026-09-15
- Added `tooling/realpage-library/sitemap.py` (reads cms sitemap index + 13 sub-sitemaps, 1 req/sec, drops duplicates, `#` fragments and `/search`), writes `raw/realpage-site/urls.csv` (url,type,lastmod).
- Live run: 3,022 URLs — posts 1912, videos 373, pages 217, webcasts 178, episodes 93, ebooks 75, authors 57, testimonials 45, case-studies 42, management-team 12, hub-terms 8, account-managers 7, podcasts 3.
- Added `tooling/qa/check-realpage-library.sh` (offline pytest, keys unset) + fixtures/tests in `tooling/realpage-library/tests` — 3 passed.
- Open: none. Next is T2 crawler.
