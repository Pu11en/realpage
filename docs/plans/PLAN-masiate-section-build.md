# Masiate Section Build

## PAUSED By Drew

On September 20, 2026, after submission but before AI selection, Drew said
"no pause that" and redirected discussion to whether the listed projects
actually need Masiate. Do not execute this plan or interpret answers to the
lead-fit discussion as an AI/build selection. Resume requires explicit human
instruction. No Masiate build worker was present in the loop store at this pause.
The key unresolved question is target buyer: owner hiring a main contractor,
general contractor hiring a trade crew, or another explicitly defined buyer.
The bank ranked first already names EBCO as general contractor; its open
subcontract needs were NOT established. Construction activity and service fit
must not be presented as proven demand for Masiate.

Check: bash tooling/qa/check-panel.sh
Try: python3 -m http.server 8891 --bind 127.0.0.1 --directory site
Open: http://localhost:8891/masiate.html

Goal: Add a regular public Masiate Construction section to CraneSignal, backed by the completed pilot, with the fixed PDF and source-aware access through the existing agent.
Done when: Visitors can find Masiate in navigation, browse/filter the 49 reviewed properties, download the unchanged report, and ask the existing agent about Masiate or a selected property; data, chat handoff, container packaging, regression tests and desktop/mobile checks pass locally, with an honest push-readiness report and no push or deployment.

## Authority And Boundary

Drew explicitly requested this plan and task-loop execution on September 20,
2026: "make the new section and all the rest that is needed ... plan it out
yourself then have task loop workers to get it done ... when i push it will be
ready for that company". This authorizes implementation and local checks,
not publishing, new subscriptions, extra collection or paid live-model tests.
Use this six-task plan only. Do not resume the deleted fifty-task collection
plan or the completed pilot/review workers.

Start from the parent session HEAD containing local delivery commit 33e861f.
Keep the pilot's public export and PDF immutable. Do not depend on runtime
files under /home/drewp/.local/state in the deployed app.
Local git commits are expected; no main-branch mutation, push or deploy.
Use the loop's isolated copies and default concurrency, without changing bot
limits or launching extra workers outside the loop. Archive finished workers
only after saved work and idle state are verified; preserve histories.

## Product Decisions

- Public `masiate.html`, in the normal CraneSignal navigation and same shell;
  no separate app, customer login wall, private workspace or new database.
- Keep the existing chat sign-in and usage limits. Public records/report are
  readable without signing in; agent questions use the normal account flow.
- Compact ranked list, county filter, keyword search, contact-available filter,
  clear result count and reset/empty/error states. Preserve ranks when filtering.
  Show useful scope/fit and sources inline or in a restrained expandable row;
  do not build a second full property-detail app or a map.
- Fixed September 20, 2026 report download; clear report/data date and incomplete
  coverage. 49 profiles, 267 collected entries, seven counties, 76 checks;
  six profiles with phone/email/site and zero confirmed open trade packages.
- Never call all 267 entries unique leads, six profiles six verified buyers,
  project values available contract values, or planned dates actual completion.
- Agent knows Masiate's construction/remodeling, roofing, floors, painting,
  fencing, concrete, siding, plumbing, lighting and framing scope and the seven
  research counties. Research boundary is not verified willingness to travel.
- Agent uses saved Masiate facts before existing Jina tools. Only research and
  sources, no outreach, CRM, call scripts, report rewriting or scheduled crawl.
- Reopen the original saved chat for earlier research; no automatic cross-chat
  memory or guarantee of unlimited long-conversation recall. Preserve per-user
  history isolation, existing auth and budgets. Later research stays in chat.
- Match existing plain JS/CSS, shared shell and design. Use existing icons and
  assets, no marketing hero, new framework or decorative redesign. Escape
  untrusted record text and only render http/https source links.

## Implementation Evidence

Source package: `propertystack/data/masiate/pilot-20260920/`, including reviewed
properties, summary, coverage, three-item coordinator watchlist and the PDF.
The short watchlist is not the full collected watchlist. Company context is in
`docs/plans/masiate-decisions.md`; newer decisions above override earlier notes.
Shared shell is `site/js/app.js`; `site/js/chat-panel.js` exposes PSChatPanel
ask/deepDive and existing auth handling. Caddy has an explicit public-page
allowlist, so adding an HTML file alone will not deploy a reachable section.
`site/Dockerfile` builds from site/ and copies its files. The agent Dockerfile
builds from repo root but only includes selected CSVs in /opt/propertystack/data.
The Hermes propertystack plugin loads those CSVs into read-only SQLite and
remembers source URLs for the citation guard. Reuse these contracts, not a new
retrieval service. Do not mix Masiate rows into apartment software lead totals.

## Build Tasks

- [ ] MS1: Publish a deterministic Masiate web/agent data contract (15-25 minutes; foundation; no dependencies).
  Own `tooling/masiate_section/`, generated `site/data/masiate/`, `site/reports/masiate/`, `propertystack/data/masiate/kb/`, and focused exporter tests. Create a standard-library exporter from the committed pilot, producing sanitized web JSON and named CSV tables for properties, sources, contacts, coverage and company/report context. Preserve stable record IDs, membership, ranks, unknowns, source dates and roles; include only source-backed public fields. Copy the original PDF without regenerating it and verify its SHA-256 matches. Write the generated contract/schema for the next workers, including file names/columns and report URL. No source-runtime paths in any output. Counts must derive from records and summary. Test deterministic regeneration, matching 49/7/76/6/0 counts, duplicate/invalid-ID failures, malformed URLs and no private paths. Run baseline Check and focused tests, commit outputs and contract. Do not edit agent or page code.

