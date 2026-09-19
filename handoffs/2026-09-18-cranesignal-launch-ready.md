# Handoff: CraneSignal launch readiness (2026-09-18, evening)

## Where things stand
- Interview is over. CraneSignal is now a free lead tool for **real estate investors** (first audience: r/CommercialRealEstate, r/realestateinvesting). One buyer type at a time; roofers dropped.
- **Live and pushed:** RealPage material archived (archive/realpage/), AI Visibility and Case Study tabs gone, map headline "Apartment activity by state", New York hidden, site open with no login, chat panel open by default (closable) asking visitors to make a free account.
- **Landing (cranesignal.com)** headline: "Apartment buildings that just sold. And what's coming next." Landing lives in the nested `business/` git repo (no remote); deploy = `cd business/marketing/landing && railway up --service propertystack-landing --ci`.
- Outer repo main pushed at 436f8a3 (auto-deploys app.cranesignal.com). Plans done: docs/plans/PLAN-archive-realpage.md, docs/plans/PLAN-investor-launch-site.md.
- Not yet verified live: the chat's "Make a free account" screen (local dev skips sign-in).
- Leftovers: 51 RealPage mentions in private business/ notes (`bash tooling/check-no-realpage-target.sh`); not visitor-facing.
- The case-study Railway service may still be running (no auth on /case-study/api/run); switch it off.

## Next job: make it ready for 20 users at once (all free tools)
Drew wants coding agents to review the code and simulated users to load-test it.
1. **Code review (free):** CodeRabbit (free for public repos, github.com/Pu11en/realpage is public) or self-hosted qodo-ai/pr-agent. Also Semgrep for security checks. Open a PR from a branch so the reviewer comments on it.
2. **20 simulated users (free):** Locust (github.com/locustio/locust, Python) or k6 (github.com/grafana/k6). Script: land on cranesignal.com → Start free → map → Early Leads → a building page, 20 users at once, report slow pages and errors.
3. **Chat under load:** each chat message costs DeepSeek credits, so ask Drew before any load test that sends real chat messages; test sign-up/open-chat without sending, or with 20 total messages.
4. Fix what the review and load test find, one small task each.

## After that
- First Reddit post: lead with "251 apartment buildings under construction or planned in Dallas–Fort Worth" (more than Austin + Houston combined); free tool mentioned at the end. Alt: 65 Phoenix sales in 2 years.
- Then a day-by-day launch-week plan (Reddit + X).

## How to talk to Drew
Short sentences. Max 5 per reply. One multiple-choice question at the end, 4+ options, recommendation first. Never suggest a break. Landing edits = change words only, keep his design.
