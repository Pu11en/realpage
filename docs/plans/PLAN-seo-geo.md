# CraneSignal: SEO + GEO -- get found by Google, get cited by AI answers

Written 2026-09-21 (thread 1551678212600373249). Plan only; nothing installed or changed yet.
Two goals in one stack: (1) make `cranesignal.com` / `app.cranesignal.com` findable and citable,
(2) turn the weekly "what do AIs answer when someone is buying property-management software?"
run into the demo footage for an **answer-share** product (the archived AI Visibility idea, revived
vendor-neutral: see `archive/realpage/PLAN-ai-visibility-v4.md`).

Four free, local, open-source tools; no subscriptions. Matches the outside-in ground rules: we only
read public pages and public AI answers, we post nothing anywhere.

| Step | Tool | Repo | Needs | Runs on |
|---|---|---|---|---|
| 1. Baseline dashboard | **CrawlSEO** | `crawlseo/crawlseo` (MIT) | Docker; Google OAuth client (login + Search Console) | WSL2 + Docker Desktop, port 3100 |
| 2. Audit + fixes | **Fire Your SEO Agency** | `leopard627/fire-your-seo-agency` (MIT) | Claude Code only, no keys | Claude Code plugin |
| 3. Buying-intent tracking loop | **GeoLook** | `aigclink/geolook` (MIT) | Python 3.9+, Linux (`fcntl`); DeepSeek key optional | WSL2, port 8765 |
| 4. Weekly answer-share run | **NiubiGEO** | `Albert-Weasker/niubigeo` (Apache-2.0) | Node 22.13+; Claude + Gemini keys direct (no OpenRouter) | WSL2, port 8787 |

Second opinion (optional, not week 1): `AgriciDaniel/claude-seo` (`/seo audit`, `/seo schema`, `/seo geo`;
Python, has a Windows installer). Install only if the Fire Your SEO Agency audit leaves gaps.

## What the site looks like today (baseline, checked live 2026-09-21)

