# RESUME PACK — RealPage knowledge base (single file)

Generated: 2026-09-10 from the working tree of `github.com/Pu11en/realpage`
(base commit b24ab3f plus same-day edits to `HANDOFF.md` and `progress.md`,
committed together with this file). This bundles the KB's six "read first"
documents, verbatim, so a session with **no access to the repo's disk and no
access to GitHub** can still work from the real evidence.

## FOR DREW

Paste this entire file as the first message in the target session, or attach it
as a `.md` file. Nothing else is needed to start the planning session.

## FOR THE AGENT READING THIS

- The six sections below ARE the repo's reading set, verbatim copies. Treat them
  as `HANDOFF.md`, `README.md`, `task_plan.md`, `findings.md`, `progress.md`,
  and `04-reddit/index.md` respectively.
- Your task is the planning session. Use the prompt in "FILE: HANDOFF.md" →
  "Copy-paste prompts" → "Brainstorm / planning session": brainstorm from the
  evidence (especially `findings.md` § "Reddit sweep" and § "Landscape check",
  and the Reddit pack below), pressure-test the five candidate directions, help
  Drew pick one, then turn the winner into a concrete plan — what it is, who
  it's for, what "working" looks like, ordered first steps. Planning only;
  no building.
- Not included: the 25 raw Reddit capture files (`raw/reddit/*.json`) and all
  other `raw/` captures. The distilled Reddit pack below is the evidence
  artifact for planning. If you need a specific raw capture, ask Drew to attach
  it from the repo or from `C:\Users\Public\realpage-raw-reddit\`.
- Do not re-fetch anything. Treat this pack as the source of truth it
  duplicates.


---

========== BEGIN FILE: HANDOFF.md ==========

# HANDOFF — start here

One-file bootstrap for any agent or session picking up this repo with **no prior
context**. If you read only one file, read this one; it points at everything else.
`task_plan.md` is the live plan and wins over this file on any conflict.

Repo (public): https://github.com/Pu11en/realpage

## Lowest-cost ways to get the repo

- If a clone of this repo already exists on the machine, use it — do not re-clone.
  It lives at `/home/drewp/main-projects/realpage` (remote already configured,
  push-ready) on Drew's main machine.
- One-command clone (needs git, no auth for read):
  `git clone https://github.com/Pu11en/realpage.git`
- Git-free, single request (if git is unavailable):
  `curl -fsSL https://github.com/Pu11en/realpage/archive/refs/heads/main.tar.gz | tar xz`
- Read-only, one file at a time (raw URL pattern):
  `https://raw.githubusercontent.com/Pu11en/realpage/main/<path>`
- Zero-disk, zero-network, one paste/attach: `RESUME-PACK.md` (repo root) —
  HANDOFF + README + planning trio + the Reddit pack, verbatim in one file,
  for sessions where both the local disk and GitHub are unreachable.

## What this is

A cited-evidence knowledge base about **RealPage** (property management software,
realpage.com), built so future sessions can answer questions or build products
about the company without asking Drew for background.

Conventions (full version in `README.md`): every file opens with
`Source / Fetched / Method / Confidence` headers; `raw/` captures are verbatim
and never edited; exact quotes are preserved; distilled analysis lives in
`01-company/` … `09-build-ideas/`.

## Read first, in order

1. `README.md` — conventions, how to use the KB
2. `task_plan.md` — live plan: phases, statuses, next step, decisions, errors
3. `findings.md` — distilled evidence so far
4. `progress.md` — session log, newest first
5. `04-reddit/index.md` — completed Reddit evidence pack

## Where things stand (2026-09-10)

- **Phase 2 (Reddit) COMPLETE:** 25 queries, 142 unique posts, 25 subreddits,
  2020–2026. Raw JSON in `raw/reddit/`; distilled pack in `04-reddit/index.md`.
- **Phase 1 (reviews) PARTIAL:** Software Advice captured in full
  (`raw/reviews/software-advice-realpage-2026-09-10.md`); Capterra indirect only
  (`raw/reviews/capterra-search-summary-2026-09-10.md`); **G2, Capterra,
  TrustRadius block headless crawling** (DataDome / Cloudflare) — need a real
  browser session, read-only.
- **Phases 3–7 PENDING:** DOJ primary docs (justice.gov is open — no blocker),
  realpage.com crawl (products/pricing/case studies), competitor stubs,
  social, synthesis.
- **ONE OPEN DECISION FOR DREW:** which of five candidate build directions to
  pursue — (1) public evidence library, (2) investigation/content series,
  (3) tool for 50–500-unit property managers, (4) migration/switch tooling,
  (5) renter-side watch. Details in `findings.md` + `progress.md`.

## Next actions, in order

1. Ask Drew which build direction he leans toward (or rejects); record the
   answer in `task_plan.md` → Decisions Made.
