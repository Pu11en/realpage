# Local collection assets — verified 2026-09-10

Source: local filesystem inspection
Fetched: 2026-09-10
Method: `ls`, `find`, file reads on /home/drewp
Confidence: high

## Reddit — DSH Reddit On Demand

- Location: `/home/drewp/main-projects/reddit/`
- Read-only `reddit_search` tool (DeepSeek Harness plugin). Hits Reddit's
  public HTTPS JSON endpoints with a saved session cookie (stored in DSH
  credential UI, not in files). Hard caps: 10 posts / 5 comments per query.
- Read `/home/drewp/main-projects/reddit/USAGE.md` — it is an excellent
  playbook for pain-mining, competitor research, and voice-of-customer work.
- In a non-DSH session (like ZCode), the same endpoints are callable directly
  (`https://www.reddit.com/r/<sub>/search.json?q=...`) — unauthenticated JSON
  works for public content until rate-limited; the DSH session cookie raises
  the ceiling. Fallback: pull JSON via curl with a browser UA, cache to `raw/`.

## X / Twitter — Twitter News skill + session

- Session cookie lives in `/home/drewp/.local/share/twitter-news/x-session.sqlite`
  (this is "the cookies somewhere" Drew mentioned). Also `accounts/`,
  `runtime/` there; docs in `/home/drewp/main-projects/jordancrypto/docs/TWITTER_NEWS.md`.
- Upstream project: github.com/Pu11en/crypto-news-agent — one owned X session,
  X's unofficial web interface, no paid API. Registry is crypto-focused but
  the machinery (session + fetch layer) can search arbitrary queries.
- ToS reality: unofficial scraping of X can break or be enforced against;
  use Drew's session for bounded read-only searches only.

## Web crawling — full local stack

- Installed: Crawl4AI 0.8.6, crawlee 1.6.3, playwright 1.59.0,
  playwright-stealth 2.0.3 (`pip list`).
- Use Crawl4AI for realpage.com product/pricing pages → markdown into `raw/`.
- Session MCP tools `web_reader` (webReader) and built-in WebSearch cover
  most research; crawl stack is for bulk/structured captures.

## LinkedIn — constrained

- No scraper, no cookies found locally. Auth-walled and bot-hostile.
- Policy: manual capture by Drew or logged-in browser automation only when
  he initiates. Store in `05-social/` with `Method: manual-capture`.

## Nothing found for

- Glassdoor/Indeed scrapers (use WebSearch + webReader; app is guest-readable
  until challenged, then manual capture).
