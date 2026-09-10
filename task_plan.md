# Task Plan: RealPage — outside-in MVP to pitch

## Goal
Using only public information (no RealPage access of any kind), build a
finished, working MVP that RealPage — or a business like theirs — would
actually use, show from outside that they lack it, and pitch it.

## Next Step
1. **Drew:** confirm C1 PMS Switch Radar (recommended) and answer the open
   decisions in `09-build-ideas/mvp-plan-switch-radar.md` §8.
2. Run `09-build-ideas/research-run-01-verify.md` (R1 = kill gate).
3. Apply results → re-run `/mvp-plan-review` → build session.

## Current Phase
Phase P1 — Verify (research run 01), pending Drew's go

## Build-track phases (new, 2026-09-10)

### Phase P0: Direction + MVP plan — COMPLETE (pending Drew confirm)
- [x] Mission corrected: outside-in constraint; pitch target = RealPage
- [x] Old five directions re-scored; C1 recommended, C3 fallback
      (`09-build-ideas/brainstorm-2026-09-10-pitch-to-realpage.md`)
- [x] MVP plan drafted (`09-build-ideas/mvp-plan-switch-radar.md`)
- [x] Plan-review skill (`.claude/skills/mvp-plan-review/SKILL.md`); plan
      reviewed: GO WITH FIXES, fixes applied (`09-build-ideas/review-mvp-plan-switch-radar.md`)
- [ ] Drew confirms direction + open decisions

### Phase P1: Research run 01 — verify
- [ ] R1–R6 per `09-build-ideas/research-run-01-verify.md`
- **Status:** pending

### Phase P2: Build MVP (steps 1–10 of the plan)
- **Status:** blocked on P1

### Phase P3: Pitch
- **Status:** blocked on P2

## Collection phases (original — PAUSED 2026-09-10)

Open-ended collection is paused. Resume a phase below only when an active
plan needs it.

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
2. ~~Which build direction?~~ Answered 2026-09-10: build to pitch RealPage; C1 recommended, awaiting confirm.
4. Does anyone already sell property-level PMS data? (research run R1 — kill gate)
3. Is the X session (`~/.local/share/twitter-news/x-session.sqlite`) still valid? Test before Phase 6.

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Collect all evidence before ranking build ideas | One evidence base serves all five directions (superseded 2026-09-10: collection now serves the chosen plan) |
| Constraint is outside-in only; pitch target is RealPage (fallback: businesses like theirs) | Drew, 2026-09-10 — "without asking Drew" in old docs was a mishearing |
| Kill hostile/competing directions (investigation, renter watch, 50–500 tool, migration tooling) | Can't pitch something against the buyer |
| Recommend C1 PMS Switch Radar, one metro; C3 compliance copilot fallback | Only candidate where outside-in is the product's strength; real-data demo; many fallback buyers |
| Every plan passes `/mvp-plan-review` before build | Cheap-model builds need plans that are feasible and unambiguous |
| Work locally; push only when Drew says | Drew, 2026-09-10 |
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