2. Continue collection regardless of his answer: Phase 3 (DOJ complaint +
   proposed final judgment → `raw/legal/`) and Phase 4 (realpage.com pages →
   `raw/site/`).
3. G2 / Capterra / TrustRadius only via real-browser automation.

## Constraints

- **The repo is PUBLIC.** Never commit credentials, cookies, tokens, or session
  data. `tooling/reddit_search.py` reads its Reddit cookie from a local machine
  path at runtime — that file (and any cookie value) must never be added.
- Reddit collection: `tooling/reddit_search.py` with the cookie saved at
  `~/.dsh/.credentials.yaml` (Drew's machine only). Pacing: 100 requests /
  ~3 min → ≤8 posts with 2 comments per query, ~20 s between queries.
- Read-only toward third parties: no posting, voting, or account actions.
- Show every markdown file created or updated in the session reply, in full
  (fenced, labeled with the filename), so Drew can read files without opening them.
- Update `task_plan.md`, `progress.md`, and `findings.md` as you work.

## Copy-paste prompts

### Brainstorm / planning session

```text
Planning session: RealPage knowledge base → what we build from it.

Repo (public): https://github.com/Pu11en/realpage
Start with HANDOFF.md, then task_plan.md, findings.md, 04-reddit/index.md.

The evidence is collected; the direction isn't chosen. Five candidates are
sketched: public evidence library, investigation/content series, a tool for
50–500-unit property managers, migration/switch tooling, renter-side watch.

Brainstorm with me — bring observations from the repo's evidence and go back
and forth on them — pressure-test those five, help me pick one, then turn the
winner into a concrete plan: what it is, who it's for, what "working" looks
like, and ordered first steps. Planning only this session; no building yet.
```

### Collection continuation

```text
You are resuming work on a RealPage knowledge base.
Repo (public): https://github.com/Pu11en/realpage
Read HANDOFF.md first, then README.md, task_plan.md, findings.md, progress.md,
and 04-reddit/index.md. Work read-only toward third parties; never commit
credentials (the repo is public). Ask Drew which of the five build directions
he leans toward, record it in task_plan.md, then continue collection with
Phase 3 (DOJ primary docs → raw/legal/) and Phase 4 (realpage.com crawl →
raw/site/). Show every markdown file you create or update in full in your
reply. Keep the planning files updated, commit, and push when done.
```


========== END FILE: HANDOFF.md ==========


---

========== BEGIN FILE: README.md ==========

# RealPage Knowledge Base

Single source of truth for everything we know about RealPage (realpage.com) —
property management software company. Purpose: any future agent session can
open this repo, read this file, and answer questions or build things about
RealPage **without asking Drew anything**.

## How to use this KB (for any future session)

1. Read this README first.
2. Check `00-BACKLOG.md` for what's collected, what's stale, what's next.
3. For the live work plan read `task_plan.md` (phases + next step) together
   with `findings.md` (distilled evidence) and `progress.md` (session log).
   These are the resume-cold files — trust them over any chat memory.
3. Every folder holds markdown files. Synthesized files cite raw files; raw
   files carry source URL + fetch date. Trust raw over summary on conflict.
4. Add new evidence as files, register them in the folder's index section
   below, never delete raw evidence.

## Conventions

- One topic per file. File names: lowercase-hyphenated, dated `YYYY-MM-DD-`
  prefix only when multiple snapshots of the same thing exist.
- Every file starts with a header block: `Source:`, `Fetched:`, `Method:`,
  `Confidence:` (high/medium/low).
- Raw captures live in `raw/` (verbatim excerpts, JSON dumps, page text).
  Distilled insight lives in the numbered folders and must link the raw file.
- Voice-of-customer files preserve **exact phrases** in quotes — never
  paraphrase complaints; paraphrase belongs in the analysis line below the quote.
- Claims without a linked source are marked `(unsourced)`.

## Map

| Folder | What's inside |
|---|---|
| `01-company/` | Profile, ownership, leadership, timeline, financials |
| `02-products/` | Product lines, pricing, tech stack, integrations |
| `03-reviews/` | G2, Capterra, TrustRadius, Glassdoor, app-store reviews |
| `04-reddit/` | Subreddit evidence packs with URLs + dates |
| `05-social/` | X posts (`x/`), LinkedIn observations |
| `06-news/` | DOJ antitrust case, press, product launches |
| `07-competitors/` | Yardi, AppFolio, Entrata, Buildium, etc. |
| `08-voice-of-customer/` | Distilled pain themes, personas, exact language |
| `09-build-ideas/` | Ranked things we could build, tied to evidence |
| `raw/` | Unprocessed captures (never edit, only add) |
| `tooling/` | Local scraping assets, how to run them |

## Ground rules

- Collection is read-only toward third parties: no posting, voting, or
  account actions. Rate-limit politely. Respect logged-in-session boundaries
  (X session belongs to Drew; use it only for reads).
- LinkedIn is auth-walled and bot-hostile: capture manually or via Drew's
  logged-in browser only when he initiates it; label those captures clearly.


========== END FILE: README.md ==========


---

========== BEGIN FILE: task_plan.md ==========

# Task Plan: RealPage knowledge base collection

## Goal
Fill the realpage KB with cited evidence (reviews, Reddit, news, site, social)
so future sessions can build things without asking questions.

## Next Step
1. **Awaiting Drew:** pick a direction from the five shapes in the brainstorm
   (see `progress.md` session 2026-09-10 + `findings.md` landscape check).
   Nothing is committed; the KB feeds all five.
2. Collection: Phase 2 (Reddit) is **done**. Unblocked next: Phase 3 DOJ
   primary docs (`raw/legal/`, justice.gov is open) and Phase 4 site crawl
   (`raw/site/`). Phase 1 remainder — G2/Capterra/TrustRadius — still needs the
   Browser Use pass; app stores + Glassdoor after that.

## Current Phase
Phase 1 — Third-party reviews (in_progress)

## Collection spec (source inventory)

| Source | Tool | Output | Status |
|---|---|---|---|
| Software Advice | Crawl4AI ✅ | `raw/reviews/software-advice-realpage-2026-09-10.md` | **captured** |
| Capterra | WebSearch (direct blocked) | `raw/reviews/capterra-search-summary-2026-09-10.md` | indirect only |
| G2 (OneSite + suite) | Browser Use (DataDome blocks headless) | `raw/reviews/g2-*.md` | **blocked** |
| TrustRadius | Browser Use (Cloudflare blocks headless) | `raw/reviews/trustradius-*.md` | **blocked** |
| App Store — resident apps | Apple RSS reviews JSON (`itunes.apple.com/.../customerreviews`) | `raw/reviews/appstore-*.md` | pending |
| Google Play — resident apps | Crawl4AI | `raw/reviews/gplay-*.md` | pending |
| Glassdoor / Indeed | WebSearch → manual capture fallback | `raw/reviews/glassdoor-*.md` | pending |
| BBB | Crawl4AI | `raw/reviews/bbb-*.md` | pending |
| Reddit | ✅ `tooling/reddit_search.py` (DSH cookie) | `raw/reddit/` (25 JSON) + `04-reddit/index.md` | **complete** |
| X | twitter-news session | `raw/x/` → `05-social/x/` | pending |
| realpage.com | Crawl4AI (proven working on open sites) | `raw/site/` → `02-products/` | pending |
| DOJ / legal | WebFetch (justice.gov is open) | `raw/legal/` | pending |
| LinkedIn | manual, Drew-initiated | `05-social/` | pending |

## Capture ladder for blocked sites

1. WebFetch (cheapest, works on open sites)
2. Crawl4AI + stealth (proven: Software Advice; use for realpage.com, Play, BBB)
3. **Browser Use with real profile** — reserved for Cloudflare/DataDome sites (G2, Capterra, TrustRadius)
4. WebSearch summary → labeled medium confidence, never quoted externally as fact

## Organization schema

- Raw captures: `raw/<topic>/<source>-<slug>-<date>.md`, each opening with
  `Source: / Fetched: / Method: / Confidence:` (per repo README)
- Distilled files in numbered folders; they link the raw file and keep exact
  quotes in blockquotes with reviewer attribution (role, size, date, stars)
- Phase ends with its index file updated (`03-reviews/index.md`, `04-reddit/index.md`, ...)
- One topic per file; snapshot prefix only when multiple captures of the same source exist

## Phases

### Phase 1: Third-party reviews
- [x] Software Advice captured (130-review page)
- [x] Capterra indirect summary (labeled medium)
- [ ] G2, Capterra, TrustRadius — Browser Use pass
- [ ] App stores (resident apps)
- [ ] Glassdoor / Indeed
- [ ] Distill into `03-reviews/index.md`
- **Status:** in_progress

### Phase 2: Reddit evidence packs — COMPLETE
- [x] Tool unblocked + verified (`tooling/reddit_search.py` + DSH cookie)
- [x] Full sweep: 25 queries, 142 unique posts, 25 subreddits → `raw/reddit/` (25 JSON)
- [x] Distilled pack: `04-reddit/index.md` (themes, verbatim quotes, links, sweep notes)
- **Status:** complete (2026-09-10). Deeper sweeps possible later — add queries
  as new angles appear; respect the 100-request/3-min rate limit (pack §4).

### Phase 3: DOJ antitrust primary docs
- [ ] Complaint + proposed final judgment → `raw/legal/`
- [ ] Confirm dates in `06-news/doj-antitrust-timeline.md`
- **Status:** pending

### Phase 4: realpage.com crawl
- [ ] Products, pricing, case studies → `raw/site/` → `02-products/`
- **Status:** pending

### Phase 5: Competitor stubs
- [ ] Yardi, AppFolio, Entrata, Buildium, MRI → `07-competitors/`
- **Status:** pending

### Phase 6: Social
- [ ] X pass via twitter-news session → `05-social/x/`
- [ ] LinkedIn capture (Drew-initiated only) → `05-social/`
- **Status:** pending

### Phase 7: Synthesize
- [ ] Voice-of-customer themes, exact phrases → `08-voice-of-customer/`
- [ ] Rank build ideas against evidence → `09-build-ideas/`
- **Status:** pending

## Key Questions
1. Does G2's DataDome yield to Browser Use with the real profile? (test first in Phase 1 block)
2. Which build direction does Drew want (compete / sell around / content / intel)?
3. Is the X session (`~/.local/share/twitter-news/x-session.sqlite`) still valid? Test before Phase 6.

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Collect all evidence before ranking build ideas | One evidence base serves all five directions |
| Verbatim quotes only in raw/; paraphrase in analysis | Preserves voice-of-customer value |
| Crawl4AI primary, Browser Use reserved for protected sites | Cheap→expensive ladder; headless proven on open sites |
| Reddit sweeps: ≤8 posts / 2 comments, ~20s gaps | Observed 100-request/3-min limit; bursts return HTTP 429 |
| Search summaries labeled medium, never quoted externally | Accuracy discipline |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| Reddit JSON blocked for unauthenticated curl | 1 | **Solved 2026-09-10:** `tooling/reddit_search.py` + DSH session cookie (curl/UA alone stays 403) |
| WebFetch G2 → HTTP 403 | 1 | Browser Use pass queued |
| WebFetch TrustRadius → 404 (wrong slug) | 1 | Correct slug: realpage-leaselabs |
| Crawl4AI G2 → DataDome captcha, HTTP 403 | 2 | Browser Use pass queued |
| Crawl4AI TrustRadius → Cloudflare JS challenge, HTTP 307 | 2 | Browser Use pass queued |
| Crawl4AI Capterra → bot security page (no content) | 2 | Browser Use pass queued |
| Software Advice via WebFetch → extractor empty | 1 | Solved: Crawl4AI captured it fully |


========== END FILE: task_plan.md ==========


---

========== BEGIN FILE: findings.md ==========

# Findings & Decisions — RealPage KB

Companion to `task_plan.md`. Raw evidence lives in `raw/`; this file distills it.

## Requirements
- Data-rich, organized KB so future sessions build without asking questions (Drew, 2026-09-10)
- Raw evidence verbatim; exact quotes preserved, never paraphrased in raw captures
- Public repo connected (`github.com/Pu11en/realpage`); push only when Drew says
- Every `.md` written by an agent session gets displayed in the session (Rule 8)

## Research Findings

### Review landscape (Phase 1, partial)
- **Customer support is the #1 recurring complaint** on both platforms captured:
  long holds (45+ min per Capterra summary), slow email, "little human interaction"
  — yet praise exists too ("customer service was great"), so it varies by account
- **Value for money is the lowest score on both** (3.7/5 on each) — cost, paid
  training ($150/hr), billing complaints
- **Pricing accuracy complaints** (wrong square footage, prices "skyrocketing")
  mirror the DOJ algorithmic-pricing story from the customer's side
- **Ease of learning is the top praise** (71% positive) — tension: easy basics,
  hard advanced workflows (renewals, portals, month-end close, search)
- **Task completion pain**: multiple sites/accounts for daily work; can't undo
  month-end close; inadequate search
- **Compliance department** criticized for not knowing affordable-housing law —
  appears independently on two platforms
- **Segment stretch**: page says "ideal for 2–10 employees" while reviews span
  1001–5000-employee firms; multifamily + student + HOA + commercial + senior
- **Integrity caveat**: 1 of 8 sampled reviews was about an unrelated product
  (rail forums) — review platforms carry contamination; never cite a single review

### Source access findings
- G2 = DataDome (hardest block); Capterra + TrustRadius = Cloudflare challenges
  → all three need a real browser session (Browser Use)
- Software Advice crawls cleanly headless; its data references Capterra CDN
  profile images — Gartner Digital Markets properties share review pools
- Reddit JSON API rejects unauthenticated curl → DSH reddit session is the route

### Company / legal (seeds, medium confidence)
- Thoma Bravo take-private Dec 2020 (~$10.2B); 24M+ units claimed
- DOJ pricing-algorithm settlement: proposed Nov 2025, entered Mar 2026;
  separate class action; NY algorithmic-pricing ban fight ongoing
- Products: AI Revenue Management (ex-YieldStar), Lumina AI Suite, OneSite,
  property management platform, marketing/reputation tools

### Landscape check — audience & builder market (2026-09-10)
- **The story is live and compounding, not a 2022 artifact.** DOJ settlement
  still in Tunney Act review with four state AGs objecting; landlord class
  settlements $141.8M (27 firms, Nov 2025) + $218M (11 landlords, May 2026);
  algorithmic-pricing bans in NY/CA/CT/NJ plus SF/Philly/Minneapolis/Seattle;
  first local enforcement in Providence (a 44% renewal hike case); 21+ states
  with restrictions; End Rent Fixing Act reintroduced; Ninth Circuit
  algorithmic-pricing precedent pending.
- **Migration wave happening now:** settling landlords agreed to purge
  nonpublic data and stop using the pricing software — active displacement
  from RealPage in the market today.
- **Builder market gap:** 50–500 unit operators are underserved as incumbents
  drift upmarket; ~120K potential customers; est. $380M/yr across five gaps;
  indie playbook = pick ONE workflow + integrate via APIs (not full-stack
  replacement); GTM via NARPM chapters, 20K-member Facebook groups, conferences.
- **Uncovered workflows named in the market:** cross-entity owner reporting,
  capital project tracking, vendor/COI management, affordable-housing compliance.
- **UX complaints reconfirmed:** Yardi Voyager "dated, cluttered... assumes
  formal training"; OneSite "outdated core interface," slowness; opaque
  enterprise pricing at both.
- Sources: saasopportunities.com (builder market math), kelpic.com (RealPage
  vs Yardi), splitpay.com (market overview), ProPublica-origin coverage.

### Reddit sweep — themes (2026-09-10, 142 posts / 25 subreddits)
- **Public/antitrust sentiment: hostile with mass engagement.** 15.5k-pt DOJ
  thread ("RealPage needs to go"), 12.3k-pt DC AG thread, 9.9k DOJ-investigation,
  8.5k ProPublica/YieldStar ("It's a feedback loop"), 6.8k White House $3.8B.
  Private-equity anger is the dominant frame. Viral framing persists into 2026
  (r/antiwork 2,785 pts "the real reason our rent is so high…an AI algorithm").
  Local politics produce heroes (NC AG threads 1.7k/1.5k pts).
- **Renter pain is concrete:** online payment fees ($30/mo in one thread, $36/yr
  another → check/mail workarounds), billing overcharges vs physical submeters,
  renewal anxiety, login/auth friction, and recourse-seeking (lawsuit sign-ups,
  deposits). Organizing impulses exist but low engagement ("publish the
  YieldStar client list", "Reverse Realpage app").
- **PM pain is operational and specific:** OneSite is the most-hated surface
  ("I hate Onesite with every fiber of my being"; "sucks donkey balls");
  screening errors need manual overrides routinely; report-scheduler failures;
  disputes ghosted after ~3 weeks; support tickets the only path.
- **Migration intent is live:** "we are making the switch to Entrata once our
  contract with Real Page ends." Leavers go to **Yardi, Entrata, AppFolio**
  (counter-signals: Entrata has its own support complaints; AppFolio "garbage
  for section 8 compliance"; MRI "still haven't fixed the renewal rate
  adjustment button").
- **Exit friction (structural):** "When you build a business, along with the
  processes/systems for running it, around a platform, it's difficult to leave
  that platform." — the strongest argument for migration-tooling/point solutions.
- **CRE professionals:** override friction — "so difficult to over ride their
  algorithm's suggestions (on a daily basis) they might have had more of a
  legitimate argument"; "no way they could tweak it to satisfy DOJ's concerns."
- **Unverified insider anecdote** (1,077 pts): "They literally preached to
  employees how our software figured out that it's more profitable to run higher
  rents while having vacan[cy]" — treat as anecdote, not fact.
- Details, links, and full quotes: `04-reddit/index.md` + `raw/reddit/*.json`.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Crawl4AI primary; Browser Use only for protected sites | Cheap→expensive ladder |
| Search summaries labeled `medium` and never quoted externally | Accuracy discipline |
| Raw captures keep page-reported figures labeled as such | Separates vendor claims from verified data |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| G2/Capterra/TrustRadius block headless crawlers | Browser Use pass queued (Phase 1) |
| Reddit JSON unauthenticated block | DSH reddit session cookie (Phase 2) |

## Resources
- `tooling/LOCAL-ASSETS.md` — all local scraping assets + how to run them
- Crawl script: `/tmp/crawl_reviews.py` (reusable; edit URLS dict); outputs to `/tmp/crawl_out/`
- Capterra RealPage id: 183247 · TrustRadius RealPage slug: realpage-leaselabs
- justice.gov settlement PR (URL in `06-news/doj-antitrust-timeline.md`)

## Visual/Browser Findings
- (none captured yet; review-site screenshots not needed — text captures sufficient)


========== END FILE: findings.md ==========


---

========== BEGIN FILE: progress.md ==========

# Progress Log

Companion to `task_plan.md`. Newest session first.

## Session: 2026-09-10 (resume pack for no-access runtime)

- A context-free session on a sandboxed runtime reported it could not reach the
  repo (no disk mount, no GitHub/raw, clone rejected by credit limit) and asked
  for HANDOFF, task_plan, findings, and the Reddit pack.
- Built `RESUME-PACK.md` — the six "read first" files verbatim in one
  paste-ready bundle, with a receiver header that includes how to trigger the
  brainstorm session.
- Copied the pack + `raw/reddit/*.json` to Windows-reachable drops
  (`C:\Users\Public\realpage-*`) so Windows-side sandboxes can pick them up.
- Files created: `RESUME-PACK.md`
- Files modified: `HANDOFF.md` (pack pointer), `progress.md` (this entry)

## Session: 2026-09-10 (reddit full sweep — Phase 2 complete)

- Ran 25 queries across PM / landlord / renter / legal / news-reaction subs;
  **142 unique posts**, 25 subreddits, 2020–2026 → 25 raw JSON in `raw/reddit/`
- Hit Reddit's rate limit mid-sweep (100 requests / ~3 min, HTTP 429) →
  waited for reset and resumed with pacing; safe cadence logged in the pack
- Wrote consolidated pack `04-reddit/index.md`; deleted the superseded
  first-pull digest (folded in, recoverable via git history)
- `r/LeasingConsultants` doesn't exist (302) → used `r/LeasingAgents`
- Files created: `04-reddit/index.md` + 21 new `raw/reddit/*.json`
- Files modified: `task_plan.md` (Phase 2 complete), `findings.md` (Reddit themes)
- **Phase 2: COMPLETE.** Ready to push.

## Session: 2026-09-10 (reddit unblocked)

- Located the DSH credential store: `~/.dsh/.credentials.yaml` →
  `refs.REDDIT_SESSION_COOKIE` (the saved session the reddit plugin uses)
- Built `tooling/reddit_search.py` — standalone replica of the DSH plugin's
  read-only search: same endpoints/bounds, cookie read at runtime from the
  DSH file, never printed or written by the script
- Verified: unauthenticated curl (even with browser UA) = HTTP 403 block page;
  with the saved session = full JSON results
- First evidence pull, 4 queries / 36 posts: `raw/reddit/` (4 JSON + evidence MD)
- Files created: `tooling/reddit_search.py`, `raw/reddit/*`
- Files modified: `tooling/LOCAL-ASSETS.md` (reddit section rewritten),
  `task_plan.md` (Phase 2 in progress, error row resolved)

## Session: 2026-09-10 (brainstorm — destination discovery)

- Context: Drew asked how to build a plan well. The four-question form was
  rejected — he wants material to react to, not a questionnaire. Brainstorm
  conversation is live and unfinished.
- Actions taken:
  - Landscape research: media/audience signal, builder market, community signal
  - Added "Landscape check" section to `findings.md`
  - Presented five concrete shapes for gut-check: RealPage Files (public
    evidence library) · investigation/content series · empty-seat tool
    (50–500 units) · lifeboat lane (migration wave) · renter-side watch
- Awaiting: Drew's direction choice (Key Question 2). None of the five is
  committed; the KB serves all five regardless.
- Next agent: ask Drew which shape he leaned toward (or which he recoiled
  from), then either run the Browser Use pass for blocked review sites or
  shift collection toward the chosen direction.

## Session: 2026-09-10 (collection kickoff)

### Phase 1: Third-party reviews — in_progress

- **Started:** 2026-09-10 ~01:30
- Actions taken:
  - WebFetch attempts: G2 (403), Software Advice (empty extraction), TrustRadius (404 wrong slug)
  - Verified local crawl stack (crawl4ai 0.8.6, Playwright chromium present)
  - Ran `/tmp/crawl_reviews.py` against 4 review URLs
  - Found correct URLs: Capterra id 183247 · TrustRadius slug realpage-leaselabs
- Files created:
  - `raw/reviews/software-advice-realpage-2026-09-10.md` (full capture)
  - `raw/reviews/capterra-search-summary-2026-09-10.md` (indirect, medium)
  - `task_plan.md` · `findings.md` · `progress.md` (planning trio)
- Files modified:
  - `03-reviews/index.md` (captured-so-far section)
  - `00-BACKLOG.md` (pointer to task_plan.md)

## Test Results

| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| crawl4ai import | `python3 -c import crawl4ai` | import | v0.8.6 | pass |
| Playwright browsers | `ls ~/.cache/ms-playwright` | chromium | chromium-1234 | pass |
| WebFetch G2 | g2.com OneSite reviews | review text | HTTP 403 | fail |
| WebFetch Software Advice | profile page | review text | empty extraction | fail |
| crawl4ai Software Advice | same URL | capture | 46KB markdown | **pass** |
| crawl4ai G2 | same URL | capture | DataDome captcha 403 | fail |
| crawl4ai Capterra | /p/183247/Real-Page/reviews/ | capture | bot security page | fail |
| crawl4ai TrustRadius | realpage-leaselabs/reviews | capture | Cloudflare 307 | fail |

## Error Log

| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| ~01:40 | G2 blocked (DataDome) | 1–2 | Browser Use pass queued |
| ~01:40 | TrustRadius blocked (Cloudflare) | 1–2 | Browser Use pass queued |
| ~01:40 | Capterra blocked (bot wall) | 1–2 | Browser Use pass queued |
| earlier | Reddit JSON unauth block | 1 | DSH session cookie (Phase 2) |

## 5-Question Reboot Check

| Question | Answer |
|----------|--------|
| Where am I? | Phase 1, 2 of ~6 review sources captured |
| Where am I going? | Browser Use (G2/Capterra/TrustRadius) → app stores → Glassdoor → distill |
| What's the goal? | Cited-evidence KB so future sessions can build without asking questions |
| What have I learned? | Support is the #1 complaint; blocked-site capture ladder established (findings.md) |
| What have I done? | See Actions above; 2 raw captures + planning trio written |


========== END FILE: progress.md ==========


---

========== BEGIN FILE: 04-reddit/index.md ==========

# Reddit evidence pack — RealPage

Source: reddit.com via `tooling/reddit_search.py` (saved DSH session cookie)
Fetched: 2026-09-10
Method: 25 bounded queries (GET `/search.json` + thread `.json`, sort=top,
  depth=1; max 10 posts / 5 comments per query). Raw JSON: 25 files in
  `../raw/reddit/2026-09-10-*.json`. 142 unique posts, 2020–2026, 25 subreddits.
Confidence: high for quoted text; votes measure engagement, not truth. This
  supersedes the earlier first-pull digest (its content is folded in here).

## 1. Public / antitrust sentiment — hostile, massive engagement

- **r/technology [2024-08] "U.S. Justice Department sues software firm
  RealPage…" — 15,549 pts, 515 comments**
  > "I hope they get the book thrown at them. RealPage needs to go." (1,793)
  > "RealPage, which is owned by the private-equity firm Thoma Bravo … Boy,
  > private equity firms really love fucking consumers from both ends" (765)
- **r/technology [2023-10] "The rent is too damn algorithmic — DC AG
  investigating RealPage" — 12,316 pts, 535 comments**
  > "The guy who built this software to do apartment rental price fixing is the
  > same guy who was busted for building software for price…" (1,515)
  > "It's a bunch of landlords giving data to a company which tells them how
  > much rent they should charge. That's a very textbook examp[le]" (1,007)
- **r/Futurology [2022-10] ProPublica "Rent Going Up? One Company's Algorithm
  Could Be Why" — 8,518 pts**
  > "It's a feedback loop. A few landlords raise the rent. This raises the
  > average rent in that market. This triggers the algorithm to…" (1,456)
- **r/technology [2024-12] White House: RealPage added billions to rents — 6,798 pts**
  > "So its basically corporate collusion software" (1,817)
- **r/Economics [2024-12] "$3.8 Billion" — 6,709 pts** ·
  **r/technology [2022-11] DOJ investigating — 9,880 pts** ·
  **r/technology [2024-06] FBI raids Cortland — 9,140 + 4,569 pts**
- **r/technology [2024-08] "RealPage lawyer denies collusion" — 2,428 pts**
  > "They literally preached to employees how our software figured out that
  > it's more profitable to run higher rents while having vacan[cy]" (1,077)
  — insider claim, **unverified**; quoted for voice-of-customer, not as fact.
- **r/antiwork [2026-07] "Found out the real reason our rent is so high. It's
  literally an AI algorithm." — 2,785 pts** (current, viral framing persists)
- **State/local political energy:** NC AG Jeff Jackson's rent-pricing suit
  announcement — r/Charlotte 1,742 pts, r/raleigh 1,490 pts ("Somebody clone
  this man"); Colorado HB24-1057 ban bill — r/Denver 805 pts; NY statewide ban
  — r/technology 1,964 pts ("It's collusion."); AZ AG suit, $141M Greystar
  settlement (r/Apartmentliving, r/PropertyManagement).
  > "$141 million settlement" → "I look forward to my cheque for $52.85 for the
  > injury of being overcharged thousands of dollars in rent over the past 7
  > years" (6)

## 2. Renters' lived pain — payments, renewals, billing, opacity

- **Payment friction & fees:** r/mildlyinfuriating "$36 a year to pay rent
  electronically…. Why…." — 3,566 pts
  > "…paying online is $30, that's per month… I'm sure no one uses it" (830)
  > "For 1 whole year I wrote a personal check and mailed it out to pay rent to
  > protest this very thing." (434)
  r/Apartmentliving "Resident eMoney Order to pay my rent" → workaround advice:
  > "go to your bank and see if you can get a checkbook for free and write
  > checks every month. no fee" (3)
- **Billing/overcharge disputes:** r/legaladvice [2026-09] "Landlord/RealPage
  overcharging for water despite physical submeter proving otherwise";
  r/PropertyManagement [2026-07] "Realpage Dispute"
  > "Took about 3 weeks for mine, came back partially adjusted and then they
  > just ghosted" (1)
- **Renewal anxiety:** r/Apartmentliving [2026-02] "Is it normal for my renewal
  rate to not go down with the current rates?" (9 pts, 17 comments)
- **Login/auth friction:** "Loft Living prompts for an authentication code but
  I never set one up?" (same issue reported by another user)
- **Recourse-seeking:** r/legaladvice questions on joining the RealPage
  lawsuit, deposits, "Landlord scams, liability, & RealPage".
- **Organizing impulses (low engagement, high intent):**
  r/renters "Publish the RealPage YieldStar client list! Expose landlords for
  price fixing & connect tenants"; "Ask your Landlord about their use of
  RealPage" (59 pts) → "Ask your local media to cover this so folks can get
  their refunds!" (21); "Reverse Realpage app" (user wanting a counter-tool).
- Adjacent (NOT RealPage-specific, flagged): r/Apartmentliving "can we withhold
  rent if this is not fixed?" — 11,881 pts, 1,966 comments (habitability, the
  biggest renter-side thread found); r/mildlyinfuriating eviction/escrow thread
  — 9,014 pts.

## 3. Property-management side — operational reality

- **OneSite is the most-hated surface:**
  > "I hate Onesite with every fiber of my being. I liked classic but new
  > experience sucks donkey balls." (2026-07, 2 pts)
  > "just thinking of OneSite is making my skin crawl lol" (2022)
  > "The new experience sucks donkey balls… Trying to generate renewals 4
  > months ahead of time" (2025-03)
- **Migration intent, live:** "Will OneSite ever be fixed, or should we ditch
  it for something new?" (2025-03)
  > "we are making the switch to Entrata once our contract with Real Page ends."
  > "Whatever you do, don't switch to MRI, haha. It's been over a year and they
  > still haven't fixed the renewal rate adjustment button."
- **Where leavers go:** "usually when someone leaves realpage, they move to
  yardi, onesite or appfolio" (2025-12)
  Entrata: "Reporting and financials are a breeze. Customer support is top
  notch and you'll always get someone on the phone quickly" / "Entrata is just
  so much more effective at everything" / "I love Entrata."
  AppFolio: "much user friendly and top on the hill" — counter: "AppFolio is
  garbage for section 8 compliance so beware if that's part of your portfolio."
- **Screening errors are routine:** "I work with real page and sometimes it has
  a lot of errors that require overrides which is most likely what happened"
  (2026-06); "My company uses one site and this happens all the time. As long
  as you have the rights, you should be able to manually edit the income"
- **Support/ops friction:** report scheduler failures ("Support g[hosted us]"),
  disputes ghosted, "you'll have to submit a ticket with Real Page", training
  via "RealPage Product Learning Portal".
- **Exit friction — the key structural quote:**
  > "When you build a business, along with the processes/systems for running it,
  > around a platform, it's difficult to leave that platform." (r/PropertyManagement)
- **CRE / institutional view:** "In RealPage We Antitrust" (38 pts, 48 comments)
  > "Honestly, if they hadn't made it so difficult to over ride their
  > algorithm's suggestions (on a daily basis) they might have had more of a
  > legitimate argument" (15)
  > "There's no way they could tweak it to satisfy DOJ's concerns…" (12)
  "Our biggest equity investor uses RealPage for Asset management, but I hate it."
- **Pricing signal:** "Appfolio… you pay per unit… less than $2 per unit" (2023);
  RealPage pricing unpublished in these threads.
- **Industry mood:** property-manager burnout threads (12 pts, 25 comments):
  "You are ONE person working the job of three+ people."

## 4. Operational notes for future sweeps

- Tool caps: 10 posts / 5 comments per query. Reddit rate limit observed:
  **100 requests / ~3 min** — pace sweeps at ≤8 posts with 2 comments and
  ~20s between queries, or wait for reset (`x-ratelimit-reset`, seconds).
- `r/LeasingConsultants` does not exist (HTTP 302) — use `r/LeasingAgents`.
- Weak-signal subs for this topic: r/HOA (only tangential fee grumbles),
  r/CommercialRealEstate (thin but one good thread), r/legaladvice (few posts,
  mostly individual disputes).
- Strongest subs: r/PropertyManagement (operational), r/technology +
  r/Economics (antitrust), r/Apartmentliving + r/Renters (renter side).
- Caveats: bounded sample; votes = engagement not proof; adjacent threads
  labeled; single comments are noise, patterns are signal.


========== END FILE: 04-reddit/index.md ==========
