# Findings & Decisions — RealPage KB

Companion to `task_plan.md`. Raw evidence lives in `raw/`; this file distills it.

## Requirements
- **Outside-in only:** no RealPage insiders, product access, or data; public sources only (Drew, 2026-09-10)
- **Goal:** a finished, viable MVP that RealPage (or a business like theirs) would use; prove from outside they lack it; pitch it
- Planning is done with the expensive model; plans must be executable by a cheaper model
- Work locally; push to GitHub only when Drew says
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

### Direction re-score (planning session 2026-09-10)
- Of the five old directions, only the evidence library survives (folded into
  the pitch as a door-opener); the other four are hostile to or compete with
  the buyer.
- Recommended **C1 PMS Switch Radar**: apartment websites link to their
  resident portal / pay-rent / apply flow, which (hypothesis) reveals the PMS
  vendor; the Wayback Machine dates switches. RealPage already knows its own
  churn, so its value is the view of non-customers, where leavers went, and
  share shifts after bans/settlements.
- Biggest unknown: RealPage (market analytics) or Yardi Matrix may already own
  property-level PMS data → research run R1 is a kill gate.
- Fallback **C3** affordable-housing compliance copilot, grounded in public HUD
  4350.3 / Section 42 rules; need rests on ~2 quotes.
- Parked for failing outside-in: OneSite support copilot (docs gated), resident
  bill explainer, screening/month-end helpers (need their data).
- Full scoring: `09-build-ideas/brainstorm-2026-09-10-pitch-to-realpage.md`.

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
