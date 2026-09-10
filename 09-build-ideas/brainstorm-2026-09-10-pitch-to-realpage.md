# Brainstorm 2 — build something RealPage would buy, from outside only

Source: Drew + planning session 2026-09-10 (thread 1547545532241809478)
Fetched: 2026-09-10
Method: re-scoring of all repo evidence against the corrected mission; no new research
Confidence: medium — every "they don't have it" claim below is a hypothesis until
  `research-run-01-verify.md` checks it

## 1. The corrected mission (supersedes the framing in brainstorm #1)

- **The constraint is "outside-in only."** We have zero access to RealPage: no
  insiders, no product login, no customer data, nobody to ask. Everything we
  know or build comes from public sources. (Earlier docs said "without asking
  Drew" — wrong. Drew is the decision-maker; RealPage is who we can't ask.)
- **The goal is a finished MVP we pitch to RealPage** — or, as fallback, a
  business like theirs (Yardi, Entrata, AppFolio, ResMan, MRI).
- **"MVP" means minimal *and* viable:** it works on real data, a specific person
  at the buyer would use it, and we can show from public evidence that they
  don't already have it (or would clearly benefit).
- **Planning is the expensive step; building is cheap.** Plans must be concrete
  enough that a cheaper model can execute them without judgment calls.

## 2. What that does to the five old directions

| Old direction | Pitchable to RealPage? | Verdict |
|---|---|---|
| 1. Public evidence library ("RealPage Files") | Only if reframed as private intel *for* them | **Folded** into C2 below as the pitch's door-opener |
| 2. Investigation / content series | No — it's against them | **Killed** |
| 3. Tool for 50–500-unit managers | No — competes with them | **Killed** for this pitch (valid for another buyer) |
| 4. Migration / switch tooling | No — helps customers leave them | **Killed** as a tool; the *signal* survives in C1 |
| 5. Renter-side watch | No — hostile | **Killed** |

## 3. Scoring criteria (the filter every idea must pass)

1. **Outside-in buildable** — delivers value with public inputs only (hard gate)
2. **Named buyer** — a specific role at RealPage owns this pain and has budget
3. **Absence provable** — we can show from outside that they lack it
4. **MVP-doable** — solo builder + cheap models, ~2 weeks after research
5. **Demo on real data** — the pitch shows *their* world, not a mockup
6. **Not hostile** — reads as help, not a threat
7. **Low legal/ToS risk**
8. **Fallback buyers** exist if RealPage says no

## 4. Candidates (evidence → idea → score)

### C1. PMS Switch Radar — which property runs which software, and who switched ★ recommended
- **Evidence:** migration is live ("we are making the switch to Entrata once our
  contract with Real Page ends"; "usually when someone leaves realpage, they move
  to yardi, onesite or appfolio"); settling landlords agreed to stop using the
  pricing software (`findings.md` landscape check); exit friction is structural
  (`04-reddit/index.md` §3).
- **Idea:** every apartment community's public website links to its resident
  portal / apply / pay-rent flow, and those links reveal the vendor (hypothesis:
  RealPage → loftliving / onlineleasing.realpage.com / ActiveBuilding; Yardi →
  rentcafe; Entrata → residentportal; AppFolio → *.appfolio.com; Buildium →
  managebuilding.com). Crawl a metro, classify each community, and use the
  Wayback Machine to see *when* the links changed = dated switch events. Add the
  "why" layer from our voice-of-customer evidence.
- **Buyer at RealPage:** sales/strategy (competitor-installed properties to win),
  customer success (portfolios drifting away), market intelligence (share by metro).
- **Scores:** 1 ✅ public websites + archive · 2 ✅ · 3 ⚠ unknown — RealPage and
  Yardi both run market-data businesses; they may already track this (R1 decides)
  · 4 ✅ one metro · 5 ✅✅ strongest demo ("in Austin, N communities, X% yours,
  these 27 left you in 12 months, here's the evidence") · 6 ✅ market intel, not
  criticism · 7 ✅ polite crawl of public pages · 8 ✅✅ every PMS vendor plus
  PropTech vendors who need to know a property's PMS before selling integrations.

### C2. Public Voice-of-Customer Radar
- **Evidence:** support is the #1 complaint on every platform captured; OneSite
  is the most-hated surface; disputes "ghosted"; value-for-money lowest score.
- **Idea:** continuous monitor of public PM + resident talk about RealPage
  products (Reddit, review sites, app stores, BBB), tagged by product, workflow,
  severity, churn intent, competitor mentioned, and "did RealPage respond?"
- **Buyer:** VP customer experience / product.
- **Scores:** 1 ✅ (pipeline already works) · 2 ✅ · 3 ⚠ partial — vendor response
  rates on public reviews are measurable · 4 ✅ · 5 ✅ · 6 ⚠ can read as a
  complaint dossier · 7 ⚠ Reddit/review-site commercial-use terms · 8 ✅.
- **Weakness:** thin volume — RealPage-specific PM posts are few and low-vote; a
  weekly feed might have a handful of items. **Better as C1's "why" layer and the
  free door-opener in the pitch** than as the product.

### C3. Affordable-Housing Compliance Copilot (runner-up)
- **Evidence:** compliance dept "not well versed in actual property management
  laws and affordable housing" (Software Advice, two platforms per findings);
  "AppFolio is garbage for section 8 compliance."
- **Idea:** cited Q&A + income-certification checker grounded in public rules
  (HUD Handbook 4350.3, IRS Section 42 / LIHTC guidance).
- **Buyer:** RealPage affordable-compliance product/support lead.
- **Scores:** 1 ✅ regulations are public · 2 ✅ · 3 ⚠ unknown (R6) · 4 ⚠ accuracy
  bar is high, needs an expert-checked test set · 5 ⚠ demo on synthetic cases ·
  6 ✅ · 7 ⚠ liability for wrong compliance answers · 8 ✅ AppFolio/Yardi/operators.
- **Weakness:** the need rests on ~2 quotes; domain credibility is on us.

### Considered and parked (fail the outside-in gate or the hostility test)
- **Support copilot for OneSite staff** — the docs it would need sit behind
  RealPage's login (Product Learning Portal). Needs a partnership first.
- **Resident bill / charge explainer** — needs their billing data.
- **Screening-override assistant, month-end close helper** — need their data.
- **Algorithmic-pricing law tracker** — outside-in ✅, but RealPage's own counsel
  already tracks this daily and law firms publish free trackers; it also pokes
  the lawsuit. Better for operators than for RealPage.
- **Public-rent comp feed for post-settlement pricing** — plausible (the
  settlement pushes them toward public data) but they almost certainly scrape
  listings already and the topic is legally hot.

## 5. Recommendation

**Build C1 (PMS Switch Radar) for one metro, with C2 folded in as the "why"
layer and the free door-opener. Keep C3 as the fallback if the research run
kills C1.**

Why C1 wins: it's the only candidate where the outside-in constraint is the
point of the product rather than a handicap; it produces hard numbers instead
of anecdotes; it demos on real data from their own market; and if RealPage
passes, the same dataset sells to every competitor and PropTech vendor.

The single biggest risk is criterion 3 — RealPage or Yardi Matrix may already
own property-level PMS data. **Research run R1 checks this first, and it can
kill C1 in under an hour.**

## 6. Also decided this session

- **Pause open-ended collection.** G2/Capterra browser pass, app stores, X,
  LinkedIn, and competitor stubs run only if the chosen plan needs them.
  Collection now serves the plan, not the other way round.
- **Every plan passes `/mvp-plan-review`** (`.claude/skills/mvp-plan-review/`)
  before a build session starts.
