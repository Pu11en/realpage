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
