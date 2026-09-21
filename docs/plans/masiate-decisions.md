# Masiate Full Plan: Decision Interview

Check: `git diff --check`

## Current Deliverable: Top-Property PDF

Latest direction from Drew on 2026-09-20 supersedes the earlier all-leads PDF
and per-lead saved-note decisions below.

- **Primary deliverable:** a PDF of the best properties/projects for Masiate,
  with as much useful, source-backed detail as can be found on each.
- Collect broadly across relevant services, rank candidates, then concentrate
  deeper research on the strongest properties. The report is a selected set,
  not an automatic dump of every collected record.
- Proposed property profile: address/map link, what is planned or happening,
  matching Masiate work, owner/developer/builder roles, available business
  contacts, known scope/budget, dates/stage, evidence, uncertainty and a useful
  next step. Project budget must not be presented as Masiate's contract value.
- Keep the public CraneSignal section and agent access to the underlying data.
  The report is the main outcome; chat supports further investigation.
- Agent research happens on request and stays in the person's saved chats;
  the agent must retrieve prior findings when that person asks again.
- **Cancel separate per-lead notes, note visibility controls and shared-record
  edits.** The latest user instruction makes the previous Q7 unnecessary.
- The PDF stays unchanged by chat research. Later editions from new collection
  runs remain undecided.
- Remembering requires persisted chat history and retrieval, not an assumption
  of automatic model memory. Inspect the existing chat/session behavior before
  promising return-visit or cross-chat recall; keep each person's history scoped
  to them even though the section is public.
- Property count is flexible: select by quality and available evidence, with no
  fixed quota or padding. This is not authorization for unlimited research cost.
- Geographic boundary, ranking acceptance rules and depth of each profile
  still need planning. No collection/build has started.

## Confirmed Instructions

- Plan the full experience before building; Drew explicitly requested an interview.
- Ask one short question at a time with meaningful options and a recommendation.
- Research factual questions ourselves; ask Drew for business decisions.
- Record answers and revisit them only when new evidence creates a conflict.
- Regular public section inside the existing CraneSignal application.
- Lead collection for Masiate across its relevant construction services.
- The existing agent must have the same sourced information.
- Planning stays in this session's worktree; no independent app or repository.
- No crawl implementation, paid workers, outreach or deployment starts during this interview.

## Existing Research

[First crawl research](masiate-first-crawl.md) is a provisional source design,
not an approved full product/build plan. Suggested areas, collection windows,
ranking rules, cadence and task order remain proposals until resolved here.
The prior area question has no recorded answer.

## Decision Tree

- [ ] Outcome: who uses a lead, who contacts the prospect, and what success means.
- [ ] Business fit, after outcome: priority work, capacity, project size and jobs to exclude.
- [ ] Geography, after business fit: service base, travel boundary and expansion order.
- [ ] Evidence, after fit/geography: what qualifies as a lead, freshness, unknowns and contact requirements.
- [ ] Collection, after evidence: sources, history, refresh frequency, access gaps and completion measures.
- [ ] Workflow, after outcome/evidence: review, assignment, contact handoff, follow-up and outcome tracking.
- [ ] Public section, after workflow: audience, views, fields, filters and what is publicly displayed.
- [ ] Agent, after evidence/workflow: questions it answers, sources, uncertainty and permitted actions.
- [ ] Operations, after collection: provider costs, usage limits, failed runs and maintenance ownership.
- [ ] Acceptance, after product scope: representative examples, failure cases and local checks.
- [ ] Build handoff, after acceptance: small tasks, dependencies, /gowork versus normal session, model choice if relevant.
- [ ] Final walkthrough: reconcile contradictions and obtain Drew's explicit instruction to begin building.

The next question comes from an unresolved decision whose prerequisites are
settled. Keep optional later enhancements out of the first build unless selected.
Use the existing research instead of repeating source discovery.

## Answered Questions

Q1: Who will turn the leads into actual jobs?

- A. Masiate's owner contacts prospects directly; recommended simplest initial workflow.
- B. A Masiate salesperson or office team handles outreach.
- C. Drew's team checks interest first, then passes interested prospects to Masiate.
- D. Drew's team and Masiate share the work and assign follow-ups to each other.

