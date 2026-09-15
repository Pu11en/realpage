# PropertyStack: AI Visibility v3 (a pro-style AI audit of RealPage)

Written 2026-09-15 with Drew. **Starts only when Drew says "go work".** Localhost only, never push.
Builds on v2 (`PLAN-ai-visibility-v2.md`, all done): Gemini answerer, run history, lawsuit data,
`run-and-report.sh`, "run AI visibility" in Discord. Keep all of that working.

Drew's answers:
- **The page is only about how AIs see RealPage and how RealPage could fix it.** No "how the tool is
  built" / engineering panels. Remove what reads as noise.
- **Pro audit format**, modelled on what Profound, Peec AI, Otterly, Semrush and Ahrefs deliver:
  (1) AI market share (share of voice) vs Yardi, Entrata, AppFolio, Buildium, ResMan, (2) mentioned vs
  cited (named vs realpage.com linked as a source), (3) position in the answer and tone, (4) trend over
  runs, (5) a to-do list tied to the exact websites Gemini quotes ("Gemini trusts G2 and this Reddit
  thread for screening questions; RealPage is absent there").
- **Richer data:** about 80 questions, each asked 3 times, so numbers are win rates, not coin flips.
- **Gemini only** (`gemini` from memory + `gemini-web` with Google Search), key in the repo-root `.env`,
  `gemini-2.5-flash`. No other AIs. Never print, copy or commit the key.
- On demand only; nothing pushes without Drew's "push it".

Gemini safety rules (every task): tests never call Gemini (fixtures only). Keep the 7-second throttle.
A full run is ~480 answers plus analysis calls, so it may hit Google's daily cap: **runs must resume** --
a stopped run keeps every saved answer and the next start continues where it left off. Only T8 makes
real Gemini calls.

Run with: `Do the next unticked task in PLAN-ai-visibility-v3.md, then tick it and stop.`
Check: `bash tooling/qa/check-ai-visibility.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765/ai-visibility.html

## How to try it (30 seconds)
1. Top of the AI Visibility tab: RealPage's AI market share next to Yardi, Entrata, AppFolio, Buildium and
   ResMan, plus "named in X% / cited in Y%" and a one-line verdict.
2. Middle: per product area (rent pricing, screening, accounting, ...) who Gemini recommends, how often,
   where RealPage sits in the answer and the tone; a short "questions RealPage is losing" list.
3. Bottom: a to-do list where every item names a real website Gemini quoted and what RealPage should do
   there.

## Tasks

- [ ] **T1 The question set (~80).** Grow `tooling/ai-visibility/questions.csv` to about 80 questions, keeping
  the 17 originals (same ids). Add columns `area` (rent pricing, resident screening, accounting, leasing /
  AI leasing, resident payments, utilities, affordable housing, student housing, senior living, platform
  overall) and `buyer` (small landlord <100 units, mid-size manager, large operator / REIT, affordable
  housing operator, any). Mix: mostly questions that do NOT name RealPage (buyer asking for a
  recommendation), plus comparisons and "is RealPage good for ..." questions. Plain buyer wording. Mark
  about 20 as `money=true` (the high-intent ones). Test that the file loads, has no duplicates and every
  area has at least 5 questions. Commit.
- [ ] **T2 Ask each question 3 times + resume.** `run.sh` / `frozen_audit.ts` ask every question 3 times per
  model (`AI_VIS_SAMPLES`, default 3; NiubiGEO's sample count if it has one, else the smallest wrapper).
  A run saves answers as it goes and, when restarted after a stop (429, daily cap, crash), skips answers
  already saved for that run. `--practice` uses 1 sample. Tests with the fake AI. Commit.
- [ ] **T3 Audit numbers.** In the builder, per run and per area / buyer / money set: **AI market share**
  (each company's mentions ÷ all six companies' mentions), **named %** and **cited %** (realpage.com URL in
  the answer or in gemini-web's sources), **average position** (1st, 2nd, ... company named),
  **top-pick win rate** per company, and **consistency** (share of questions where the 3 asks agreed on
  the top pick -- used only to mark shaky numbers on the page, not shown as a tech stat). Save in the run
  history file; older runs stay readable. Tests on fixtures. Commit.
- [ ] **T4 Tone per company.** One `gemini` JSON call per answer (batched, throttled) labels how the answer
  talks about each company named: positive / neutral / negative plus the short reason given (e.g.
  "praised for ease of use", "criticised for support"). Word-list fallback if the call fails. Roll up to
  a tone score per company and the top 3 praise and top 3 criticism reasons for RealPage. Keep the
  lawsuit data from v2 (it becomes part of RealPage's criticism reasons). Tests on fixtures. Commit.
- [ ] **T5 Sources Gemini trusts.** From gemini-web's grounding sources: websites quoted per area, how
  often, and for each site which companies the quoting answers named. Flag sites where rivals appear and
  RealPage doesn't, and realpage.com's own share of citations vs rivals' own sites. Resolve Google
  redirect links to the real domain (title fallback). Tests on fixtures. Commit.
- [ ] **T6 Source-based to-do list.** Build `site/data/ai-visibility-actions.json` from the data, not by
  hand: each item = a finding ("Gemini cites g2.com in 60% of screening answers; RealPage has 1/5 of
  the reviews Yardi has there" -- only facts the data supports), the website, what to do there, and
  priority (money questions and big gaps first). One `gemini` call drafts the plain-English wording from
  the facts; numbers are always filled in by code. Keep the checked realpage.com facts (llms.txt,
  sitemap, comparison pages, DOJ page) as their own group. Tests on fixtures. Commit.
- [ ] **T7 The page, audit format.** Rebuild `site/ai-visibility.html` (match the app's current design):
  (1) verdict line + AI market share bar vs the five rivals + named % / cited %, (2) per-area cards: who
  wins, RealPage's win rate, position, tone and top reason, shaky numbers marked "few answers", (3)
  "Questions RealPage is losing" (money questions first, with the winner), (4) trend of market share and
  win rate across runs (Sept 12 Claude/ChatGPT as a labelled baseline), (5) the to-do list grouped by
  website. Drop the old stacked lawsuit boxes (the lawsuit shows up as a criticism reason and in the
  to-do list) and anything that reads as tool internals. Plain empty states. Phone size works. Update the
  page check on practice data. Update `report.py` and `to_research.py` to the new numbers. Commit.
- [ ] **T8 First full real run.** Run `run-and-report.sh` for real (~480 answers, throttled, may need a
  second start next day if Google's daily cap is hit -- resume, don't restart). Open the page on localhost
  and confirm real numbers. Recap for Drew in plain words: RealPage's AI market share vs rivals, the areas
  it wins and loses, top praise / criticism, and the top 5 to-dos. Do not push. Commit.