- [ ] MS2: Build the public Masiate section and navigation (15-30 minutes; depends on MS1; parallel-safe with MS3).
  Own `site/masiate.html`, `site/js/masiate.js`, `site/css/masiate.css`, `site/js/app.js` navigation and `site/Caddyfile` route allowlist. Consume MS1 contract unchanged. Implement the compact ranked list and filters above, sources/contact evidence, real data dates, coverage and fixed report download. Use an accessible static/native detail expansion if needed. Company name visible at first glance. Handle loading, failed JSON, zero matches, keyboard focus, mobile and docked chat width without overlap. Provide data attributes/stable hooks for MS4 Ask actions but do not modify shared chat logic. Preserve all existing navigation behavior and apartment data. Verify public page/report status with Caddy when available, escape hostile fixture text, run Check and page checks; commit.

- [ ] MS3: Bake Masiate evidence into the existing agent (15-30 minutes; depends on MS1; parallel-safe with MS2).
  Own `chatbot/Dockerfile`, propertystack plugin SOURCE_NAMES/schema hints, `chatbot/hermes-profile/skills/query-propertystack/SKILL.md`, a narrowly scoped SOUL addition if necessary, and `chatbot/tests/test_masiate_knowledge.py`. Include MS1 CSVs in the baked read-only KB without replacing existing data. Explain source-backed context, available-business-route versus buyer distinctions, original report date, seven-county research boundary and unknown job availability. Give the agent stable IDs and source URLs for selected-record lookup, filtered comparisons and coverage questions. Prevent inclusion in state_leads/software counts; retain read-only SQL and source-link guard. Tests must build/load actual exported CSVs and prove lookups, county/contact counts, source links and old tables coexist without real model/Jina calls. Document no automatic PDF mutation or cross-chat recall. Run Check and plugin tests; commit.

- [ ] MS4: Connect section and selected-property questions to saved chat (15-25 minutes; depends on MS2 and MS3).
  Own Masiate Ask-button wiring and only necessary scoped changes to shared chat handling, with focused handoff tests. Provide a company-level Ask action and per-property Ask action sending company name, stable Masiate record ID, location, baseline date and a research question through the existing PSChatPanel/auth path. Use a Masiate-prefixed deep-dive/cache identity if using existing caches, and confirm no collision with apartment IDs or leak between users; prefer ordinary ask if the cache contract is unsuitable. Pending questions survive normal sign-in exactly once. Reuse saved chats; do not store cross-user research or change the PDF. Inspect the actual chat/proxy history path and test restored history with an isolated stand-in, clearly distinguishing that from a live provider test. Check long-history truncation behavior and document realistic limits rather than promising permanent memory. No live model spend. Run Check and focused handoff/auth regressions; commit.

- [ ] MS5: Verify the complete section on desktop and phones (15-30 minutes; depends on MS4).
  Own dedicated `tooling/qa/check-masiate-section.sh`, browser/data regressions and screenshots/review notes. Create a self-contained check with kernel-assigned ports, owned-process cleanup and no live AI calls; use the existing fake-webui pattern for auth/chat. Exercise navigation, 49 default entries, all county filters, search, no results/reset, six-contact filter, source URLs, report response/content/hash, Ask context, JSON failure/retry and hostile-text fixtures. Test desktop with docked chat and mobile at 390px plus narrow 320px: no horizontal overflow or covered controls, readable text, keyboard focus. Save representative screenshots and inspect them, not merely generate them. Run the existing panel/proxy suites for regressions. Replace this plan's top Check with the dedicated combined check once it works independently in under about two minutes. Do not soften assertions to mark done; fix in-scope defects, commit.

- [ ] MS6: Verify deploy packaging and hand off the local release candidate (15-30 minutes; depends on MS5).
  Inspect changes against the build's starting commit, run the final Check and all changed tests, verify Caddy serves the section/JSON/PDF without account login and chat retains existing auth. Verify actual site and chatbot image packaging with local Docker build/isolated containers when available; never touch shared production services, volumes or ports and do not send real provider requests. If Docker is unavailable, explicitly record the unverified image-startup check and do not claim fully verified deployment readiness. Confirm no external-runtime paths, new required credentials/subscriptions, report divergence or missing generated artifacts. Update local preview/run instructions with safe port handling, launch an owned preview on an unused port, open it via xdg-open when available and return its URL plus a short three-click walkthrough. Report actual verified versus unverified behavior, local branch/commit and which existing services need redeploying after Drew's later push. Never claim a Git push automatically deploys both services without inspecting project deployment configuration. Keep everything committed locally, give this parent thread the completion receipt and screenshots, and stop at human testing; no push/merge/deploy.

## Checks And Progress

The initial Check is the existing self-contained offline panel regression; each
task additionally runs its focused checks. MS5 makes the top-level check cover
the new feature so the final loop gate is not merely an old-page smoke test.
Write one concise entry per task into this plan's adjacent progress file with
the commit, exact check/results and remaining caveats. Never mark a task complete
based on a future task implementing its required behavior. Dependency groups:
MS1 -> [MS2, MS3] -> MS4 -> MS5 -> MS6. Initial estimate is 75-140 elapsed minutes,
not a deadline or measured result; report actual timing and blockers.

## How To Try It

1. Open Masiate from CraneSignal navigation and filter the list to one county.
2. Download the PDF and confirm its report date and property count match the section.
3. Ask about a property, verify the question names the correct project, then
   reopen the saved chat to continue; live answer quality is a later human test.
