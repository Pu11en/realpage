# Build A: Early Leads agent-first — progress

## 2026-09-19 — G1-T1 Deep dive prompt

- Updated upcoming and sold lead prompts to ask first for the management company, office phone, website, role, and a source link for each.
- Recently sold leads with no buyer now also ask who bought the building; the Early Leads and building-page callers pass buyer data when it exists.
- Added prompt coverage for contact-first ordering, known buyers, missing buyers, and all existing lead stages.
- Implementation commit: `549a726` (`feat: ask for sourced lead contacts first`).
- Checks: focused prompt tests passed (3); required QA suite passed (207); all active project test folders passed (298).
- Note: an unscoped repository-root pytest run cannot collect archived projects because their old standalone import paths are unavailable. The current, non-archived project suites are green.
- Open: G1-T2 and the later plan tasks remain untouched for subsequent workers.
