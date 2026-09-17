# CraneSignal: AI Visibility v4 -- the real runs

Written 2026-09-15 with Drew. **Starts only when Drew explicitly says to run it** (this uses his
Claude and Codex plans and the Gemini key). Needs `PLAN-ai-visibility-v4.md` fully ticked.
Localhost only, never push.

Real AI calls happen only in this file. Keep the 7-second Gemini throttle; a stopped run resumes
(Google's daily cap may need a second start next day -- resume, don't restart). Never print, copy
or commit any key.

Run with: `Do the next unticked task in PLAN-ai-visibility-v4-run.md, then tick it and stop.`
Check: `bash tooling/qa/check-ai-visibility.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765/ai-visibility.html

## How to try it (30 seconds)
1. The report card shows real numbers from today's run, not "practice data".
2. "What AIs get wrong" lists real wrong claims, each with the correct fact and a source link.
3. The before / after section shows real re-asked answers.

## Tasks

- [ ] **R1 Smoke run.** `run.sh` with 5 questions x 1 ask on all 4 AIs (~20 answers). Confirm every
  AI answered, claims were checked and the page renders real data. Fix anything broken. Commit.
- [ ] **R2 Full run.** `run-and-report.sh` for real: ~40 questions x 3 asks x 4 AIs (~480 answers),
  then the claim checker and the before/after re-asks. Resume if stopped. Commit.
- [ ] **R3 Recap for Drew.** Open the page on localhost and check the numbers match the data. Post a
  plain-words recap: RealPage's AI market share vs rivals, areas it wins and loses, top 5 wrong
  claims, the before/after result, and the **draft headline sentence for Drew to approve or reword**.
  Do not push. Commit.
