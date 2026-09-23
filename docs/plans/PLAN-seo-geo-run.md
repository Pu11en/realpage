# The 6-hour SEO/GEO run — prep sheet and running order

Written 2026-09-23 (thread 1551678212600373249). This is the plan for one long unattended session.
The what-and-why lives in `PLAN-seo-geo.md`; this file is only about making six hours pay off.

## What I checked before writing this (all real, today)

- Network out is fine: nodejs.org, codeload.github.com, pypi.org all answer.
- Python 3.12 with `requests`, `beautifulsoup4`, `lxml` already importable.
- `claude -p --model sonnet` works from inside a session and answers. **This is the one AI engine
  we can actually use today.**
- **There is no `.env` in this repo on this machine.** No `GEMINI_API_KEY`. (DeepSeek is out by Drew's call anyway.)
  So NiubiGEO cannot run here yet, and neither can GeoLook's automated sampling.
- No Docker, no Node, no admin, no WSL, and nobody at the keyboard to click UAC. CrawlSEO needs a
  Google OAuth client that doesn't exist yet, so its dashboard cannot be logged into either.
- The data is much better than I assumed: **1,861 visible leads** (Texas 1,587 + Arizona 274),
  **146 Texas cities**, 5 metros, 259,251 units in play, 794 with a recorded sale, every row carrying
  a public source link. That is a real, unique, sourced content asset — it is the whole SEO bet.

## What that means for the run

Three of the four tools are blocked on credentials I don't have, so **a run spent installing tools
would produce almost nothing.** The run is therefore built around the two things that need no
credentials and carry all the value:

1. **Make the site readable** — metadata plus real, crawlable pages built from those 1,861 leads.
2. **Take the "before" measurement with the only engine we have** — Claude, on the subscription.

Tool installs are last, time-boxed, and allowed to fail.

## Guardrails (fixed, not negotiable during the run)

- All work on branch **`seo-geo-week1`**. Never `main`, never pushed, never deployed.
- Every task ends with a commit and a line appended to `docs/plans/PLAN-seo-geo-run.progress.md`,
  so a compaction or a crash loses at most one task.
- The full test suite must pass before each commit:
  `python -m pytest -q chatbot/tests tooling/realpage-library/tests tooling/qa/fixes_tests`.
  A task that cannot go green gets reverted and written up, not forced through.
- `bash tooling/check-no-realpage-target.sh` must still exit 0.
- **Claude sampling cap: 60 `claude -p` calls total** (~25 questions, one pass, plus retries).
  Hard-stop at 60 even if questions remain; note what was skipped. Each call is a fresh process
  with `--setting-sources ""` so none of this repo's context leaks into the answer.
- Nothing touches third-party sites beyond normal page reads. No posting anywhere.
- A lounge note at the start, at the halfway mark, and at the end. Nothing else posted.

## Running order

**Hour 1 — Audit and metadata.**
Install the Fire Your SEO Agency skill (a plugin, no admin). Run its audit against
`https://app.cranesignal.com` and `https://cranesignal.com`, save the scorecard to
`docs/seo/2026-09-audit.md`, split the fix list into "this repo" and "Drew's landing repo".
Then ship T3: `robots.txt` (allowing GPTBot, ClaudeBot, PerplexityBot, Google-Extended),
`sitemap.xml`, `llms.txt` and `llms-full.txt`, JSON-LD on every page (Organization, WebSite,
Dataset with the real lead counts), unique titles and descriptions, canonical links, Open Graph
cards, and the `site/Caddyfile` changes that make those files reachable and stop `/` from being a
302. Tests in `tooling/qa/fixes_tests/test_seo_files.py`. Commit.

**Hours 2–4 — The pages that actually matter (T4).**
Extend `site/data/build_data.py` (not a second builder) to emit static HTML alongside the JSON:

- One page per state: `site/leads/tx.html`, `site/leads/az.html`.
- One page per metro: `site/leads/tx/dallas-fort-worth.html`, `houston`, `austin`,
  `san-antonio` — 810 / 443 / 83 / 43 leads respectively, so each is a substantial page.
- One page per city with at least 15 leads (Dallas 310, Houston 294+56, Arlington 200, Austin 68,
  Fort Worth 58, Irving 43, San Antonio 36, Plano 34, Garland 29 …). City names in the data are
  inconsistently cased and some are counties — normalise and merge before generating, and skip
  anything that isn't a real city.
- Each page: a real `<h1>` naming the place, a paragraph of plain text stating what the list is and
  when it was updated, a genuine HTML table of leads (name, address, units, stage, opening or sale
  date, developer, source link), internal links up to the metro and state page, and JSON-LD
  `ItemList`. No RealPage text anywhere.
- A summary block in `index.html` that is present in the HTML before JavaScript runs, and that the
  app replaces on load, so visitors see no change.
- `site/Caddyfile` serves `/leads/*`; the sitemap from hour 1 regenerates to include every new page.
- Tests: every generated page has a unique title, ≥ 15 real rows, a working source link on each row,
  and passes the RealPage check. Commit after the state pages, again after the metro pages, again
  after the city pages — three commits, so a failure late doesn't lose the earlier work.

**Hour 5 — The "before" measurement (Claude only).**
Write `tooling/seo/questions.csv` with the two sets from `PLAN-seo-geo.md` (Set A, ~15 questions
CraneSignal could plausibly be cited for; Set B, ~10 buying-intent questions from the archived
RealPage bank). Write `tooling/seo/sample_claude.py`, lifted from
`archive/realpage/ai-visibility/tooling/local_ai.py`: fresh `claude -p --model sonnet
--setting-sources "" --allowedTools WebSearch,WebFetch` per question, JSON per answer, resumable,
capped at 60 calls, with `fake_ai.py`-style tests that never call Claude. Run it once. Write
`docs/seo/answer-share/2026-09-23/report.md`: for every question, which companies were named, in
what order, with which sources cited — and for Set A, whether CraneSignal appeared at all
(expected: no, and that is the point). Label it honestly as Claude-via-CLI, not the consumer app.
Commit.

**Hour 6 — Install what can be installed, then write the handoff.**
Time-boxed 30 minutes: Node 22 from the official ZIP into `%LOCALAPPDATA%` (no admin), clone
NiubiGEO and GeoLook, `npm ci`, scaffold their `.env` files with the key names left blank, and try
GeoLook with a small `fcntl` shim. Whatever comes up, comes up; whatever doesn't gets one paragraph
in `tooling/seo/INSTALL.md` saying exactly how it failed. Then the handoff: update
`PLAN-seo-geo.md` ticks, write the end-of-run summary at the top of the progress file — what shipped,
what the numbers were, what is waiting on David, what is waiting on Drew — and post the closing
lounge note.

## What you'll have at the end

A branch with the site genuinely readable by Google and by AI crawlers: robots, sitemap, llms.txt,
schema, and roughly 50–150 real pages built from sourced lead data, every one of them tested and none
of them deployed. An audit scorecard. A dated "before" record of what Claude answers for 25 buying
questions, naming every company it mentions. And an honest install note about the three tools that
need credentials.

What you will **not** have: Search Console numbers (needs your Google setup), Gemini or DeepSeek
answers (needs keys), a CrawlSEO dashboard (needs the OAuth client), or anything live (needs Drew).

## What I need from you before I start

1. **"Go"** — and confirm: branch `seo-geo-week1`, local commits only, nothing pushed, nothing deployed.
2. **Permission to write the static pages** (they only exist on the branch; Drew still decides whether
   they ever ship). If this is a no, the run is worth about 90 minutes, not 6 hours — say so and I'll
   shrink it.
3. **The Claude sampling cap** — 60 `claude -p` calls will use subscription quota on top of the run
   itself. Confirm 60, or give me a smaller number, or say "skip the sampling" and hour 5 becomes more
   city pages.
4. Optional, not blocking: if `.env.seo` (Google) or a `.env` with `GEMINI_API_KEY` appears before I start, I'll fold the CrawlSEO baseline and the Gemini leg in.

## Known risks, and what I do about each

- **Context compaction mid-run.** Progress file after every task; each task self-contained.
- **A generated page looks wrong.** Tests check structure, not taste. First state page gets written
  to `docs/seo/sample-page.html` too, so you can eyeball one without running anything.
- **Messy city data** (`GARLAND (DALLAS CO)`, `Tarrant County`, all-caps). Normalise, merge, and skip
  non-cities; the skip list goes in the progress file.
- **`claude -p` burning quota.** Hard cap, resumable, and the script stops on the first auth error
  rather than retrying in a loop.
- **A tool install eats the clock.** Hard 30-minute box in hour 6; failure is an acceptable outcome
  and gets written up.
