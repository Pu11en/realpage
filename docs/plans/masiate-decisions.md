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

## Current Question

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
Answer: pending; Drew may combine outcomes or describe another deliverable.

## Build Boundary

Planning answers are decisions, not commands to start a build. Once the complete
plan is reviewed, choose the execution method and start only when instructed.
The usual /gowork option runs small checked tasks in fresh sessions; a normal
session remains an option. No loop has been created or queued.
