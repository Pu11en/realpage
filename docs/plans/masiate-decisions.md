# Masiate Full Plan: Decision Interview

Check: `git diff --check`

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

## Feature Experience

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

## PDF Deliverable

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

## Current Question

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

Answer: pending. Public read access remains agreed; who may trigger research
or save shared edits will be resolved separately. Already-downloaded PDFs are
dated snapshots and cannot change retroactively.

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
