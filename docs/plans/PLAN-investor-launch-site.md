# Plan: site ready for investors from Reddit (2026-09-18)
Goal: A Reddit investor can click "Start free" on the landing page and land in the site without logging in, then see only investor-facing content: the chat open on every page with a free-account prompt, nothing about RealPage, and no thin New York data.
Done when: `bash tooling/check-no-realpage-target.sh` exits 0, and signed out, the landing page's "Start free" link and each of the Map, Early Leads and Under the Hood pages return 200 with content and no RealPage text, with New York absent from the area picker.

Audience: r/CommercialRealEstate + r/realestateinvesting. No new data, no new features beyond the chat change.
Decisions (Drew, 2026-09-18): all data open, no login; chat panel open by default on every page, closable (X);
inside the chat a big "Make a free account" button + small "Already have one? Sign in"; signed-in users remembered.

Check: bash tooling/check-no-realpage-target.sh
Try: bash tooling/dev.sh
Open: http://localhost:8765

## Tasks
- [x] T1 Clear the 52 leftover hits of tooling/check-no-realpage-target.sh (all in business/): move RealPage-pitch notes to archive/realpage/business, reword the rest; check must exit 0.
- [ ] T2 Landing page (business/marketing/landing/index.html): rewrite for investors. Headline "See which apartment buildings just sold, who bought them, and what's being built." Primary button "Start free" links straight to the site (no login). Keep the design; update its test in business/tools/test_landing.py.
- [ ] T3 Remove any login gate in front of the site pages (Caddy/proxy/Google sign-in) so Map, Early Leads, building pages and Under the Hood load signed out. Test: curl each page signed out returns 200 with content.
- [ ] T4 Chat panel on every site page: open by default, X closes it (remember closed state per visit). Signed out, it shows "Make a free account" (primary) and "Already have one? Sign in" (small link) using the existing sign-in; signed in, it shows the existing chat.
- [ ] T5 Hide New York (2 leads) from the area picker and map until it has real data (data/areas/index.json flag, not deletion).
- [ ] T6 Map headline: neutral ("Apartment activity by state"); lead cards: move "software not picked yet" below sale/buyer/opening info.
- [ ] T7 Chat agent knowledge (SOUL.md): describe CraneSignal as sales, buyers and new builds for investors; no RealPage-as-customer talk. Ask 5 investor questions locally; answers cite data.
- [ ] T8 Final local walk-through: landing → Start free → Early Leads → a building → chat sign-up prompt. Screenshot each for Drew. Nothing pushed.

## How to try it
1. Open the landing page: it talks about sales and buyers, and "Start free" drops you into the site with no login.
2. Every page has the chat open; the X closes it; it asks you to make a free account.
3. Menu shows only Map, Early Leads, Under the Hood; no RealPage anywhere; New York is gone.