- **Two hosts.** `cranesignal.com` = landing page (separate `business/` repo on Drew's machine, not this repo).
  `app.cranesignal.com` = this repo's `site/` (Caddy, Railway). Both need the fixes; only the app is ours to edit here.
- **app.cranesignal.com:** `/` answers **302** to `/index.html`; `/robots.txt`, `/sitemap.xml`, `/llms.txt` all **404**
  (`site/Caddyfile` only serves an explicit list of paths); **no JSON-LD** on any page; **every page is a JS shell**
  (`<div id="app-shell"></div>` + `renderShell(...)`), so Googlebot-without-JS and every AI crawler see just the
  `<title>` and one meta description. `property.html` is one template driven by `?id=`, so no building has its own
  crawlable URL. Titles are generic ("CraneSignal -- Leads"). No canonical, no Open Graph tags.
- **cranesignal.com:** has a real title and description; also 404 on robots/sitemap/llms.txt; no JSON-LD.
- Data we can expose: 5 areas (`site/data/areas/{tx,az,nm,ny}.json`), `leads.json`, `map-markers.json`.
- Reusable: 35-row question bank with real Gemini answers from the RealPage AI Visibility run
  (`archive/realpage/ai-visibility/tooling/questions.csv`); `DEEPSEEK_API_KEY` (chat) and `JINA_API_KEY` (`.env`).

## This machine (David, Windows 11 Home)

Python 3.12 and Claude Code 2.1.278 are installed. **No Docker, no Node, no WSL.** GeoLook needs Linux, CrawlSEO
needs Docker (or Node 20 + Postgres), NiubiGEO needs Node 22. One install covers all of it: **WSL2 (Ubuntu) + Docker
Desktop**, then Node 22 (via `nvm`) inside WSL. Side effect: `tooling/dev.sh` (needs Docker) also becomes runnable here.
Needs admin + one reboot. On Drew's Linux box none of this is needed.

**Ports:** CrawlSEO defaults to 3000 (= Open WebUI in `dev.sh`) -> map it to **3100** in its compose file.
GeoLook UI is **8765** (= the dev site in `dev.sh`, port not configurable per its README) -> don't run both at once,
or start the dev site on another port. NiubiGEO 8787 is free.

## Decisions for Drew (ask before the task that needs them)

1. **Google.** Who does the Google runbook below (G1-G5): the Porkbun login holds G1; the rest can be David on
   the same Google account. Also: GA4 yes/no (G4).
2. **Keys.** We have Claude (`ANTHROPIC_API_KEY`), Google (`GEMINI_API_KEY`) and DeepSeek. NiubiGEO's `.env.example`
   takes those directly (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`; also `OPENAI_API_KEY`,
   `PERPLEXITY_API_KEY`), so **no OpenRouter**. Week 1 runs 3 engines: Claude + web search, Gemini + Google Search,
   DeepSeek (from memory, labelled so). ChatGPT joins later two ways: the ChatGPT plan (consumer app) is sampled by
   hand through GeoLook's sample-sheet when it is back on, and an `OPENAI_API_KEY` slots into NiubiGEO if Drew ever
   wants it. Same labels as the archived plan: these are the vendors' API engines, not the consumer apps, except
   the hand-pasted ones. Cost with our keys: ~25 questions x 3 engines weekly, well under $5.
3. **Site changes.** OK to change `site/Caddyfile` (serve robots/sitemap/llms.txt, `/` served directly instead of a 302)
   and to add **static, crawlable HTML** to the app: a pre-rendered summary on the home page, one static page per
   state (`/leads/tx.html` ...), and later one per building. This is the change that actually moves rankings; the
   metadata fixes alone won't. Visible on the live site after deploy.
4. **Landing page fixes** (`business/marketing/landing/index.html`): Drew applies the hand-off list from T3, or gives
   this repo a copy to edit.
5. **Answer-share brand set.** Which vendors to track (proposed: RealPage, Yardi, Entrata, AppFolio, Buildium, ResMan,
   Rent Manager) and whether CraneSignal itself is in the set (it isn't a PMS; it can only be cited on "how do I find
   new apartment buildings / which software does a building run" questions -- see the two question sets in T5).
6. **Weekly note.** Post the Monday answer-share totals to Discord like the Texas weekly run does, or keep it in the repo.

## The Google setup (runbook: one sitting, ~45 min, one Google account)

Use **one** Google account for all of it and write which one in `tooling/seo/INSTALL.md` (no passwords). DNS is at
**Porkbun** (nameservers `*.ns.porkbun.com`); whoever holds the Porkbun login does G1. The site has no Google tag
of any kind today.

- **G1 Search Console -- a Domain property for `cranesignal.com`.** search.google.com/search-console -> Add property
  -> *Domain* -> `cranesignal.com`. It gives one `google-site-verification=...` TXT. Porkbun -> DNS -> add TXT, host
  blank, that value. Verify (can take up to an hour). A Domain property covers `app.cranesignal.com` and `www` too, so
  it's the only property we need. Fallback if DNS is out of reach: a URL-prefix property for
  `https://app.cranesignal.com/` verified with the HTML meta tag; T3 puts the tag in every page head.
- **G2 Submit the sitemaps** (after T3 deploys): Sitemaps -> `https://app.cranesignal.com/sitemap.xml`, and the
  landing's once it has one. Then URL Inspection -> "Request indexing" for `/index.html`, `/under-the-hood.html`
  and each `/leads/<state>.html` (T4). Note the date in `docs/seo/2026-09-baseline.md`; GSC data starts here.
- **G3 Google Cloud project `cranesignal-seo`.** console.cloud.google.com -> new project -> APIs & Services ->
  enable **Google Search Console API** and **PageSpeed Insights API**. OAuth consent screen: External, app name
  "CrawlSEO local", add the G1 account as a test user (stays in "Testing", nobody else can log in). Credentials ->
  OAuth client ID -> Web application -> authorized redirect URI `http://localhost:3100/api/auth/callback/google`
  (and `http://localhost:3000/...` in case the port is left at default). Copy client ID + secret into CrawlSEO's
  `.env` (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`). Credentials -> API key restricted to PageSpeed Insights ->
  `GOOGLE_PAGESPEED_KEY`. Nothing here costs money; these two APIs are free.
- **G4 Analytics (GA4) -- optional, Drew decides.** Only worth it to see if AI referrals arrive
  (`chatgpt.com`, `perplexity.ai` show as referrers). If yes: analytics.google.com -> property -> web stream for
  `app.cranesignal.com` -> `G-XXXXXXXX`; T3 adds the gtag snippet and the CSP in `site/Caddyfile` must allow
  `https://www.googletagmanager.com` in `script-src` and `https://*.google-analytics.com` in `connect-src`; add a
  line to `site/privacy.html`. If no, skip -- GSC impressions are enough for the weekly numbers.
- **G5 Bing Webmaster Tools (5 min, same sitting).** bing.com/webmasters -> "Import from Google Search Console".
  Free; Bing's index feeds ChatGPT search and Copilot, so it counts for the GEO side as much as Google does.
- **Not doing:** Google Business Profile (no physical address to show), Google Ads, Merchant Center.

Where each lands in the tasks: G1 + G3 before **T1**, G2 right after **T3** deploys, G4 inside **T3** if yes, G5 any time.

## Question sets (the loop tracks these every week)

Two sets, because they measure different things:

- **Set A -- CraneSignal's own category** (can we be cited?): "how do I find apartment buildings under construction
  in Dallas", "which property management software does an apartment building use", "list of recently sold apartment
  buildings in Houston with new owners", "how to find new multifamily developments in Texas before lease-up",
  "tools that show which PMS a building runs", "free lead list of new apartment projects Texas". ~15 questions.
- **Set B -- the buying-intent market** (the answer-share product; we are not expected to appear):
  "best PMS for 200-unit buildings in Texas", "best property management software for a multifamily portfolio",
  "RealPage vs Yardi", "AppFolio vs Buildium for 500 units", "what software do large Texas apartment operators use".
  Start from the 35 archived questions, add ~15 with a size + state angle. ~25 questions.

Both sets live in one file, `tooling/seo/questions.csv` (columns: `set,question,intent,brands_expected`), and both
GeoLook and NiubiGEO import from it so the two tools never drift.

## Safety rules (every task)

Read-only toward third parties; polite rate limits; a run that stops keeps everything saved so far. Never print or
commit keys (all `.env` files gitignored). Local testing first; `main` only after Drew's OK. All outputs are dated
files under `docs/seo/` so before/after is provable.

Run with: `Do the next unticked task in PLAN-seo-geo.md, then tick it and stop.`
Check: `bash tooling/qa/check-seo.sh` (T3 creates it; until then `python3 -m pytest -q tooling/qa/fixes_tests`)
Try: `bash tooling/seo/crawl.sh` then open http://localhost:3100

## How to try it (30 seconds, once T1-T4 are done)

1. Open http://localhost:3100: both hosts listed, a health score, and the crawl issues (before) next to the newest crawl (after).
2. `curl https://app.cranesignal.com/llms.txt` and `/sitemap.xml` answer 200; view-source on the home page shows real text and a JSON-LD block.
3. Open `docs/seo/answer-share/<latest>/report.md`: for every Set B question, which vendors each AI named, and the share per vendor.

## Tasks

### Week 1 order: install -> baseline -> audit + fixes -> tracking loop -> first weekly run

- [ ] **T0 Install the stack (David's machine; skip on Linux).** `wsl --install -d Ubuntu` (admin, reboot), Docker Desktop
  with the WSL2 backend, then inside Ubuntu: `nvm` + Node 22, `pip3 install requests beautifulsoup4 lxml`. Clone the
  four repos under `~/seo-tools/` (outside this repo). Write `tooling/seo/INSTALL.md` with the exact commands run,
  versions seen, and the port map (3100 / 8765 / 8787). Commit only the doc.
- [ ] **T1 CrawlSEO baseline (day one).** Needs G1 + G3 done. `cp .env.example .env`, set `NEXTAUTH_URL=http://localhost:3100`, the OAuth
  client + PageSpeed key from G3, `APP_SECRET`/`NEXTAUTH_SECRET` via `openssl rand -hex 32`; change the compose port to 3100;
  `docker compose pull && docker compose up -d`. Add both hosts, run the first crawl and vitals. Export keywords/pages
  CSV (empty until GSC is verified: say so). Save `docs/seo/2026-09-baseline.md`: health score, the 16 issue counts,
  vitals, and the list of pages the crawler could actually read (expect: shells). Add `tooling/seo/crawl.sh`
  (starts the stack, kicks a crawl). Register the MCP server in `.claude/settings.json` (`cwd` = the clone) so later
  sessions can ask "what are the top issues" from the terminal. Commit.
- [ ] **T2 Audit with Fire Your SEO Agency.** `/plugin marketplace add leopard627/fire-your-seo-agency` +
  `/plugin install fire-your-seo-agency@fire-your-seo-agency`. Run the audit on `https://app.cranesignal.com` and
  `https://cranesignal.com`. Save the five-lane scorecard (SEO/AEO/GEO/LLMO; ignore NEO/Naver) to
  `docs/seo/2026-09-audit.md` with the proposed fix list, split into "this repo" vs "landing repo (Drew)". Commit.
  No site change in this task.
- [ ] **T3 Ship the metadata fixes (this repo).** In `site/`: `robots.txt` (allow all incl. GPTBot, ClaudeBot,
  PerplexityBot, Google-Extended; sitemap line), `sitemap.xml` (every real page + per-area URLs from T4),
  `llms.txt` (what CraneSignal is, the areas, how the data is sourced, links to under-the-hood and the free PDF) and
  `llms-full.txt`; JSON-LD on every page (`Organization`, `WebSite`, `SoftwareApplication` for the app, `Dataset`
  for the lead list with `temporalCoverage` = the "Last updated" date); unique `<title>`/description per page,
  `<link rel="canonical">`, Open Graph + Twitter cards using `docs/design-screens/final/*.png`, the GSC
  `google-site-verification` meta tag (G1 fallback) and the GA4 snippet + CSP change only if G4 is yes. `site/Caddyfile`: add
  `/robots.txt /sitemap.xml /llms.txt /llms-full.txt` to the public list; serve `/` as `index.html` directly
  (`rewrite`/`try_files`, no 302). Update the landing hand-off list in `docs/seo/2026-09-audit.md`. Tests in
  `tooling/qa/fixes_tests/test_seo_files.py`: files exist, sitemap lists every `.html` in `site/` except 404 and
  master-table, JSON-LD parses on every page, Caddyfile serves the new paths; `tooling/qa/check-seo.sh` runs them
  plus a live curl of the three files. Re-crawl in CrawlSEO; note the score delta in the baseline doc. Commit. After Drew deploys: do G2 (submit sitemap,
  request indexing).
- [ ] **T4 Crawlable content (needs decision 3).** Add a build step to `site/data/build_data.py` (don't write a
  second builder) that emits static HTML: (a) a `<noscript>`-free, always-present summary block in `index.html`
  (areas, lead counts, last-updated, top 10 leads per area as plain links), (b) one page per state,
  `site/leads/<state>.html` (title "New and recently sold apartment buildings in Texas -- CraneSignal", the lead table
  as real HTML rows linking to `property.html?id=`, sources column), rebuilt on every data run. Keep the app behaviour
  identical; the JS hides/replaces the static block once loaded. Per-building static pages are a **later** task
  (decide after seeing GSC impressions on the state pages). Caddyfile serves `/leads/*`. Sitemap from T3 picks the
  new pages up. Tests: each state page has >= 20 rows of real text and no `RealPage` text. Commit.
- [ ] **T5 GeoLook loop (start tracking).** In WSL: `python3 scripts/geo.py new --url https://app.cranesignal.com
  --market en`; set `DEEPSEEK_API_KEY` in its `.env` for auto-derivation; write `tooling/seo/questions.csv` (Set A +
  Set B above; reuse the 35 archived questions) and load it into GeoLook's question bank; run the first full cycle
  (crawl -> audit -> sample every engine we have keys for -> tickets -> assets). Compare its generated `llms.txt` /
  JSON-LD with T3's and merge anything better into `site/`. Record which of its 10 API engines we actually have keys
  for (its README doesn't list them) and which 7 are manual; do one manual sampling pass via its sample-sheet for
  Perplexity (free tier) and Google AI Overviews now, ChatGPT once the plan is back on (a human pastes answers). Copy `work/<slug>/` outputs to
  `docs/seo/geolook/<date>/`. Commit.
- [ ] **T6 First weekly NiubiGEO run (the demo footage).** `npm ci`, `ANTHROPIC_API_KEY` + `GEMINI_API_KEY` +
  `DEEPSEEK_API_KEY` in its `.env` (no OpenRouter), `npm run server` (8787). Project = `app.cranesignal.com`;
  models: the newest Claude and Gemini the tool lists, web search on where it offers it, DeepSeek as the no-search
  control; keyword tests = Set B without the brand name. First run: confirm the direct-key path actually
  works for each provider and note the exact model IDs in `report.md`. Run, then record the dashboard walkthrough
  (Win+G / OBS, ~2 min: domain -> models -> side-by-side descriptions -> competitor table -> a source click) to
  `docs/seo/answer-share/<date>/demo.mp4` (path only in git if > 10 MB: keep the file in `raw/`). Export the answers
  and write `report.md`: table question x model -> vendors named, plus "share of answers naming each vendor". Commit.
- [ ] **T7 Make it weekly.** `tooling/seo/weekly.sh`: CrawlSEO re-crawl (or its `CRAWL_SCHEDULE`), GeoLook
  `sample-sheet --intent buyer` export, NiubiGEO scheduled measurement, then a one-file `docs/seo/weekly/<date>.md`
  with the four numbers that matter: health score, pages indexed / GSC impressions (once verified), Set A citation
  count, Set B vendor shares. Monday, same timer as the Texas weekly run (`PLAN-texas-weekly.md`; systemd on Drew's
  box, Task Scheduler -> `wsl bash ...` here). Discord note only if decision 6 says yes. Commit.

### After week 1

- [ ] **T8 Answer-share as a product page** (Drew's call after seeing two weekly reports): a vendor-neutral page in
  the style of the archived `ai-visibility.html`, one row per vendor, before/after per week, every quote linked to
  the saved answer. Buyer: PMS vendors' marketing teams. Proof they lack it: the paid trackers ($200-600/mo) don't do
  multifamily buying-intent questions by state and building size.
- [ ] **T9 Per-building static pages** if state pages get impressions in GSC within 4 weeks.
- [ ] **T10 Landing page fixes landed** in the `business/` repo (Drew) and re-audited.
