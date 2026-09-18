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
