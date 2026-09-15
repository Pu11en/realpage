# realpage.com crawl report

Crawled 2026-09-15 with `tooling/realpage-library/crawl.py` (Crawl4AI, Jina fallback, 1 req/sec).

- **2,195 of 3,022 sitemap pages saved.** Every non-blog type is complete: pages 217, videos 373,
  webcasts 178, episodes 93, ebooks 75, authors 57, testimonials 45, case studies 42,
  management team 12, hub terms 8, account managers 7, podcasts 3.
- **Blog posts: 1,085 of 1,912.** Drew chose to stop here (the rest are older market-commentary
  posts, not needed for product cards or key facts). Resume anytime: rerun `crawl.py` -- it skips
  saved pages.
- **Failures: 0** (`failed.csv` empty after one retry). A handful of pages came via the Jina fallback.
- First run paused when Docker crashed on the machine (unrelated to the crawler, which needs no Docker).
- Spot-checked main pages (e.g. multifamily, company, user group): clean text, link header, no menus.
- Page index: `01-company/realpage-site-index.md`. Product list: `raw/realpage-site/products.csv`.
