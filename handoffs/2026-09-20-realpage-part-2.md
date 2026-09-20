# Handoff: CraneSignal (realpage repo), 2026-09-20 part 2

## Goal — what we are ultimately trying to achieve
Drew's RealPage interview is over (2026-09-18; he felt it went badly). CraneSignal is no longer a pitch to
RealPage: it is a free product for **companies that sell software or services to apartment buildings**
(property-management software, resident tech, leasing/marketing services). It lists apartment buildings that
just did something worth a call — filed permits, opened soon, or sold to a new owner — and an AI agent finds
**who to call** for any of them. The immediate goal is real users: finish the data, then launch (LinkedIn first).
Never advertise which states are covered; the story is "U.S. apartment leads".

## Where things stand — done, in progress, broken
**Live and working** (app.cranesignal.com = the app, cranesignal.com = the landing page; both deploy from
`main` of github.com/Pu11en/realpage, landing via `railway up` from the nested `business/` repo):
- RealPage material archived (`archive/realpage/`), AI Visibility + case study gone; tag `launch-v1` marks the
  launch-ready state; editions saved as branches `edition/software-sellers` (current) and `edition/investor`.
- Leads page: "All areas" tab ranked across states, quick filters with counts (New builds / Opening soon /
  Recently sold), state+region pills, plain words everywhere ("call list", "See who to call", "Why now"),
  address under each building, office phone shown free when public.
- Free to browse with no login. A **free account** unlocks: who to call (agent), the call-list PDF, the CSV
  spreadsheet. Public sample call list at /sample-lead-pack.pdf.
- Agent panel is part of every page: docked open on screens >= 900px (it shrinks the page, never covers it);
  on phones a yellow "Ask the agent" bar is pinned at the bottom. Closing it only lasts for that page view.
- Map: states clickable; "Don't see your area?" box posts to the landing server, which saves it and posts to
  the Discord sign-ups channel (`SIGNUP_WEBHOOK_URL` is set on the landing Railway service).
- Hero line on both sites, filled from data: "Last check Sep 20, 2026: 936 buildings just filed permits,
  526 just sold. 1,462 tracked." Source: `site/data/summary.json`.
- Scores: Lighthouse app 97/100/100/100, landing 100s; Mozilla Observatory landing A+, app B+.
- 250+ tests pass: `python3 -m pytest -q tooling/qa/fixes_tests/`.

**The lead run (finished 2026-09-20 ~00:23, all 14 tasks, auto-published):**
- Texas: 592 -> **1,176** leads. Arizona: 279 -> **274**. Both fine.
- New Mexico: only **12** leads, so it is auto-hidden (rule: hide an area under 25 leads).
- **Broken:** `nm/albuquerque.json` returned 0 rows even though the endpoint is live and holds **236** apartment
  permits (verified by hand: add `&returnCountOnly=true` to the recipe's endpoint). `nm/las-cruces.json`
  returned only 2 of ~82k rows. This is a bug in the new runner's arcgis handling, not a missing source.
- Genuinely missing sources (documented, not a bug): Rio Rancho and Santa Fe have no machine-readable permit
  feed; New Mexico counties publish no free sale price/date. See `propertystack/runs/needs-a-source.md`.

**Known leftovers:** 51 RealPage mentions in private `business/` notes (no visitor sees them); many buildings
have no phone and some no unit count; the old `propertystack-case-study` Railway service still exists but is
dead (all 404, nothing running) — Drew can delete it in the Railway dashboard.

## Decisions — do not re-ask
- Audience: sellers into apartments. Investors edition exists but is parked on `edition/investor`.
- Never name covered states on any page. Show size + freshness instead (the hero line above).
- Say "check" or "run", never "scrape", in anything a visitor sees.
- Browsing is free; a free account is required for who-to-call, the PDF and the CSV. Say it up front, in plain
  words, before the visitor hits it.
- Lead runs publish live automatically once the checks pass. No waiting for Drew.
- A run must **never stop to ask Drew a question**: rules decide, a failed source is retried once then skipped
  with a note, the run carries on and reports at the end.
- Cheap by design: pulls are plain downloads, no AI. AI is only used to find a replacement source for a city
  that has none, capped at 20 searches/city and 100/run.
- `/gowork` runs **one build per project at a time** — starting a second kills the first. Put everything in one
  ordered plan; parallelism belongs inside the runner (6 sources at once).
- `business/` is a **separate nested git repo** (no remote). The real landing page lives there; a gowork build
  cannot see it, so landing edits are done by hand, wording only, keeping Drew's design.
- Product polish is frozen at `launch-v1` unless something is broken. First-user test scores plateaued
  (5.2 -> 6.6 -> 6.7 -> 6.4 out of 10); pretend users stopped teaching us much.
- How to talk to Drew: very short sentences, max 5 per reply, blank line between each, and **every** reply ends
  with one multiple-choice question (4-5 real options, recommendation first). Never suggest taking a break.
  He only reads Discord: never point at a file or path as if he read it; put long material in a Markdown file
  whose path is appended to `.ccdb-attachments-<thread id>` so it renders as cards.

## Next steps
1. **Fix the New Mexico pull** (the very next thing): make `tooling/run_area.py`'s arcgis handler return the rows
   the endpoint actually holds — Albuquerque should give ~236, Las Cruces far more than 2. Then re-run
   `bash tooling/new-run.sh nm` and confirm New Mexico unhides itself (needs >= 25 leads).
2. Spot-check the refreshed data: are the 526 "just sold" real, and did Texas gain anything junk? Run
   `python3 tooling/qa/check_lead_data.py`.
3. Then launch: LinkedIn first, angle "Stop fighting gatekeepers — call the building before the software is
   picked" (from the repo's own research: a rep in r/PropertyManagement wrote "the gatekeepers are really good
   at not letting me through"). Reddit only for helpful answers in r/sales and r/PropertyManagement, never a pitch.
4. Optional later: Nevada/Colorado in the same machine; a weekly automatic run; fill missing phones/unit counts.

## Key files
- /home/drewp/main-projects/realpage/docs/plans/PLAN-leads-run-nm-tx-az.md — the run plan and its decisions
- /home/drewp/main-projects/realpage/tooling/run_area.py — the parallel source runner (the bug is here)
- /home/drewp/main-projects/realpage/tooling/new_run.py and tooling/new-run.sh — the one-command chain
- /home/drewp/main-projects/realpage/propertystack/recipes/nm/ — the New Mexico source recipes
- /home/drewp/main-projects/realpage/docs/plans/nm-sources-research.md — verified NM endpoints and what each returns
- /home/drewp/main-projects/realpage/propertystack/runs/source-health.json and runs/needs-a-source.md — what worked, what did not
- /home/drewp/main-projects/realpage/site/data/build_data.py — builds site/data/areas/*.json + summary.json, stamps firstSeen
- /home/drewp/main-projects/realpage/site/index.html, site/js/app.js, site/js/chat-panel.js — the Leads page and the agent panel
- /home/drewp/main-projects/realpage/business/marketing/landing/index.html and server.py — the landing page (nested repo) and its area-request endpoint
- /home/drewp/main-projects/realpage/tooling/first-user-test/run.py — the 10-persona first-time-user test (browser-use + DeepSeek)
- /home/drewp/main-projects/realpage/EDITIONS.md — the editions and how to switch them
- /home/drewp/main-projects/realpage/handoffs/2026-09-18-cranesignal-launch-ready.md — the previous handoff
