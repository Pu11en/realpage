# Progress: archive RealPage-target material

## T1 ✅ Write check-no-realpage-target.sh + fix all violations

**What:** Created bash script `tooling/check-no-realpage-target.sh` that identifies RealPage-as-target (customer pitch) references. Script allows:
- RealPage as a software brand in data files (leads.json, rules.json, detector rules)
- RealPage in vendor comparison lists (alongside Yardi, Entrata, AppFolio)
- RealPage in outside-in research context
- Color mappings for RealPage as a vendor

**Violations found and fixed:** 40 lines across site/, chatbot/, README.md, AGENTS.md, docs/

**Changes:**
- Site: map.html, under-the-hood.html, js/map.js — changed "Where RealPage already has clients" to "Apartment buildings by software", removed RealPage-specific marketing language
- Chatbot: SOUL.md — removed "software opportunities for RealPage" references, changed to generic vendor/company language
- Chatbot plugin: propertystack/__init__.py — changed "RealPage research notes" to "Research notes", generalized AI Visibility descriptions
- SKILL.md: changed description from "RealPage research folders" to "research data"
- README.md: changed pitch from RealPage-specific to "any property-management software company"
- AGENTS.md: removed "RealPage / PropertyStack" header, generic "site library" instead of "RealPage library", removed "RealPage Discord thread"
- Test docs: removed RealPage-specific test scenarios, changed to vendor-neutral examples

**How checked:** Ran `bash tooling/check-no-realpage-target.sh` → ✓ No RealPage-as-target references found

## T2 ✅ Move research folders to archive/realpage/

**What:** Moved 10 research folders (01-company, 02-products, 03-reviews, 04-reddit, 06-news, 09-ai-visibility, 09-build-ideas, 10-dashboard-wireframes, raw/realpage-site, raw/research-01) from root into archive/realpage/ using `git mv` to preserve history.

**Fixed path references:** Updated 10 files that had hardcoded references to the old paths:
- .claude/skills/mvp-plan-review/SKILL.md (2 references)
- PLAN-v1-cleanup.md (1 reference)
- README.md (1 reference)
- chatbot/Dockerfile (research folder copy paths)
- chatbot/README.md (1 reference)
- docs/plans/PLAN-ai-visibility-v4.md (4 references)
- docs/plans/done/PLAN-realpage-site-library.md (5 references)
- tooling/ai-visibility/to_research.py (output path)
- tooling/realpage-library/cards.py (2 paths)
- tooling/realpage-library/facts.py (2 paths)
- tooling/realpage-library/index.py (2 paths)

**How checked:** Ran `bash tooling/check-no-realpage-target.sh` → ✓ No issues found

**Commit:** d987858 "T2: Move research folders to archive/realpage/ and fix all path references"

**Next:** T3 moves case study to archive/realpage/casestudy

**Follow-up fix:** Fixed stale path in `tooling/ai-visibility/run-and-report.sh` line 14: changed `09-ai-visibility/summary.md` to `archive/realpage/09-ai-visibility/summary.md` to reflect the moved research folders.

## T3 ✅ Move case study to archive/realpage/casestudy (part 1 — file move complete)

**What:** Moved the case study directory and related planning files to archive/realpage/casestudy using git mv to preserve history. Updated all path references across the codebase.

**Files moved:**
- casestudy/ directory (75 files including Python code, web assets, research, tests)
- PLAN-casestudy-bot.md
- PLAN-casestudy-bot.progress.md
- PLAN-casestudy-repo-hunt.md
- PLAN-casestudy-repo-hunt.progress.md

**Path references updated in:**
- tooling/qa/fixes_tests/test_e1_signin.py (line 160)
- chatbot/hermes-profile/SOUL.md (line 54)
- handoffs/2026-09-18-realpage.md (Key files section, lines 28-37)
- .planning/2026-09-17-c13-dress-rehearsal/findings.md (lines 14, 31-34)
- .planning/2026-09-17-case-study-human-results/findings.md (lines 44-47)

**How checked:** Ran `bash tooling/check-no-realpage-target.sh` → ✓ No RealPage-as-target references found

**Commit:** 7e5b41a "T3: Move case study to archive/realpage/casestudy and update path references"

