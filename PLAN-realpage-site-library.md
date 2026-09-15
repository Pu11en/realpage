# CraneSignal: realpage.com library (crawl + organize + chat)

Written 2026-09-15 with Drew. Part 1 of 2 (T1-T4: crawl + page index, no AI). Part 2 (T5-T8, Gemini cards + chat) is `PLAN-realpage-site-library-part2.md` and waits for Drew. Localhost only, never push.

Goal: download all of realpage.com, organize it so an AI agent can use it, and let the CraneSignal
chat answer RealPage questions from it. The same library later feeds the AI Visibility
"what AIs get wrong about RealPage" check (separate plan, not this one).

Drew's answers:
- **Whole site**, not just key pages.
- **Three layers:** (1) one clean text file per page, (2) a short card per RealPage product
  (what it does, who it's for, current name, old names), (3) one key-facts sheet (lawsuit status as
  RealPage states it, acquisitions, product renames, company basics). Every fact and card line
  carries the realpage.com link it came from.
- **Chat hookup is part of this plan** (last tasks), tested on localhost only.

What we know (checked 2026-09-15):
- `robots.txt` allows crawling except `/search`. Sitemap index: `https://www.realpage.com/cms-sitemap.xml`
  -> 13 sub-sitemaps, about 3,000 pages: posts 1,912, videos 373, pages 217, webcasts 178,
  episodes 93, ebooks 75, authors 57, testimonials 45, case studies 42, management team 12,
  hub terms 8, account managers 7, podcasts 3. `/sitemap.xml` is a 404 -- use the cms one.
- Tools already on this machine (free): Crawl4AI 0.8.6 (Python) and the `crawl4ai-server` Docker
  container; Jina Reader (`JINA_API_KEY` in repo-root `.env`) as fallback for pages Crawl4AI fails on.
  Brave is for search only and is not needed here. SearXNG is banned. Never print or commit keys.
- The chat (`chatbot/`) reads markdown under `01-company` .. `09-ai-visibility` via
  `ps_research_search` (line-by-line keyword match, returns the full file list on every call) and
  `ps_research_read`. So 3,000 raw pages must **not** go into those folders -- only the cards, the
  facts sheet and a compact page index do. Raw pages live in `raw/realpage-site/`.

Safety rules (every task): tests never touch the network or any AI (saved fixture pages only). The
crawl is polite: 1 request per second, one at a time, a clear user agent, honours robots.txt,
resumes after a stop (skips pages already saved). Only T3 crawls for real; only T5 calls an AI.
The AI for T5 is Gemini (free key in `.env`, keep the 7-second throttle) -- about 60-100 calls.
Nothing pushes; the live chat is not redeployed by this plan.

Run with: `Do the next unticked task in PLAN-realpage-site-library.md, then tick it and stop.`
Check: `bash tooling/qa/check-realpage-library.sh`
Try: `cat raw/realpage-site/CRAWL-REPORT.md`
Open: (no page -- part 1 is files only)

## How to try it (30 seconds)
1. The crawl report shows about 3,000 pages saved, counts per type, and few failures.
2. Open any saved product page: clean readable text, with its realpage.com link at the top.
3. The page index lists RealPage's main pages and products, each with a link.

## Tasks

- [x] **T1 Page list.** `tooling/realpage-library/sitemap.py` reads the cms sitemap index and all
  sub-sitemaps into `raw/realpage-site/urls.csv` (url, type from the sitemap name, lastmod).
  Drops duplicates and `/search`. Create `tooling/qa/check-realpage-library.sh` (runs
  `pytest tooling/realpage-library/tests` offline, no keys) and test on saved sitemap fixtures. Commit.
- [ ] **T2 Crawler.** `tooling/realpage-library/crawl.py` fetches each URL with Crawl4AI and saves
  clean markdown to `raw/realpage-site/pages/<type>/<slug>.md`, each starting with a small header:
  url, title, type, lastmod, crawled date. Strips menus, footers and cookie banners. Jina Reader
  fallback when Crawl4AI returns an error or under 200 characters. 1 request/sec, resumes by skipping
  saved pages, logs failures to `raw/realpage-site/failed.csv`. `--limit N` for a practice run. Tests
  with saved HTML fixtures and a fake fetcher. Commit.
- [ ] **T3 Real crawl.** Run `crawl.py --limit 20`, spot-check 5 pages by eye against the live site
  (text complete, no menu junk), fix the cleaner if needed, then run the full crawl (~3,000 pages,
  ~1 hour; restart resumes). Retry `failed.csv` once. Record counts per type and failures in
  `raw/realpage-site/CRAWL-REPORT.md`. Commit the pages (plain text only).
- [ ] **T4 Page index.** `tooling/realpage-library/index.py` writes `01-company/realpage-site-index.md`:
  one line per non-blog page (pages, case studies, ebooks, management team, testimonials, hub terms)
  with title, type and link, grouped by type; blog posts, videos, webcasts and episodes as a
  count plus the 50 newest titles. Also finds the product pages (from `/products/`-style URLs and
  the site menu) and lists them in `raw/realpage-site/products.csv` (name, url, related pages).
  Tests on fixtures. Commit.
