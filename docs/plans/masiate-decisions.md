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
- The section shows a short ranked property list, the detailed PDF and an Ask
  Agent action. Full on-site property profiles and map browsing are not selected.
- Agent research happens on request and stays in the person's saved chats;
  reopen the original saved chat to ask about its earlier findings. Drew
  delegated this detail; the assistant chose existing-chat continuity for the
  first version, without automatic search across different conversations.
- Agent scope is research only: facts, sources and available business contacts.
  No outreach-message drafting or call briefs; Masiate handles preparation and
  contact itself. Nothing is sent to prospects by the system.
- **Cancel separate per-lead notes, note visibility controls and shared-record
  edits.** The latest user instruction makes the previous Q7 unnecessary.
- One initial collection/research run and one fixed PDF are selected. No
  scheduled crawling, recurring editions or broad report-refresh feature in
  the first version. The agent still researches a selected lead on request.
- Show the report and dataset dates; later chat findings have their own dates
  and do not rewrite the report or imply the baseline has refreshed.
- Remembering requires persisted chat history and retrieval, not an assumption
  of automatic model memory. Inspect the existing chat/session behavior before
  promising return-visit recall; verify earlier findings can actually be used
  after reopening, including long conversations. Keep each person's history
  scoped to them even though the section is public; cross-chat recall is excluded.
- Property count is flexible: select by quality and available evidence, with no
  fixed quota or padding. This is not authorization for unlimited research cost.
- Use existing CraneSignal services, including already-paid access, plus useful
  open-source tools. No new subscriptions, paid datasets, credit purchases or
  unapproved overages. Verify allowances before collection; a configured key is
  not proof of a paid balance. See [tool research](masiate-tool-research.md).
- Geographic scope: wider Brazos Valley, covering Brazos, Robertson, Burleson,
  Grimes, Leon, Madison and Washington counties. Source coverage must be checked
  separately for each jurisdiction; this is a collection boundary, not proof of
  Masiate's willingness to travel to every property.
- Assistant ranking default: recent relevant work, evidence quality and an
  identifiable business contact first; distinguish likely need from an explicit
  open request for bids. Deeper profile acceptance checks still need planning.
  No collection/build has started.

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
The area question is resolved in Q9: wider Brazos Valley.

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

## Collection Area

Q9: Which area should the PDF's properties cover?

- A. The wider Brazos Valley: recommended for broad coverage around the stated
  service region, with more sources and potentially farther-away properties.
- B. Bryan and College Station only: concentrated report, fewer jurisdictions.
- C. Brazos and Robertson counties: both cities plus Hearne and nearby areas.
- D. A chosen travel radius from Masiate's base: user provides town and limit.

Answer: **A**, selected by Drew on 2026-09-20. Cover the wider Brazos Valley:
Brazos, Robertson, Burleson, Grimes, Leon, Madison and Washington counties.
The source inventory must cover selected cities and unincorporated areas,
recording gaps instead of treating Brazos-only results as region-wide coverage.
DFW and statewide collection are outside this chosen boundary.

## Report Frequency

Q10: After the first PDF, when should the system collect again and make a new report?

- A. Weekly new editions, with refreshed data for the agent; recommended useful
  cadence without generating a daily report that may repeat the same properties.
- B. One initial report; the agent can investigate it on request, with no
  scheduled broad collection or report generation.
- C. New collection/report only when an authorized user requests a refresh;
  control over timing, with a wait while the job runs.
- D. Daily new editions and refreshed data; more frequent checking and work,
  even when official sources have not published new records.

Answer: **B**, selected by Drew on 2026-09-20. Produce one initial report and
let the agent investigate its leads on request. No scheduler, recurring PDF
generation or user-triggered whole-report refresh is part of the first version.
The collected dataset/report must show their dates to avoid claiming freshness
that only an individual chat lookup has established.

## Ranking Default

Q11: What should put a property near the top of the report?

- A. Best chance of useful near-term outreach: recent matching work and an
  identifiable buyer; recommended actionable ranking, without claiming hiring
  intent or a probability of winning the job.
- B. Largest relevant potential jobs: emphasize scope/value even if the sale
  takes longer; whole-project budget is not Masiate's contract value.
- C. Earliest warning: properties still in planning, with longer lead times.
- D. Repeat-work potential: properties tied to builders/owners with multiple
  projects, emphasizing relationships rather than a single immediate job.

User answer: **Idk**. No option was selected. Assistant will use a practical
default: prioritize relevant, recent projects with clear evidence and an
identifiable business contact. Keep early opportunities and repeat-work
potential as secondary signals. Do not rank purely by total project value.

Separate documented open bids from inferred trade needs, explain why each
property ranks well, and retain unknowns rather than inventing hiring intent.
Missing contacts do not automatically erase otherwise promising properties.
Treat this as an assistant planning default, not a claimed user preference or
a calibrated prediction of sales success. No need to re-ask for scoring weights.

## Agent Outreach Boundary

Q12: Beyond researching a property, what should the agent help the owner prepare?

