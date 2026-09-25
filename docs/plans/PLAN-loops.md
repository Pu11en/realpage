# What should run on a loop

Written 2026-09-25. Everything built so far is a one-shot: someone ran it, it worked, and it
will quietly rot. This is about what should keep running without anyone remembering.

## The rule that decides what gets a loop

**A loop earns its place only if it changes something, or if someone will read it when it
speaks.** Anything else is a job that turns green forever, gets ignored, and trains everyone
to ignore the one that eventually turns red.

Two consequences, applied throughout:

- A loop that produces a report nobody opens is worse than no loop, because it costs
  attention and returns none.
- A loop should be **silent when fine and loud when broken**. A weekly "all good" email is
  the fastest way to make a real failure invisible.

## What we actually have to run loops on

Checked 2026-09-25, because this determines what is possible rather than desirable:

| Where | What it can do | Catch |
|---|---|---|
| **GitHub Actions** on `Pu11en/realpage` | Anything on a schedule, free and unlimited — the repo is public. Committing to `main` triggers the Railway deploy, so an Action can ship. | No Claude, no Gemini key unless added as a secret. |
| **Drew's Linux box** | systemd timers, already assumed by `PLAN-texas-weekly.md`. Has the data pipeline and Railway CLI. | Only runs when that machine is on. |
| **`CronCreate` in a Claude session** | Prompts on a schedule. | **Session-only, and expires after 7 days.** Not a loop. Useful for "remind me this afternoon", nothing more. |
| **David's Windows machine** | Task Scheduler. | No Docker, no WSL, machine sleeps. Not dependable. |

So: **GitHub Actions is the loop engine.** Drew's box keeps the data pipeline. Nothing
important should depend on a Claude session staying alive.

## The loops, in order of what breaks without them

### 1. Freshness — the one that must exist

**Problem it solves, today:** the data was last refreshed 2026-09-20. It is now five days
old. Every one of the 18 pages, the sitemap's `lastmod`, llms.txt's counts and the home
page's pre-JavaScript block is **generated from that data**, and nothing re-runs the
generators when it moves. The moment a refresh lands, the site starts making false claims
about its own freshness — and freshness is the single ranking signal this whole plan leans
on. A sitemap that lies about `lastmod` is worse than no sitemap: it actively tells crawlers
nothing changed.

**The loop:** on any push touching `site/data/**` or `tooling/seo/**`, and once on Monday
after the weekly data run — regenerate everything derived, run the tests, and commit **only
if something actually changed**. The commit deploys. Then push only the changed URLs to
IndexNow, after a pause for the deploy, because submitting a URL that 404s teaches the engine
the page is gone.

Drafted at `docs/plans/drafts/seo-freshness.yml.draft`. Kept out of `.github/workflows/`
on purpose: dropping it there would arm it immediately, and whether a bot may commit to
`main` is Drew's call — see the open question at the bottom.

**Silent when fine:** if the generated files already match the data, it commits nothing and
says so.

### 2. The live guard — cheap, and catches the class of bug that already bit us

**Problem it solves:** today the landing page's three new files were in the repo, passed
every test, and would have 404'd in production forever, because the Dockerfile copies an
explicit file list. Nothing would have told us. DrewAI caught it by hand.

**The loop:** daily, fetch the live site and check the things that are invisible when they
break — `robots.txt`, `sitemap.xml`, `llms.txt` and `llms-full.txt` all 200; `/` serves 200
rather than redirecting; a sample of the `/leads/` pages 200 and still contain their tables;
no `noindex` anywhere it should not be; the share card and logo still resolve; 404s still
404. Both hosts.

Opens a GitHub issue when something fails, and says nothing at all when it passes.

**Why daily and not hourly:** nothing here changes hour to hour, and a job that fires 24
times a day becomes wallpaper.

### 3. Data staleness — an alarm, not a report

**Problem it solves:** the product's whole claim is freshness. If the weekly data run stops —
Drew's machine off for a fortnight, a source changing shape — the site keeps serving
confident dated numbers that are quietly months old. Nobody notices, because nothing breaks.

**The loop:** daily, read `updated` from `site/data/areas/index.json`. Say nothing under 10
days. Over 10 days, open an issue. Over 21 days, say so loudly, because at that point the
"last updated" line on every page is doing reputational damage rather than good.

Cheap enough to fold into loop 2 rather than run separately.

### 4. The answer-share measurement — monthly, and human-triggered

