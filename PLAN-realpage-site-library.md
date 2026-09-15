# CraneSignal: realpage.com library (crawl + organize + chat)

Written 2026-09-15 with Drew. Starts only when Drew says "go work". Localhost only, never push.

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
Try: `docker compose -f chatbot/docker-compose.local.yml up --build`
Open: http://localhost:3000

## How to try it (30 seconds)
1. Ask the local chat "What does RealPage Lumina do?" -- it answers from RealPage's own product card
   and links the realpage.com page.
2. Ask "What is the status of RealPage's DOJ lawsuit, according to RealPage?" -- it answers from the
   key-facts sheet with the date and source link.
3. Ask "Which RealPage products handle resident screening?" -- it names the right products, each with
   a realpage.com link.

## Tasks

- [ ] **T1 Page list.** `tooling/realpage-library/sitemap.py` reads the cms sitemap index and all
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
- [ ] **T5 Product cards + key facts (Gemini, ~60-100 calls).** `tooling/realpage-library/cards.py`
  writes one card per product to `02-products/realpage/<product>.md`: what it does, who it's for,
  current name, old or acquired names, related products, 3-5 key claims -- every line with its
  realpage.com link. Gemini drafts from that product's pages only; code rejects any line without a
  link that exists in `urls.csv`. `facts.py` writes `01-company/realpage-key-facts.md`: company basics,
  leadership (management-team pages), acquisitions and renames, and the DOJ/legal status **as
  RealPage states it**, from press posts and legal pages, newest first, each with date and link.
  Resumes if stopped. Tests with a fake AI. Commit.
- [ ] **T6 Library check.** Offline test that every card and fact line has a valid realpage.com link,
  no card is empty, no duplicate products, and the chat folders (`01-company`, `02-products`) stay
  under 1 MB total (raw pages never leak in). Spot-check 5 cards against the live pages and fix
  wrong ones by hand, noting each fix in `CRAWL-REPORT.md`. Commit.
- [ ] **T7 Chat hookup.** Update `chatbot/hermes-profile/skills/query-propertystack/SKILL.md` and
  `SOUL.md`: for RealPage product or company questions, read `01-company/realpage-key-facts.md` and
  the matching `02-products/realpage/` card first, answer with the realpage.com link, and say
  "according to RealPage" for its own claims (lawsuit included). Confirm the Dockerfile already copies
  these folders (it copies `01-company` .. `09-ai-visibility`). Offline test that the new files are
  found by `ps_research_search` for "Lumina", "screening" and "DOJ". Commit.
- [ ] **T8 Local chat test.** Build and start the local chat (`chatbot/docker-compose.local.yml`),
  ask the 3 "How to try it" questions plus 5 more RealPage product questions, and save the answers
  in `raw/realpage-site/CHAT-TEST.md` with pass/fail per question. Fix and retest failures. Stop the
  containers. Recap for Drew in plain words; do not push or redeploy. Commit.
