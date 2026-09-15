# Plan C: fix the agent-test findings (15 small jobs)

## How it runs
- ⬜ **Starts only when you say "go work".** Claude Sonnet does one job per fresh session, on your computer only. Nothing is pushed or put live.
- After every job, an automatic check runs: all the earlier fix tests plus the new ones.
- Each fix gets its own small test that fails without the fix, so it can't quietly break later.
- It won't touch AI Visibility, Street Talk or the Under the Hood page (that page has its own plan).
- The privacy contact email is left for you. It goes in the final report.

## ⚠️ Broken (jobs 1–5)
- **1 Chat loads every time:** it waits up to 30 seconds instead of 8, says "Waking up the chat…", retries once by itself, then shows a Try again button.
- **2 One chat header bar:** stops the "Ask CraneSignal" bar from appearing twice.
- **3 Sign-out button:** "Sign out" goes in the header of every page.
- **4 Real "page not found":** a made-up address shows a simple CraneSignal "not found" page with a link home, instead of the leads page.
- **5 Logo goes home:** clicking CraneSignal takes you to the leads page.

## 🟡 Confusing (jobs 6–11)
- **6 Saved deep dive comes back:** clicking Deep dive a second time on a building gives the instant saved copy.
- **7 No broken "Sources: )" line** at the end of chat answers.
- **8 Duplicate building:** "Torrington Wilmer" shows once, not twice.
- **9 Arizona names cleaned up:** lot labels like "South Pier Lot 6" become "Apartments at <address>".
- **10 Table headers sort:** clicking a column header in the full table sorts by it, and clicking again reverses it.
- **11 Map markers do what they say:** clicking the Texas, Arizona or New York marker opens that state's table, or the wording changes to match what happens.

## 🔹 Polish and finish (jobs 12–15)
- **12 Fence permit removed** from the Houston leads.
- **13 No doubled source links:** "Website" and "State project record" show once when they're the same link.
- **14 Shorter leads list:** the first 50 rows show, with a "Show more" button. Filters and counts still use every lead.
- **15 Final checks and a plain-English report** of what changed and how to try each fix.

## How you'll try it (30 seconds)
- Click **Ask** five times after a fresh page load: the chat opens every time, with one header bar.
- Click the logo and you go home. Type a made-up page address and you see "Page not found".
- Click **Deep dive** on a building twice: the second time is instant and says it's saved.