**Next:** Part 2 requires Drew's OK: turn off the case-study Railway service and the /case-study link on app.cranesignal.com

## T3 ✅ part 2 — case study turned off (Drew said yes, 2026-09-18)

**What:** Removed the Case Study nav tab (site/js/app.js), the /case-study route in site/Caddyfile, the casestudy service from both chatbot compose files, and the case-study image from tooling/qa/check-container-security.sh. Updated test_e1_signin.py and test_h6_human_preview.py to match; .gitignore paths now point at archive/realpage/casestudy.

**Railway:** Ran `railway down` on service `propertystack-case-study` (project propertystack, production). Its only live deployment a9fae1cf is now REMOVED, so it uses no credits. The service shell and its settings still exist (not deleted), so it can be redeployed.

**How checked:** check-no-realpage-target.sh passes; the two edited test files pass (8 tests); Railway deployment list shows REMOVED.

**Left open:** The live site still shows the Case Study tab until this branch is pushed (nothing pushed, per the GitHub-last rule); clicking it now gives an error page. SOUL.md still mentions the case study folder — T7 rewrites it.

## T3 ✅ review fix — interview handoffs archived (2026-09-18)

**What:** Moved handoffs/2026-09-18-realpage.md (case-study interview) and handoffs/2026-09-14-realpage.md (goal = RealPage interview leverage) to archive/realpage/handoffs/. Kept 2026-09-15-realpage.md and -night.md: they are about the CraneSignal agent and shipcheck, not the interview. No other file referenced the old paths; no .ccdb-* interview cards exist in the repo. T3 box ticked.

**How checked:** check-no-realpage-target.sh passes; grep for the old paths finds nothing outside this log.

## T4 ✅ AI Visibility removed (2026-09-18)

**What:** Moved the AI Visibility page, its site data and history, the two builder scripts, propertystack/data/ai-visibility, tooling/ai-visibility, its chat-data builder, its QA checks/test and design screenshot to archive/realpage/ai-visibility/. Dropped the nav tab (site/js/app.js), the Caddyfile route, the Dockerfile KB copy line, the design-pages entry, the AI-visibility question in check_answers.py, and the page from three test page lists.

**Commit:** 2df476e

**How checked:** check-no-realpage-target.sh passes. tooling/qa/fixes_tests: 199 pass, 4 fail — the same 4 fail before this change (chatbot SOUL/link tests, T7's job).

**Left open:** Chatbot SOUL/skill/plugin still mention AI Visibility (T7); README/AGENTS/plans mention it (T8); site/data/buildbot.json keeps a historical build-log entry naming it. Stale allow-list lines for the old paths remain in the check script (harmless).

## T4 ✅ review fix — stale imports fixed (2026-09-18)

**What:** Fixed import paths in `tooling/realpage-library/cards.py` and `tooling/realpage-library/facts.py`. Both were still pointing to `tooling/ai-visibility/local_ai.py` which had been moved to `archive/realpage/ai-visibility/tooling/local_ai.py` in T4. Updated both files to use the new archived path.

**Files fixed:**
- tooling/realpage-library/cards.py (line 17)
- tooling/realpage-library/facts.py (line 15)

**How checked:** 
- `python3 tooling/realpage-library/cards.py --help` runs without error
- `python3 tooling/realpage-library/facts.py` imports and executes successfully
- `bash tooling/check-no-realpage-target.sh` passes

## T5 ✅ recruiter scorecard framing removed (2026-09-18)

**What:** Renamed site/data/recruiter-scorecard.json to saved-scorecard.json and reworded its status from "Historical recruiter scorecard" to "Historical scorecard" (also in evals.json, chat-stats.json, build_evals.py and test_h2). The file was kept, not deleted, because Under the Hood's frozen numbers are rebuilt from it. Searched map, under-the-hood, index and app.js for "for RealPage" panels: none remain (T1 already removed them); the only RealPage mention in pages is the software-brand list in app.js.

**Commit:** 1b10fd1

**How checked:** check-no-realpage-target.sh passes; test_h2 passes; fixes_tests 199 pass, the same 4 chatbot failures as before (T7).

**Left open:** map.js still loads client-map.json (T6). Old docs/plans/done and .planning notes still say "recruiter" (history, not shown on the site; T8 may archive).
