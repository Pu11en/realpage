# Handoff: plan the CraneSignal fixes from the Sep 15 audit

## Where things stand
- **Repo:** realpage. User-facing name is **CraneSignal**; PropertyStack is internal only (memory cranesignal-official-name). Chat model id stays `hermes-agent`, display name "CraneSignal Agent".
- **Local copy:** worktree `realpage/.worktrees/local-test` (branch local-test). Start with `bash tooling/dev.sh`. The site is http://localhost:8765 and the chat is :3000 (no sign-in locally).
- **Live:** app.cranesignal.com (site + chat behind Caddy, Railway project `propertystack`) and cranesignal.com (landing, service propertystack-landing).
- **Audit:** read-only, nothing changed or pushed. The full plain-English report card is `handoffs/2026-09-15-cranesignal-audit.md`. The live test user is already deleted.
- ⚠️ **Other work is going into local-test right now:** AI Visibility v2 and the Street Talk gowork build. Don't plan changes to `ai-visibility.html`, `street-talk.html`, `tooling/street-talk/` or the AI Visibility build scripts.
- **Your job:** write a fix plan the new way. One small task per fix (15–30 minutes each), `- [ ]` checkboxes, one `Check:` line, plus `Try:`, `Open:` and a "How to try it" section. Ask Drew one plain yes/no question per chunk. Ask whether to run it with /gowork or in a normal session. Nothing is built until he says "go work". GitHub is always last.

## 🔴 Broken (fix first)
1. **Live chat answers never show in the panel.**
   - The Railway service `propertystack-chat` has `CORS_ALLOW_ORIGIN=https://propertystack-production.up.railway.app` but `WEBUI_URL=https://app.cranesignal.com`.
   - The websocket from origin app.cranesignal.com gets **403**. With no origin, or the old origin, it gets 101.
   - The answer completes in the database, but it never streams to the panel.
   - **Fix:** add `https://app.cranesignal.com` to CORS_ALLOW_ORIGIN (Railway env, restarts the chat).
   - This is a live change: announce it in the lounge and get Drew's OK first. No push needed.
   - **To verify:** raw websocket upgrade to `wss://app.cranesignal.com/ws/socket.io/?EIO=4&transport=websocket` with `Origin: https://app.cranesignal.com` should return 101. Then do 1 real panel question (`/tmp/audit/ui_chat.py` shows how: seed a token and poll the frame).