Answer: **A**, selected by Drew on 2026-09-20. Masiate's owner contacts
prospects directly. This does not authorize automated outreach or imply that
the system has already verified a prospect's interest.

Q2: Which jobs should appear at the top of the owner's lead list?

Collection remains broad across relevant services; this decision sets priority.

- A. Best opportunities across all services: prioritize local, fresh, well-supported
  matches; recommended for the requested broad coverage, with a mixed daily list.
- B. Fencing and concrete for builders: prioritize portions of larger projects.
- C. Homeowner remodels: prioritize kitchens, bathrooms, additions and similar work.
- D. Commercial renovations: prioritize shops, offices and other business premises.
- E. Whole-house builds: prioritize opportunities to lead a complete home project.

Answer: **A**, selected by Drew on 2026-09-20. Rank the best matches across
all relevant services; no single trade gets exclusive collection priority.

## Interview Correction

Drew wants questions about the final feature and deliverable, not a sales
strategy interview. Lead with concrete user-visible behavior and scope choices.
The earlier decision tree is a topic checklist, not a requirement to exhaust
business questions before discussing the product. Resolve travel/capacity only
when needed for an actual feature behavior, without revisiting broad coverage.

## Earlier Feature Choice

Q3: What should the finished CraneSignal section let the owner do?

- A. Find leads, inspect the work/contact/evidence, ask the agent, and track
  contacted/quoting/won; recommended complete workflow, with more features to build.
- B. Search, inspect, ask the agent and export leads; handle follow-up elsewhere.
- C. Work through a prioritized daily list with next actions and reminders;
  prioritize a guided workflow over exploring the whole database.
- D. Ask the agent to research opportunities and build saved shortlists;
  prioritize conversation over a table-led workflow.

All options retain a regular public section and shared sourced agent knowledge.
Personal notes or follow-up visibility, if selected, remain a later explicit
design decision; a public section does not automatically mean public sales notes.
Answer: **D**, selected by Drew on 2026-09-20. Agent-led research and saved
shortlists are the main experience. Do not assume a full sales-tracking system
was selected. The regular public CraneSignal section remains agreed.

Drew also requested "a pdf of everything" and wants to explore the feature
further. Q4 below resolves this as a feature export of the complete lead report.

## Earlier PDF Choice: Superseded

Q4: What should "a PDF of everything" contain?

- A. A complete lead report: overview, every lead in the selected collection,
  project details, known business contacts, fit reasons, source links, dates and
  gaps; recommended complete takeaway, potentially a long document.
- B. A chosen shortlist with those details: a smaller working document based on
  the owner's selected leads.
- C. The agent's research session: questions, findings and supporting sources,
  rather than every record in the collection.
- D. The full feature/build plan as a PDF for Drew now, rather than a future
  lead-report export.

Answer: **A**, selected by Drew on 2026-09-20 and repeated after an interrupted
turn. The feature must export a complete lead report: overview, every collected
lead in the selected collection, project details, available business contacts,
fit reasons, dates, source links and information gaps. This is not a request to
generate a planning PDF now. Do not silently replace all leads with a top-N
shortlist, omit unknown fields without explanation, or invent missing facts.

## Agent Research Scope

Q5: How far should the agent go beyond the information already collected?

- A. Answer from saved data and research a selected lead online when asked;
  recommended balance of useful investigation, speed and controllable cost.
- B. Use collected data only; fast and predictable, with missing facts left open.
- C. Automatically check live sources while answering; fresher evidence, with
  longer waits and higher potential usage cost.
- D. Also launch new searches for additional leads; broader discovery with
  longer-running jobs and more usage to manage.

Answer: **A**, selected by Drew on 2026-09-20. The agent answers from collected
data and researches a selected lead online when explicitly asked. Automatic
live checks on every question and new broad collection runs from chat are not
selected. Scheduled collection remains a separate open decision. This is a
future capability, not authorization to spend on live research during planning.
Outreach remains with the owner under Q1.

## Superseded Save Question

Q6: When the agent discovers new information about a lead, how should it be saved?

- A. Show the finding and source, then let the owner save it to the lead record;
  future full PDF exports include saved updates. Recommended owner control,
  with a review step.
- B. Automatically add source-backed findings to the shared lead record and
  future PDFs; less manual work, with automated validation and change history.
