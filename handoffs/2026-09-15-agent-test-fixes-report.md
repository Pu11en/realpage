# Agent-test fixes — what changed

Every problem the live agent test found on Sep 15 has been fixed, tested, and checked. All automated
checks pass: 110 offline tests, the design check (0 problems on 7 pages), and the chat panel check (0
problems on 3 pages, panel_test.py clean).

## Broken things, now fixed
- **Chat loads every time.** The chat used to give up after 8 seconds if it was slow to wake up. It now
  waits 30 seconds, shows "Waking up the chat…", and automatically retries once before showing an error
  with a Try again button.
- **One chat header bar.** The chat panel could sometimes show two stacked header bars. It's now
  guarded so it can only build itself once, no matter how it's opened or reopened.
- **Sign-out button.** Every app page now has a Sign out link in the header (hidden on your local test
  copy since there's no sign-in there).
- **Real "page not found" page.** Visiting a bad address like /nope.html used to silently show the leads
  page. It now shows a proper CraneSignal "not found" page with a link home.
- **Logo goes home.** Clicking the CraneSignal logo in the header now takes you to the home page.

## Confusing things, now fixed
- **Saved deep dive comes back.** Clicking "Deep dive" a second time on the same building now instantly
  shows "Saved deep dive from <date>. Press ↻ to redo it." instead of re-asking the same question.
- **No more broken "Sources: )" line.** Found the exact bug: when a citation link pointed to something
  the tool never actually returned, the text was removed but stray parentheses were left behind. Now the
  whole broken line is dropped.
- **Duplicate building fixed.** "Torrington Wilmer" was showing up twice (once under Dallas, once under
  the neighboring town Wilmer) because the de-duplication only compared buildings within the same city
  label. It now compares by name first, so the two copies merge into one.
- **Arizona names cleaned up.** Some Arizona listings were showing raw government lot/parcel labels
  (like "South Pier Lot 6") instead of a readable name. They now show as "Apartments at <address>", and
  this same fix caught and cleaned a similar case in Texas.
- **Table headers sort.** The column headers on the leads table (Score, Property, City, Units, Signal,
  Software) now actually sort when clicked, with an arrow showing which way, and stay in sync with the
  Sort dropdown.
- **Map markers do what they say.** The state markers on the map said "click to open its table" but
  sometimes the click missed and only showed a small popup. The clickable area around each marker is now
  bigger so clicks land reliably.

## Polish, now fixed
- **Fence permit removed.** A Houston "perimeter fence" permit was showing up as an apartment lead
  because its text happened to include the words "multi-family." It's now filtered out along with other
  non-apartment permits, and the underlying data was rebuilt.
- **No duplicate source links.** Some building pages showed the same state website link twice, once
  labeled "Website" and once "State project record." Now it only shows once, with the more specific
  label.
- **Shorter leads list.** The Early Leads table used to show all ~593 Texas rows at once. It now shows
  the first 50 with a "Show more" button to load 50 more at a time. The stats and filters still count
  every row, not just the visible ones.

## Finishing touches
- **Privacy page contact email.** The placeholder email on the privacy page is now Drew's real address,
  drewpullen2003@gmail.com.

## What's not done
Nothing from the plan is left undone — this was the final task, closing out the list. Everything has
been committed locally. Nothing has been pushed or deployed; that's Drew's call once he's tried it
himself.

## Anything only Drew needs to do
- Nothing required. Optional: when ready, say "push it" to put this on GitHub (nothing has been pushed
  yet).
