# CraneSignal audit fixes — what changed

Written 2026-09-15 after the Sep 15 audit. All work is local; nothing was pushed
when this was written. This file is the plain-word record of every fix, the new
lead numbers, and the short list of things only Drew can do.

## The biggest change: the app now needs sign-in (E1)

- Online, every app page and its data needs the same sign-in the chat already
  uses (Google or email). That is Early Leads, the Map, property pages, AI
  Visibility, Under the Hood, and the data files behind them.
- Anyone not signed in is sent to the chat's sign-in page and lands back on the
  page they asked for after signing in.
- Still open to everyone: the privacy page, the style/font/favicon files the
  privacy page needs, and the chat app's own sign-in screen.
- The chat panel's little framed chat still works, and the check the panel uses
  to decide "signed in or not" still answers.
- Locally nothing changed: `bash tooling/dev.sh` serves the site with no sign-in
  so testing stays easy.

## The site pages (A1–A9)

- **A1 Phones:** every page has the "fit a phone screen" tag, and the phone
  checks now really pretend to be a phone; nothing overflows sideways.
- **A2 Early Leads numbers:** the number boxes at the top follow whatever you
  have picked (state, region, city, search). A search with no matches shows one
  clear "Nothing found" row with a Clear search button.
- **A3 Chat panel open:** with the chat open on a desktop the table becomes one
  card per building, so Software and Why are always readable. "Chat" no longer
  looks selected when the panel is open.
- **A4 Every building opens:** every row in Texas, Arizona and New York opens a
  page with its name, town, stage, units, software, why, sources and a Deep dive
  button — not just the 42 Plano rows.
- **A5 Deep dive tells the truth:** the deep-dive question now says the real
  stage ("permit filed", "under construction", "leasing now", "recently sold")
  instead of calling every upcoming building "planned".
- **A6 Menu footer:** "Last updated" comes from the built data (today's date),
  not a hard-coded Sep 10. "View as" has a plain label and a tooltip, and
  "Neutral" reads "Everyone".
- **A7 Under the Hood:** the raw bits (area tag, run-file names, an error row, a
  place-holder box) are hidden, and its lead count matches the site.
- **A8 Privacy page:** linked from the app menu and the landing footer, and it
  now explains Google sign-in, email sign-up, chats and what we store. One blank
  to fill: the contact email (see below).
- **A9 Map labels:** each state label sits in a small white pill with navy text,
  above its dot, and stays readable on a phone.

## The chat (B1–B4)

- **B1 Naming:** chat Sources say "CraneSignal lead ranking"; no user sees
  "PropertyStack" or "Open WebUI" anywhere in the chat.
- **B2 Counts match the site:** the chat's Texas table now includes the 42
  Plano–Richardson rows, so Texas reads the site total and Dallas–Fort Worth
  reads the same number the site shows.
- **B3 Vendor answers say their scope:** when the chat ranks software vendors it
  says the software data only covers Plano and Richardson, never implying it is
  statewide.
- **B4 Saved deep dives are free:** re-opening a deep dive you already paid for
  no longer uses one of your three free deep dives a week; only a fresh one does.

## The lead data (C1–C5)

- **C1 Junk permits out:** pool, carport, stair/remodel, repair, roof and
  garage-apartment permits are no longer leads. Seven Texas rows went.
- **C2 Duplicates:** Westdale Hills (an old complex listed twice) is gone, 16
  same-name duplicates were merged, and real phases are labelled "Phase 1 /
  Phase 2".
- **C3 Units and names:** New York's two rows show "?" instead of 0 units; 45
  Arizona rows that said "Multi-Family Dwelling" etc. now read "Apartments at
  <address>". Units were only filled when the count was already saved.
- **C4 Sources a person can open:** raw ArcGIS/Socrata query links (all 279
  Arizona, 7 Texas and 2 New York) now open the dataset's public page with a
  plain name like "City of Mesa building permits". Internal tags like
  "[houston-weekly-xlsx]" and "[county record]" now read "Houston weekly permit
  list" and "County property records".
- **C5 Stage and addresses:** a building marked "leasing" never also says
  "opens not public yet" (two Arizona rows were doing exactly that); 40 of the
  42 Plano–Richardson rows now carry the street address that was already saved
  with them, so the chat can give addresses. The last two have no address saved
  anywhere, so they stay blank rather than guess.

## New lead numbers

- **Texas:** 597 leads (was 628 before junk and duplicate clean-up).
  - Dallas–Fort Worth 311 · Houston 70 · Austin 84 · San Antonio 41 · rest of Texas 91.
- **Arizona:** 279 leads.
- **New York:** 2 leads.
- **Site total:** 878 leads.

## What only Drew can do

1. **Test the live sign-in** after the push. This is the one change that must be
   checked by a real browser: open https://app.cranesignal.com signed out and
   make sure you are sent to sign in and come back to the page, then check
   Privacy still opens with no sign-in.
2. **Turn on sign-up alerts.** The chat app can post "new person signed up" to
   Discord by itself, but it needs one Railway setting: on the chat service
   (`propertystack-chat`) add a variable named `WEBHOOK_URL` with the webhook
   link for the private `#new-users` channel. The link was sent in the Discord
   thread; it is a secret, so keep it out of GitHub. Open WebUI already formats
   the post correctly for Discord.
3. **Pick a contact email** for the Privacy page. It currently says
   `CONTACT_EMAIL_TBD`. Tell me the address and I will put it in.
4. **Rename the call link.** The booking button points at
   `cal.com/drew-pullen/propertystack-intro`. Rename it to something like
   `cranesignal-intro` in cal.com, then update `BOOK_CALL_URL` in
   `chatbot/proxy.py` and the landing page to match.
5. **Run the answer checks.** `bash tooling/qa/check-answers.sh` asks the live
   chat the frozen questions (including the new Dallas–Fort Worth and vendor
   questions). It costs money, so it is your call when to run it.
6. **Deploy the landing page.** The landing edits (no sign-up form, "sign in
   free", Privacy link) are committed in the `business` repo, which has no
   GitHub remote, so it needs its usual `railway up` from
   `business/marketing/landing`.
7. **Open WebUI name licence.** We hide "(Open WebUI)" from the chat name. Their
   licence only allows that while we stay at 50 or fewer users in any 30 days;
   past that, restore the name or buy their licence.

## Checks run (all green)

- `bash tooling/qa/check-fixes.sh` — 57 offline fix tests + the design check
  (0 problems on 7 pages).
- `bash tooling/qa/check-panel.sh` — clean.
- `bash tooling/qa/check-lead-finder.sh` — clean.
- `build_data.py` was re-run and reproduced the same files (no drift).
- The sign-in gate was tested offline by running the real Caddy file with the
  fake chat upstream: signed-out page/data requests redirect, Privacy and CSS do
  not, and a valid cookie gets the page.
- CORS for `app.cranesignal.com` was already fixed live earlier today, so the
  chat websocket works from the live site. No further action.
