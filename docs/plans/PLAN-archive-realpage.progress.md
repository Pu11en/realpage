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
