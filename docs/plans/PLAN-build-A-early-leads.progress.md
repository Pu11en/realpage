# Build A: Early Leads agent-first — progress

## 2026-09-19 — G1-T1 Deep dive prompt

- Updated upcoming and sold lead prompts to ask first for the management company, office phone, website, role, and a source link for each.
- Recently sold leads with no buyer now also ask who bought the building; the Early Leads and building-page callers pass buyer data when it exists.
- Added prompt coverage for contact-first ordering, known buyers, missing buyers, and all existing lead stages.
- Implementation commit: `549a726` (`feat: ask for sourced lead contacts first`).
- Checks: focused prompt tests passed (3); required QA suite passed (207); all active project test folders passed (298).
- Note: an unscoped repository-root pytest run cannot collect archived projects because their old standalone import paths are unavailable. The current, non-archived project suites are green.
- Open: G1-T2 and the later plan tasks remain untouched for subsequent workers.

## 2026-09-19 — G1-T2 Chat rules

- Updated SOUL.md and the query-propertystack skill to start building research with Who to call: company, office phone, website and role, each with a supporting link; missing or unsupported details remain visible as "not found".
- Research uses the building's saved contact/developer data first, then at most six web searches within twelve total tool calls. Developer and permit contacts retain their real roles.
- Recent sales always include New owner, using saved buyer evidence first and county/news lookup for missing evidence; sellers and developers cannot be substituted for buyers.
- Removed conflicting old CSV-only contact, answer-layout, citation and tool-budget instructions.
- Implementation commit: `2b516ae` (`feat: require sourced contact-first building research`).
- Checks: required `python3 -m pytest -q tooling/qa/fixes_tests/` passed (207); final combined run of that suite plus `chatbot/tests`, `tooling/street-talk/tests`, `tooling/realpage-library/tests` and `propertystack` passed (605). `git diff --check` passed.
- Skill validation: the Codex-only quick validator rejects the existing Hermes frontmatter keys (`author`, `platforms`, `version`); separately validated YAML, required fields and unchanged Hermes metadata. No metadata migration was needed.
- Limits: these are instruction changes, checked offline; no real AI calls, paid searches, push or deployment. Actual generated answers have not been live-tested.
- Open: G1-T3 and subsequent tasks remain untouched. This step supports the overall goal; buttons, search/filter UI, freshness display and eventual approved publishing remain for later work.
