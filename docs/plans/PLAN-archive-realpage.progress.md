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

**Next:** T2 moves research folders to archive/realpage/