2. **4 pages have no viewport meta tag.** They are `site/index.html`, `under-the-hood.html`, `property.html` and `ai-visibility.html` (the last one is v2's territory, so coordinate or leave it). `map.html` and `privacy.html` have the tag. On a real phone, Early Leads renders as a shrunken desktop page.
   - **Also:** `tooling/qa/sweep.py` phone runs use `is_mobile=False`, so they missed this. Add an `is_mobile=True` check.
3. **Chat says "PropertyStack lead ranking" in Sources.** It comes from the "Say it as" column in `chatbot/hermes-profile/skills/query-propertystack/SKILL.md` (the `leads` and `state_leads` rows). Rename it to something like "CraneSignal lead ranking". Also check `chatbot/hermes-profile/SOUL.md` and the plugin for the same label.

## 🟡 Confusing (plan as small tasks)
- **Chat counts vs the site.** Live said Texas 586 and DFW 278. Local now says 628, but DFW is still 278 (the site says 320).
  - Plano-Richardson's 42 live in the `leads` table, not `state_leads` (tx/chat-leads.csv has 586 rows).
  - Fix at the data level: include Plano-Richardson in the Texas/DFW count or in chat-leads, and add a check_answers question for "How many leads in Dallas–Fort Worth?" = 320.
- **"Which vendor runs the most buildings?"** answers "Yardi 66 of 204" without saying it's only Plano and Richardson. Fix in SOUL or the skill.
- **Deep dive prompt says "planned"** for under-construction buildings. The cause is `deepDivePrompt` in `site/js/chat-panel.js`, which treats every signalType "Upcoming" as planned. Pass the real stage instead.
- **Chat panel open on desktop hides the table's Software and Why columns.**
- **Stat boxes don't follow the Region pick** (`site/index.html` renderPage).
- **Empty search has no "nothing found" row.**
- **Only the 42 Plano rows open a property page**, because only they have a `propertyId`. Decide: remove the pointer affordance, or build a simple detail view.
- **Hardcoded "Last updated: Sep 10, 2026"** in `site/js/app.js` line 49. Also, the "Neutral" View-as dropdown is unexplained.
- **Under the Hood** shows "area: plano-richardson", "propertystack/runs/*.json", an error row, a PLACEHOLDER box, and 49 leads vs 42. It's already in a planned rebuild, so maybe just hide the raw bits for now.
- **Privacy page** isn't linked from anywhere (site or landing). It mentions only Google sign-in, although email sign-up exists, and it has no contact email.
- **Small stuff:**
  - The sign-in popup title says "CraneSignal (Open WebUI)".
  - The cal.com link slug is `propertystack-intro` (it's in `chatbot/proxy.py` BOOK_CALL_URL and on the landing page).
  - Landing sign-ups go silently to `/data/signups.csv` with no alert to Drew (0 so far).
  - Saved deep-dive replays still use up 1 of the 3 weekly deep dives (`chatbot/proxy.py` gateway_chat: `_free_take` runs before the saved replay).

## 🟠 Data (fix upstream in the lead finder, then rebuild with `python3 site/data/build_data.py`)
- **Texas junk, about 9 rows:**
  - Pool permits: tx-305, 325, 328, 343.
  - Carport: tx-301. Stair remodel: tx-327. Garage apartment: tx-335.
  - Check tx-7 and tx-365 (parking garage mentioned, but they may be real apartments).
  - Add a filter for pool, carport, remodel, repair and roof permits.
- **Westdale Hills Apts:** listed in both Hurst and Euless at 2,141 units, and it's an old complex. It tops the size sort.
- **Missing units:** 124 of 628 Texas rows and 80 of 279 Arizona rows show "?". New York's 2 rows show **0** units (should be "?" or dropped).
- **Duplicate names:** 17 Texas pairs in the same city (Buena Vida Brownsville, Belmont Austin, Lakeside Lofts San Antonio, Emberstone San Antonio, 6802 Marbach Lofts, Lofts at Birdwell…). Some may be real phases.
- **Generic Arizona names:** 29 "Multi-Family Dwelling" (Scottsdale), 6 "Commercial Multi-Family" (Gilbert), 9 "Unnamed project" (Mesa and Maricopa County).
- **Source links:** all 279 Arizona sources (plus New York's 2 and 7 in Texas) are raw ArcGIS or Socrata API query URLs, not a page for that building. Also, 88 Texas sources show as bracketed labels like "[houston-weekly-xlsx]" and "[county record]", which is internal jargon.
- **Arizona contradiction:** rows with stage "leasing" show signal "Upcoming · opens not public yet" while the Why column says "Leasing" (e.g. az-1 La Victoria Commons).
- **Plano-Richardson rows** have address None (42 rows), so the chat can't give addresses.
- **Remember:** the Texas cleanup plan from the postmortem (handoffs/2026-09-15-texas-build-postmortem.md) overlaps with this. Merge the two, don't duplicate them.

## ✅ Already verified working (don't re-test)
- **Pages:** all pages and all 218 property ids, with no console errors. All 301 source URLs return 200.
- **Map:** markers, hover and click work, and the counts match (TX 628, AZ 279, NY 2). The regions sum to 628, the city list follows the region, and filters and sorts work. The old `?area=plano-richardson` link opens Texas.
- **Chat:** the name shows as CraneSignal Agent. The 10/day and 3/week limits work. Google OAuth redirect is fine and email sign-up works. "Opening soonest" now gives future dates.
- **Audit scripts in /tmp/audit** (may vanish): `flow.py` (page flow), `ui_chat.py` (live panel question), `ask.py` (API questions), `map2.py`.