# Reddit — RealPage evidence capture (first pull)

Source: reddit.com via `tooling/reddit_search.py` (saved DSH session cookie)
Fetched: 2026-09-10
Method: GET `/search.json` + thread `.json` (sort=top, depth=1), bounded to
  10 posts / 3 comments per query. Raw JSON: `2026-09-10-*.json` (this folder)
Confidence: high for quoted text; low for representativeness (bounded sample,
  votes are engagement not proof)

Queries run: `realpage` in r/PropertyManagement (10) · r/Landlord (10) ·
r/renters (8) · global top (8).

## Public / national sentiment — hostile and high-engagement

- **[2024-08] r/technology, 15,549 pts, 515 comments** — "U.S. Justice
  Department sues software firm RealPage for allegedly helping landlords
  collude"
  > "I hope they get the book thrown at them. RealPage needs to go." (1,787 pts)
  > "RealPage, which is owned by the private-equity firm Thoma Bravo … Boy,
  > private equity firms really love fucking consumers from both ends, don't
  > they?" (767 pts)

- **[2024-12] r/technology, 6,797 pts** — "RealPage pricing software adds
  billions to rental costs, says White House"
  > "So its basically corporate collusion software" (1,819 pts)

- **[2024-12] r/Economics, 6,709 pts** — "The White House Estimates RealPage
  Software Caused U.S. Renters To Spend An Extra $3.8 Billion"
  > "$3.8 billion and the DOJ dropped the suit…" (1,217 pts)

- **[2022-11] r/technology, 9,872 pts** — "exactly what anti trust laws are for." (794 pts)
- **[2024-06] r/technology, 9,140 pts** — "FBI raids corporate landlord office"

- **[2022-10] r/mildlyinfuriating, 3,566 pts** — "$36 a year to pay rent
  electronically…. Why…." — payment-fee resentment outside the antitrust frame

## Property-management side — operational, not political

- **[2026-08] r/PropertyManagement — "RealPage Report Scheduler Issues"**
  > "Our property had the exact same thing start happening last Tuesday…
  > Support g[hosted us]" (2 pts)
- **[2026-07] "Realpage Dispute"**
  > "Took about 3 weeks for mine, came back partially adjusted and then they
  > just ghosted" (1 pt)
- **[2025-11] "Have you switched to Entrata or Realpage in the lst 6 months…"**
  > "Entrata! Reporting and financials are a breeze. Customer support is top
  > notch and you'll always get someone on the phone quickly" (1 pt)
  > "I really like Entrata, real page is okay" (1 pt)
- **[2024-11] "Realpage vs Appfolio" (33 comments)**
  > "RealPage is good, No doubt here. But Appfolio is much user friendly and
  > top on the hill. It will be hard for your team to migrate at first…" (5 pts)
- **[2025-04] "Potentially moving from RealPage to Entrata"**
  > "Entrata is just so much more effective at everything…" (2 pts)
- **[2025-11] "DoJ agrees to settle with RealPage…"**
  > "Disappointing to see them face no consequences for price fixing" (2 pts)
- **[2025-08] "America's Largest Landlord to Stop Using RealPage Rent-Setting
  Software, Makes Deal With DOJ"** (Greystar — migration wave, on the ground)

## Landlord / screening side

- Repeated renter questions about the **RealPage AI Score**:
  > "Realpage scores range from 1-1000. A low 800's is like an A- on a report
  > card." — "Closer to 1000 is best for a realpage score"
- **[2025-01] "US sues six of the biggest landlords over 'algorithmic pricing
  schemes'" (23 pts)** — skeptical counterpoint present:
  > "Why isn't it ok to price according to what the market will bear?"

## Renter side — organizing impulses, low engagement

- **[2025-09] r/renters: "Publish the RealPage YieldStar client list! Expose
  landlords for price fixing & connect tenants"**
- **[2024-06] "Ask your Landlord about their use of RealPage" (59 pts)**
  > "Ask your local media to cover this so folks can get their refunds!" (21 pts)
- **[2026-09] "Problems with RealPage payments [Louisiana]"** ·
  **[2026-08] "Realpage settlement (KY)"** — current renter-side threads
- **[2024-09] "Reverse Realpage app"** — a user literally asking for a counter-tool

## Analysis (not quotes)

- Public sentiment is **hostile and hugely engaged** (15.5k-pt thread) — the
  story has an audience, not just a legal docket.
- PM sentiment is **operational**: support responsiveness, report scheduling,
  dispute handling. Switching talk favors **Entrata and AppFolio**.
- **Screening opacity** (AI Score) is a recurring renter pain with no good
  public answer — matches "renter-side watch" as a real gap.
- Caveats: bounded sample; r/Landlord results partly off-topic (rent
  calculators, insurance); single comments are noise, patterns are signal.
