# Masiate Pilot: Coordinator Finalization

## Current State

Eight Codex workers were confirmed simultaneously running for the approved
roughly one-hour first pass. The bot had ten running sessions including this
coordinator and one unrelated worker. No /gowork cap or live bot setting changed.
The old stopped loop was not resumed. Existing /api/spawn sessions are the
execution route, with independent worktrees and nonoverlapping source ownership.

Read masiate-pilot-launch.json for exact worker IDs, paths and target times.
The statewide worker has a delivered queued instruction to relay once to this
parent thread when all lanes finish or the collection wrap target arrives.
That relay continues this coordinator for review and delivery, not a new pass.
Do not launch another worker or broad crawl when it arrives.

## On Completion

1. Read all eight status.json, records.json, coverage.json and summary.md files
   from the run root. Distinguish failed/missing/partial from empty/completed.
2. Confirm worker state via the sessions API. Use checkpoint snapshots if a
   worker is still finishing; tell it to wrap without killing unrelated work.
3. Combine records conservatively by source ID/location/project, retaining
   suites, phases, participants and all evidence; record duplicate decisions.
4. Select strongest relevant candidates, not a target count. Confirm source
   facts, jurisdiction, date, status, business-contact role and remaining unknowns.
   Older awards/expired bids are watchlist/history, never open work. Planned
   start/completion dates do not prove construction or availability.
5. Use actual downloaded evidence to validate every included profile. Page
   discovery alone is insufficient. Do not publish private homeowner contacts.
6. Generate the fixed first-pass PDF with detailed properties, linked sources,
   fit explanations, status uncertainty, contacts where verified, next research
   steps and seven-county coverage. Include an honest no-qualified-results
   report if none qualify; do not invent leads.
7. Produce matching sanitized JSON for eventual agent access and a concise
   Markdown coverage/results summary. No live site or agent integration.
8. Render PDF with existing WeasyPrint (import was verified), Playwright or
   bundled jsPDF; do not add paid services. pdfplumber, pypdf and pdftotext
   are available. Visually inspect representative/all layout types and check
   text extraction, page overflow, links and facts against the export.
9. Commit coordinator-owned scripts/tests and sanitized deliverables locally.
   Do not push, modify main or overwrite workers' worktrees; retain their raw
   evidence and commits. Use source-specific tests for any new parser logic.
10. Append the final PDF and Markdown results summary absolute paths to
    /home/drewp/main-projects/realpage/.ccdb-attachments-1551377360756940940
    so they appear in THIS thread. Do not attach raw personal data.

## Reporting And Stop

Report actual elapsed time, source-record count, distinct projects, detailed
shortlisted profiles, sourced business contacts and gaps, separately.
Explain that a first pass is not complete regional coverage. Mention successful
sources and specific blocked ones; avoid generic claims of all-data completion.
End this pass after delivery. Ask which next action Drew prefers, using real
findings to offer meaningful options; do not automatically spend another hour.
