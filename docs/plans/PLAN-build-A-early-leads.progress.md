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

## 2026-09-19 — G1-T2 review follow-up

- Added an offline regression test for the complete contact-research contract: contact-first answers, saved data before web lookup, six-search limit, sourced phone/website, visible not-found gaps, no guessed numbers, and a sourced new owner for recent sales.
- Test commit: `329abd5` (`test: cover sourced contact research rules`).
- Checks: the focused test passed (7); required QA passed (214); all active project suites passed (612). `git diff --check` passed.
- Open: no live or paid AI call was made. G1-T3 and later tasks remain for subsequent workers.

## 2026-09-19 — G1-T3 Get contact button

- Replaced the visible Deep dive buttons on every Early Leads row and both building-page paths with “Get contact →”, directly under the building name on the left.
- Contact questions now submit automatically. Signed-out visitors see “Make a free account” while the question waits, and that same question sends as soon as signup finishes; a shared `ask` path is ready for the later lead-search task.
- Updated saved-contact behavior so a request is remembered only after it actually sends, not while it is waiting for signup.
- Added offline coverage for labels, placement, automatic submission and the signup queue. Extended the fake chat and browser check to prove the waiting question sends after signup, and brought that harness in line with the existing open-by-default panel.
- Implementation commit: `284dcfe` (`feat: send sourced contact requests from every lead`).
- Checks: required `python3 -m pytest -q tooling/qa/fixes_tests/` passed (219); the other active project suites passed (398); `bash tooling/qa/check-panel.sh` passed; `node --check site/js/chat-panel.js` and `git diff --check` passed.
- Limits: all checks used local fake/offline services; no paid or live AI call, push or deployment. AF-T1 and later tasks remain for subsequent workers.

## 2026-09-19 — AF-T1 Agent lead search

- Added a wide “Describe the leads you want…” bar above the existing filters, with an accessible label and an Ask agent button; pressing Enter submits it too.
- Requests use the shared agent `ask` path, so the panel opens and sends automatically for signed-in visitors, while signed-out visitors keep the question queued through account creation.
- Added offline coverage for placement, full-width styling, accessible form controls, empty-query handling and the shared send path.
- Implementation commit: `10f85c3` (`feat: add agent lead search bar`).
- Checks: required QA and all active project suites passed together (628); `git diff --check` passed.
- Limits: no real AI call, paid service, push or deployment. AF-T2 and later tasks remain for subsequent workers.

## 2026-09-19 — AF-T2 Location-aware example searches

- Added three example chips below the agent search for openings, recent large sales, and buildings without software; the wording uses the selected state or region and refreshes immediately when the region changes.
- Clicking a chip sends its full text through the shared agent `ask` path, including the existing sign-up queue for signed-out visitors. Added offline checks for placement, location-aware wording, click behavior, wrapping chip styles, and region refresh.
- Implementation commit: `1dbed75` (`feat: add location-aware lead examples`).
- Checks: required QA passed (234); the other active project suites passed (398); a local Chromium check showed all three Texas examples, sent a clicked query, and refreshed all three for Austin. `git diff --check` passed.
- Check correction: the first combined test command named the old nonexistent `propertystack/tests` path; reran against the actual `propertystack/lib/tests` and `propertystack/skills/*/tests` paths successfully.
- Limits: no real AI call, paid service, push or deployment. AF-T3 and later tasks remain untouched; those tasks are still needed to fold filters, finish mobile layout, remove the fake New count, show the real data date, and complete the overall build.

## 2026-09-19 — AF-T3 Folded filters

- Put property search, signal, city, software, sort, and hide-my-software controls behind a small Filters button that starts closed; the state and region pills remain visible.
- The button reports its open/closed state for assistive technology, and opening or closing it leaves the existing filter controls and event handlers intact.
- Added offline coverage for the closed default, accessible toggle, control placement, visible location pills, and unchanged filter listeners.
- Implementation commit: `b6d5f35` (`feat: fold early lead filters by default`).
- Checks: required QA passed (239); the other active project suites passed (398); focused AF-T1 through AF-T3 tests passed (12); `git diff --check` passed.
- Browser check: Chromium confirmed the controls start closed, open from the button, property search narrows to the matching building, and the Sold dropdown returns only sold rows.
- Limits: no real AI call, paid service, push or deployment. AF-T4 and later tasks remain untouched; the overall build still needs the mobile pass, fake New removal, real data date, final screenshots, and approved publishing.

## 2026-09-19 — AF-T4 Phone layout

- At widths below 900px, the lead request input and submit button, all three example chips, the Filters toggle, and opened filter controls now stack at full width with 44px touch targets and readable wrapping.
- Added regression coverage for the mobile behavior while retaining the existing AF-T1 through AF-T3 tests, plus desktop and 390px phone screenshots in `docs/plans/af-t4-screenshots/`.
- Implementation commit: `d9744cf` (`feat: stack early lead controls on phones`).
- Checks: required QA passed (242); the other active project suites passed (398); focused AF-T1 through AF-T4 tests passed (15); `git diff --check` passed. Chromium at 390px confirmed the column layout and no horizontal overflow.
- Check correction: the first browser geometry assertion compared the bordered form to its inner button exactly; the expected two-pixel border difference was allowed and the corrected browser check passed.
- Limits: no real AI call, paid service, push or deployment. G3-T1 and later tasks remain untouched; the overall build still needs fake New removal, the real data date, final freshness text/screenshots, and approved publishing.