- C. Keep findings in the research conversation only; the shared record and
  full collection PDF remain based on the collector's dataset.
- D. Save a dated research appendix alongside the lead; include it in future
  PDFs while preserving the collector's original fields.

Answer: no option selected. Drew clarified that the complete PDF stays fixed;
the agent helps find more information but does not write that research back to
the PDF. Drew asked how difficult option A would be. The earlier choices that
fed agent updates into future PDFs are superseded by this clarification.

## Earlier Save Design: Superseded

- Confirmed: keep the original complete collection PDF unchanged by agent research.
- New findings appear in chat and can be saved as separate notes attached to a
  lead, as confirmed in Q6 revised; note visibility is still open.
- Any later report edition from a new collection is a separate, unresolved
  product decision, not an automatic consequence of asking the agent questions.
- Saving a finding is feasible, but needs persistent storage, a save action,
  retrieval on return visits and clear editing permissions. The current agent
  data tools are read-only, so shared-record updates require additional work.
- A separate saved note can preserve source/date without changing the original
  collector record or PDF. No precise delivery estimate has been promised.

## Earlier Lead Notes: Canceled

Q6 revised: With the PDF fixed, how should extra research be kept?

- A. Save useful findings as notes attached to each lead; recommended reusable
  research without overwriting the original record, with some additional build work.
- B. Keep research in saved chat conversations; simpler, but findings are less organized.
- C. Download a separate research note; portable, without in-app saved findings.
- D. Save changes into the shared lead record itself; richer integration, with
  more work for validation, edit permissions and history; PDF still unchanged.

Answer: **A**, selected by Drew on 2026-09-20 before an interrupted turn.
Save useful research findings as notes attached to each lead. Preserve the
original collected record and fixed PDF. Visibility and editing permissions
remain undecided; this answer does not select shared-record editing.

## Canceled Visibility Question

Q7: Who should see research notes saved on a lead?

- A. Everyone viewing the public section; recommended match for shared public
  research, with only source-backed project findings published as research notes.
- B. Only the person who saved them; the leads and original PDF remain public.
- C. Masiate's selected team; research is shared among team members.
- D. Choose public or personal when saving each note; more flexibility and controls.

Canceled by Drew's latest instruction: research stays in saved chat history,
so do not ask who can see separate lead notes or build note controls.

## Report Length

Q8: How many top properties should the first detailed PDF cover?

- A. Up to 20: recommended focused report with substantial research per property.
- B. Up to 10: a smaller, more deeply investigated first selection.
- C. Up to 50: broader choice, with more research and a longer report.
- D. Up to 100: extensive coverage, with the most work and a much larger report.

Answer: **Does not matter**, stated by Drew. Use judgment on count and report
length based on meaningful, well-supported opportunities. Do not impose the
suggested 20-property limit or ask for another number. Keep research budgets
and source coverage as separate decisions; no unlimited spend is implied.

## Current Question

Q9: Which area should the PDF's properties cover?

- A. The wider Brazos Valley: recommended for broad coverage around the stated
  service region, with more sources and potentially farther-away properties.
- B. Bryan and College Station only: concentrated report, fewer jurisdictions.
- C. Brazos and Robertson counties: both cities plus Hearne and nearby areas.
- D. A chosen travel radius from Masiate's base: user provides town and limit.

Answer: pending. Wider Brazos Valley is a proposed collection area, not a claim
that Masiate accepts work in every town. The earlier area question remains
unanswered; do not assume DFW or statewide coverage.

## Product Questions To Explore Next

- What the agent can actually do: search collected records, verify live sources,
  research a new opportunity, compare jobs, and suggest a next step.
- What a useful answer contains and what happens when evidence or a contact is
  missing; demonstrate with a clearly hypothetical example before building.
- How the user opens, saves, revisits and exports research; public visibility
  and persistence are not yet decided beyond the section itself being public.
- Whether data refresh is scheduled, requested by the user, or both; report
  freshness and collection coverage must be visible.
- A first-use walkthrough and concrete acceptance checks for the chosen output.

## Build Boundary

Planning answers are decisions, not commands to start a build. Once the complete
plan is reviewed, choose the execution method and start only when instructed.
The usual /gowork option runs small checked tasks in fresh sessions; a normal
session remains an option. No loop has been created or queued.
