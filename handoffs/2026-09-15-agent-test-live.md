# Agent test of the live app (Sept 15)

## What we did
- 5 AI testers acted as a new customer on **app.cranesignal.com**: sign-up and sign-in, the leads list, building pages and the full table, the map and other pages, and the chat with deep dives.
- They used one test account, which showed up in #new-users. ✅ **It is deleted now.**
- I double-checked the biggest findings myself. The chat timeout, the fake-page problem, the duplicate building and the fence permit are all real.

## ⚠️ Broken (fix first)
- **Chat fails to load about half the time.** The panel says "Couldn't load the chat." The page gives up after 8 seconds, but the chat often takes longer to wake up. A customer would think the chat is down.
- **The chat panel sometimes shows two "Ask CraneSignal" header bars** stacked on top of each other, on computer and phone.
- **There's no sign-out button anywhere.**
- **The privacy page still says CONTACT_EMAIL_TBD** (this needs your contact email).
- **A made-up address like /nope.html shows the leads page** instead of a "page not found".
- **Clicking the CraneSignal logo does nothing.** It should go home.

## 🟡 Confusing
- **A saved deep dive didn't come back.** Clicking Deep dive a second time on the same building reopened the unsent question instead of the instant saved copy.
- **One answer ended with a broken source line** that read just "Sources: )" (the "Which buildings sold recently?" question).
- **Duplicate building:** "Torrington Wilmer" (300 units, Planned) is listed twice, once as Dallas and once as Wilmer.
- **Some Arizona names still aren't cleaned up:** one reads "South Pier Lot 6" (developer City of Tempe) instead of "Apartments at <address>".
- **The full table's column headers look clickable but don't sort.** Only the Sort dropdown works.
- **The map's Texas, Arizona and New York markers say "click to open its table"** but only show a small popup.
- **Under the Hood reads like an engineering log:** pipeline names, raw counters and file names as link text.

## 🔹 Polish
- **The leads list shows all 597 Texas rows on one very long page** with no "load more", which is a lot of scrolling on a phone.
- **One Houston lead is a fence permit**, not an apartment project.
- **On some building pages, "Website" and "State project record" point to the same state link.**
- **102 Texas leads show "?" for units.** That's honest, just missing data.

## ✅ Worked well
- **Sign-up and sign-in** work and bring you back to the page you wanted. The name is CraneSignal everywhere, the Google button is there, and it works on a phone.
- **All lead numbers match exactly:** Texas 597 (DFW 311, Houston 70, Austin 84, San Antonio 41, rest 91), Arizona 279, New York 2, 878 in total.
- **Filters, search and sort work**, with no errors, no "0 units" and no junk text. "Last updated" is correct.
- **Building pages are right:** leasing buildings no longer say "opens not public yet", and every source link tested opened.
- **When the chat loads, it's good:** answers took 12–27 seconds and the numbers matched the site. It named its scope for the software question, didn't leak any code or old names, Past chats works, and the deep dive gave a real address, phone and 4 working sources.
- **Phone layouts held up** on every page tested.
