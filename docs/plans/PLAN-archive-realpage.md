# Plan: archive everything RealPage-as-target (2026-09-18)

Goal: CraneSignal stops being "a pitch to RealPage" and becomes a general free lead finder.
Move RealPage-target material into `archive/realpage/` (git history keeps everything).
KEEP: "RealPage" as a *software brand the detector finds* on buildings (like Yardi, Entrata) — that is product data.

Check: bash tooling/check-no-realpage-target.sh
Try: bash tooling/run-local.sh
Open: http://localhost:8080

## Tasks
- [x] T1 Write `tooling/check-no-realpage-target.sh`: greps site/, chatbot/, README/AGENTS for RealPage-as-target wording (allow-list: software-brand fields in data JSON, detector rules); exits non-zero with file list. Fix all 40 violations.
- [x] T2 Move research folders to archive/realpage/: 01-company, 02-products, 03-reviews, 04-reddit, 06-news, 09-ai-visibility, 09-build-ideas, 10-dashboard-wireframes, raw/realpage-site, raw/research-01.
- [ ] T3 Move case study to archive/realpage/casestudy (+ PLAN-casestudy-*.md, handoffs about the interview, .ccdb-* interview cards). Turn off the case-study Railway service and the /case-study link on app.cranesignal.com (only after Drew's OK).
- [ ] T4 Remove AI Visibility: site/ai-visibility.html, site/data/ai-visibility*, ai_visibility_lawsuit.py, build_ai_visibility.py, propertystack/data/ai-visibility, tooling/ai-visibility → archive; drop nav links.
- [ ] T5 Remove recruiter-scorecard.json and any "for RealPage" panels from site pages (map, under-the-hood, index, app.js).
- [ ] T6 Client-map skill ("buildings already on RealPage, skip them"): archive it and client-map.json; make lead scores stop penalising/boosting by RealPage.
- [ ] T7 Chatbot: rewrite SOUL.md, query skill and plugin so the agent knows nothing about RealPage the company; archive TEST-ANSWERS/SPOT-CHECK; fix link_guard tests.
- [ ] T8 Rewrite README.md, AGENTS.md, CHANGELOG header, business/BUSINESS.md, marketing-board to the new "leads for anyone selling to apartment owners" story; drop RealPage plans from docs/plans (site-library, ai-visibility v3/v4) into archive.
- [ ] T9 propertystack skill docs/tests (lead-finder, deep-dive, find-upcoming): reword "RealPage sales" to general buyers; keep detector rules.
- [ ] T10 Final sweep: run the check, start the site locally, click every page, chat 5 questions; nothing mentions RealPage as the customer.

## How to try it
1. Open the site locally: no "AI Visibility" tab, no RealPage pitch anywhere.
2. Ask the chat "who is this for?" — it says businesses that sell to apartment owners, not RealPage.
3. Open a building: it still shows which software it runs (RealPage is fine there).
