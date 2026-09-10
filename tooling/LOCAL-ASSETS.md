# Local collection assets — verified 2026-09-10

Source: local filesystem inspection
Fetched: 2026-09-10
Method: `ls`, `find`, file reads on /home/drewp
Confidence: high

## Reddit — WORKING standalone CLI (verified 2026-09-10)

- **Tool: `tooling/reddit_search.py`** — standalone replica of the DSH
  `reddit_search` plugin (same endpoints, same bounds: max 10 posts, 5
  comments per post; GET-only; cookie never forwarded through redirects).
- **Cookie source:** `~/.dsh/.credentials.yaml` → `refs.REDDIT_SESSION_COOKIE`
  (saved via DSH Settings → Plugins → Reddit), or env var `DSH_REDDIT_COOKIE`.
  The script reads it at runtime; the secret is never printed or stored.
- **Usage:**
  `python3 tooling/reddit_search.py "realpage" --subreddit PropertyManagement --limit 10 --comments 3 --out raw/reddit/<name>.json`
- **Unauthenticated access is dead:** plain curl (even with a browser UA) gets
  HTTP 403 block pages from this IP; old.reddit.com 302s. The saved session
  cookie is required — do not retry the no-cookie path.
- Upstream plugin + playbook: `/home/drewp/main-projects/reddit/` (README,
  USAGE.md — pain-mining, competitor, and voice-of-customer playbook).

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
