# CraneSignal: fix what the Sep 15 live agent test found

Written 2026-09-15 from `handoffs/2026-09-15-agent-test-live.md` (read it first; screenshots were in
/tmp/agent-test/ and may be gone). **Starts only when Drew says "go work".** Localhost only: never push,
never deploy, never change Railway settings.

Ground rules for every task:
- User-facing name is **CraneSignal**. Never show "PropertyStack", "Hermes" or "Open WebUI" to users.
- Any new UI uses the existing classes in `site/css/styles.css`; the design check must keep passing.
- Every fix adds one small offline test in `tooling/qa/fixes_tests/test_<task>.py` (no network, no paid
  AI calls) that fails without the fix. Never weaken an existing test to make the Check pass.
- Data fixes happen upstream (lead finder / build scripts), then rebuild with
  `python3 site/data/build_data.py` and the chat's `chat-leads.csv`, and commit the rebuilt files.
- **Never touch anything AI Visibility** (`site/ai-visibility.html`, `site/data/*ai*`, `09-ai-visibility/`),
  nor `tooling/street-talk/`, nor the Under the Hood page (its own plan rewrites it).
- `check_answers.py` questions may be added but never run (they cost money); Drew runs them.
- Tech choices are yours. Anything only Drew can do goes in the final report, not a question.

AI for the build: Claude Sonnet.

Run with: `Do the next unticked task in PLAN-agent-test-fixes.md, then tick it and stop.`
Check: `bash tooling/qa/check-fixes.sh`
Try: `bash tooling/dev.sh` (site plus chat)
Open: http://localhost:8765/index.html

## How to try it (30 seconds)
1. Click **Ask** five times in a row after a fresh page load: the chat opens every time, with one header bar.
2. Click the CraneSignal logo: you go home. Open http://localhost:8765/nope.html: you see "Page not found".
3. Click **Deep dive** on a building twice: the second time is instant and says it's a saved deep dive.

## Tasks

### Broken
- [x] **T1 Chat loads every time.** `site/js/chat-panel.js` gives up after 8 s (`loadTimeoutMs`), but the
  chat often takes longer to wake. Raise the wait (e.g. 30 s) with a "Waking up the chat…" message, and
  one automatic retry before "Couldn't load the chat." (with a Try again button). Test: the timeout and
  retry logic. Commit.
- [x] **T2 One chat header bar.** The panel sometimes shows two stacked "Ask CraneSignal" bars (desktop and
  phone). Find why the panel/header is built twice (double init, re-open, retry) and make it idempotent.
  Test: opening the panel twice leaves exactly one header. Commit.
- [x] **T3 Sign-out button.** Add "Sign out" to the site header on every app page (calls the chat app's
  sign-out, clears the session, lands on the sign-in page). Hidden locally where there's no sign-in.
  Test: the link exists on every app page. Commit.
- [x] **T4 Real "page not found".** `site/Caddyfile` sends unknown addresses like /nope.html to the leads
  page with status 200. Serve a simple CraneSignal 404 page (with a link home) and status 404, without
  breaking the sign-in gate. Test against the Caddyfile offline like the E1 sign-in test. Commit.
- [x] **T5 Logo goes home.** The CraneSignal logo in the header is a plain box. Make it a link to
  index.html on every page. Test. Commit.

### Confusing
- [x] **T6 Saved deep dive comes back.** Clicking Deep dive a second time on the same building reopened
  the unsent question instead of the instant saved copy ("Saved deep dive from <date>. Press ↻ to redo
  it."). Find why the live flow misses the saved copy and fix it. Test. Commit.
- [x] **T7 No broken "Sources: )" line.** The answer to "Which buildings sold recently?" ended with
  "Sources: )". Find where citations are formatted (chat skill/SOUL or the proxy) and never emit an empty
  or broken Sources line. Test on a fixture answer. Add a check_answers question (don't run it). Commit.
- [x] **T8 Duplicate building.** "Torrington Wilmer" (300 units, Planned) appears twice, once as Dallas and
  once as Wilmer. Fix the dedupe upstream so the same project in two city labels becomes one row;
  rebuild data. Test. Commit.
- [x] **T9 Arizona names cleaned.** Some Arizona rows still show raw lot labels (e.g. "South Pier Lot 6",
  developer City of Tempe) instead of "Apartments at <address>". Widen the generic-name rule; rebuild.
  Test. Commit.
- [x] **T10 Table headers sort.** On `master-table.html` the column headers look clickable but do nothing.
  Make them sort (click again to reverse) and keep the Sort dropdown in step. Test. Commit.
- [x] **T11 Map markers do what they say.** The Texas/Arizona/New York markers say "click to open its table"
  but only show a popup. Either open that state's table or change the wording to match. Test. Commit.

### Polish
- [x] **T12 Fence permit gone.** One Houston lead is a "Multi-Family New Perimeter Fence" permit. Add fences
  to the non-apartment permit filter upstream; rebuild. Test. Commit.
- [x] **T13 No duplicate source links.** Some building pages show "Website" and "State project record" as the
  same state link. When the website is only the state record, show it once. Test. Commit.
- [x] **T14 Shorter leads list.** Early Leads shows all 597 Texas rows at once. Show the first 50 with a
  "Show more" button (filters and counts still use every row). Test. Commit.

### Finish
- [x] **T16 Privacy contact email.** Drew picked **drewpullen2003@gmail.com** (2026-09-15). Replace
  `CONTACT_EMAIL_TBD` in `site/privacy.html` (link text and mailto) and anywhere else it appears in
  `site/` or the landing page. Test: no `CONTACT_EMAIL_TBD` left in `site/`. Commit.
- [x] **T15 Final checks and report.** Run the Check, the design check and the panel check; write
  `handoffs/<date>-agent-test-fixes-report.md` in plain English: what changed, how to try each, anything
  only Drew can do, and what's not done. Commit.