**Why not an Action:** it needs `claude -p` on the subscription and the Gemini key. The
Claude half cannot run in CI at all.

**Why monthly rather than weekly:** the numbers wobble a few points week to week on their
own. Sampling weekly would produce noise and burn subscription quota to do it. The signal
we care about — does CraneSignal get named at all — moves on the scale of months.

**The loop:** a calendar reminder, not automation. First run 2026-10-09
(`PLAN-seo-remeasure-2026-10-09.md`), then the 9th of each month. A session runs
`tooling/seo/sample.py`, appends to the table, and stops.

### 5. Outreach packs — on demand, never scheduled

Deliberately **not** a loop. A pack is built for a named person at a named company, minutes
before it is sent. Generating fifteen packs on a Monday that nobody sends produces stale
files and the illusion of progress.

## What must not go on a loop

- **Posting.** `marketing-board/README.md` requires Drew's explicit approval per platform,
  and the rule is right: an automated public post is how a brand says something it cannot
  take back.
- **Outreach sends.** Same reason, higher stakes — these go to named people.
- **Adding pages.** The 18-page ceiling is a deliberate defence against the sitewide
  thin-content penalty. A loop that "adds pages when data grows" would walk straight into it.
- **Anything that emails a green summary.** See the rule at the top.

## Loop 0, which was missing: run the tests at all

Written 2026-09-25 as `docs/plans/drafts/tests.yml.draft`, and it goes first because every
other loop assumes a green suite and there was not one.

There was **no CI in this repo**, and `tooling/qa/check-seo.sh` runs a single test file. So
nothing ran `tooling/qa/fixes_tests/` end to end, and **eight tests had been red for four
days** without anyone knowing:

- Three were stale assertions against `site/index.html`, all traceable to deliberate product
  changes that never reached the tests — `7ec4b52` and `e8d956c` un-gated the PDF and the
  spreadsheet, and a template refactor turned the Region pill's label from a ternary into a
  plain string. The behaviour was fine; the tests described code that no longer existed.
- Five failed only because **Node and Caddy are absent on Windows**, so on David's machine
  the suite could never be green. That is the worse half: it made the three real reds
  invisible, and it is exactly the "trains everyone to ignore red" failure this plan warns
  about in its first paragraph.

Those five now **skip** when the tool is missing, and `CRANESIGNAL_REQUIRE_TOOLS=1` turns the
skip back into a failure — set in CI, where the tools are there and a skip would be hiding
something. Same shape as `check-seo.sh --live-required`.

**This one is safe to arm, unlike loop 1's.** It only reads — no commit, no deploy, no
secret — so there is nothing to decide. It sits in `drafts/` only because GitHub refuses a
push that adds a workflow file unless the token has the `workflow` scope, and the session
token does not. Copying it to `.github/workflows/tests.yml` from a normal sign-in is the
whole job. Loop 1's freshness workflow stays drafted for the real reason instead: it commits
to `main`.

## Order to build

1. **Loop 0.** The suite is green (552 passing, 16 skipped). One `cp` away from running in CI.
2. **Loop 2, the guard, next.** It is the cheapest, it has already proven necessary today,
   and it protects everything else. Half an hour.
3. **Loop 1, freshness.** Bigger, and it commits to `main`, so it wants the guard in place
   first to catch it if it ships something wrong.
4. **Loop 3** folded into loop 2 as an extra check.
5. **Loop 4** is a reminder, not code.

## Open questions, genuinely open

- **Should an Action be allowed to commit to `main` and so deploy unattended?** Loop 1 needs
  it to be worth anything, and the alternative — opening a PR nobody merges — is the same
  rot with extra steps. But `AGENTS.md` says main deploys only after Drew's OK, and a bot
  committing to main is a real change to how this repo works. **Drew's call.** Until then the
  workflow stays drafted and disabled.
- **Where do failures go?** A GitHub issue is the default and needs no secrets. The Discord
  bot would be better read, and there is already a `/api/notify` pattern in
  `PLAN-texas-weekly.md`. Discord needs a webhook in repo secrets.
- **Is the weekly data run actually running?** `PLAN-texas-weekly.md` describes a systemd
  timer on Drew's box. The data being five days old is consistent with it running last
  Sunday — or with it never having been switched on. Worth confirming before building a
  freshness loop around it, because if nothing refreshes the data, loop 1 has nothing to do
  and loop 3 is the only one that matters.
