# Task Plan: RealPage knowledge base collection

## Goal
Fill the realpage KB with cited evidence (reviews, Reddit, news, site, social)
so future sessions can build things without asking questions.

## Next Step
1. **Awaiting Drew:** pick a direction from the five shapes in the brainstorm
   (see `progress.md` session 2026-09-10 + `findings.md` landscape check).
   Nothing is committed; the KB feeds all five.
2. Collection continues either way: one Browser Use pass (real Chromium) at
   G2, Capterra, TrustRadius → `raw/reviews/`; then app stores + Glassdoor.

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
| Reddit | DSH reddit session cookie; fallback browser-UA JSON | `raw/reddit/` → `04-reddit/` | pending |
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

### Phase 2: Reddit evidence packs
- [ ] Queries: r/PropertyManagement, r/Landlord, r/renters, r/LeasingConsultants
- [ ] Switching stories, support complaints, pricing chatter → `04-reddit/`
- **Status:** pending

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
| Search summaries labeled medium, never quoted externally | Accuracy discipline |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| Reddit JSON blocked for unauthenticated curl | 1 | Use DSH reddit session (Phase 2) |
| WebFetch G2 → HTTP 403 | 1 | Browser Use pass queued |
| WebFetch TrustRadius → 404 (wrong slug) | 1 | Correct slug: realpage-leaselabs |
| Crawl4AI G2 → DataDome captcha, HTTP 403 | 2 | Browser Use pass queued |
| Crawl4AI TrustRadius → Cloudflare JS challenge, HTTP 307 | 2 | Browser Use pass queued |
| Crawl4AI Capterra → bot security page (no content) | 2 | Browser Use pass queued |
| Software Advice via WebFetch → extractor empty | 1 | Solved: Crawl4AI captured it fully |