- A. A tailored first-contact message based on known facts; recommended practical
  next step, with the owner reviewing and sending it.
- B. Research answers only; the owner handles all outreach preparation.
- C. A call briefing with what is known and questions to ask; no written message.
- D. Both a first-contact message and call briefing on request; broader assistance.

Answer: **B**, selected by Drew on 2026-09-20. Keep the agent focused on research
answers, evidence and available business contacts. Outreach preparation belongs
to the owner; message drafting and call briefs are outside this feature's scope.
No sending messages, contacting prospects or inventing company qualifications,
relationships, price quotes or confirmed work availability.

## Collection Tools And Spending

Q13: What spending rule should apply to collecting information for the first PDF?

- A. Free public sources first; recommended starting point, with paid-only gaps
  clearly marked instead of purchasing access.
- B. Allow paid sources within a budget Drew specifies before any spending;
  potentially more coverage, but a firm cap and cost checks are required.
- C. Use existing subscriptions only where their included allowances and access
  are verified; no new subscriptions, purchases or overage charges.
- D. Compare free and paid coverage first, then decide whether paid access is
  worthwhile; no purchase while preparing that comparison.

Answer: **Existing services plus open source**, clarified by Drew on 2026-09-20.
Use what CraneSignal already has, including Jina AI and already-paid tools;
research useful open-source additions. Do not buy new services or credits.
This is broader than free sources alone, closest to C, but no exact letter was
chosen. It does not authorize implementation or a live collection run yet.
Verify remaining allowances and billing behavior before using paid endpoints;
stop or use a no-new-charge alternative if an extra charge would be required.
No unlimited token budget or provider billing cap is assumed.

## Public Section Experience

Q14: Besides downloading the PDF, what should visitors see in Masiate's section?

- A. A short ranked property list and an Ask Agent action; recommended useful
  preview while keeping the detailed PDF the main deliverable.
- B. The PDF and agent only; smallest section, with property browsing in the PDF.
- C. Full searchable property profiles on the website too; more convenient
  browsing, with a larger interface to build and test.
- D. A map with property summaries, PDF and agent; geographic browsing, requiring
  verified locations and a map source with no new charges.

Answer: **A**, selected by Drew on 2026-09-20. Show a short ranked property list
with PDF access and an Ask Agent action. Keep the detailed PDF as the primary
deliverable, rather than duplicating every property profile on the website.
Map browsing and full searchable web profiles are not part of this first version.
The regular public section and user-scoped saved chats remain as selected.

## Next Walkthrough

The core product choices are now recorded. Move from preference questions to
demonstrating the proposed experience and checking the plan's remaining gaps.

Q15: Which part should we walk through first before building?

- A. The complete experience from opening the section to returning to a saved
  research chat; recommended to expose missing steps across the whole feature.
- B. One clearly hypothetical property profile showing the PDF's level of detail.
- C. The collection run: where records come from, how they become ranked leads,
  and what happens when a source is unavailable.
- D. The agent: example questions, sourced answers and retrieving earlier research.

Answer: **A**, selected by Drew on 2026-09-20. The complete proposed experience
is written in [the walkthrough](masiate-experience-walkthrough.md), including
failure states and checks. This chooses a planning walkthrough, not approval of
every newly proposed detail or authorization to build.

## Returning To Research

Q16: When someone asks about earlier research, where should recall work?

- A. In any new chat, search that person's previous chats automatically;
  recommended match for the requested experience, with extra retrieval work.
- B. In the original saved chat after they reopen it; simplest implementation,
  without automatic cross-chat recall.
- C. Let them choose a previous chat to use in a new conversation; explicit
  control over the research carried forward.
- D. Asking about a property reopens its earlier conversation; property-linked
  continuity without general history search.

Answer: **Delegated to the assistant**, on 2026-09-20. Drew said this detail
does not matter and to choose. Assistant default: **B**, reopen the original
saved chat and continue there. This is not a claimed explicit letter selection.
Reuse the existing saved-chat experience; no automatic cross-chat search,
separate memory database or property-to-conversation routing in version one.
Verify persistence, restored context and user isolation before calling it done;
stored messages alone do not prove older findings reach the agent in long chats.
Keep the PDF unchanged and add no separate lead notes. Do not re-ask this choice
unless a verified limitation makes the selected behavior unworkable.

## Product Questions To Explore Next

- What the agent can actually do: search collected records, verify live sources,
  research a new opportunity, compare jobs, and suggest a next step.
- What a useful answer contains and what happens when evidence or a contact is
  missing; demonstrate with a clearly hypothetical example before building.
- How the user opens, saves, revisits and exports research; public visibility
  and persistence are not yet decided beyond the section itself being public.
- How dated baseline facts and newer chat findings are distinguished; report
  date and collection coverage must be visible, with no recurring refresh.
- A first-use walkthrough and concrete acceptance checks for the chosen output.

## Build Boundary

Planning answers are decisions, not commands to start a build. Once the complete
plan is reviewed, choose the execution method and start only when instructed.
The usual /gowork option runs small checked tasks in fresh sessions; a normal
session remains an option. No loop has been created or queued.
