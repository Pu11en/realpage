# CraneSignal: AI Visibility v4 -- "How AIs see RealPage, and how RealPage can fix it"

Written 2026-09-15 with Drew (thread 1549501531273961543). Replaces `PLAN-ai-visibility-v3.md` (never built).
Build part only: every task uses practice data and fake AIs. The real AI runs are a separate plan,
`PLAN-ai-visibility-v4-run.md`, which starts only on Drew's OK. Localhost only, never push.

**Starts after the realpage.com library is done** (`PLAN-realpage-site-library.md` and `-part2.md`
both fully ticked). This plan is Drew's explicit exception to "task loops never touch AI Visibility".
Builds on v2 (all done): `local_ai.py`, `run.sh`, `frozen_audit.ts`, run history, lawsuit data,
`run-and-report.sh`, "run AI visibility" in Discord. Keep all of that working.

Drew's answers:
- **Story:** buyer market share vs Yardi, Entrata, AppFolio, Buildium, ResMan **plus "what AIs get
  wrong about RealPage"**. Not a renter/reputation study.
- **"Wrong" means:** contradicts the realpage.com library (`01-company/realpage-key-facts.md`,
  `02-products/realpage/*.md`) or one of ~15 hand-checked facts (things RealPage's own site won't say,
  e.g. lawsuit outcomes). The session drafts and sources the 15 facts; Drew only skims them.
- **AIs (4 set-ups):** `claude-web` (Claude + web search), `chatgpt` (Codex; turn on its web search if
  the CLI supports it, else label "from memory"), `gemini-web` (Gemini + Google Search), `gemini`
  (Gemini from memory). Label each honestly on the page (these are the tools' engines, not the
  consumer apps). No DeepSeek, no GLM.
- **Size:** ~40 questions x 3 asks x 4 set-ups = ~480 answers.
- **Fix section = before/after proof:** write 2-3 real fix pages (a clear "RealPage facts" page and a
  fair RealPage-vs-Yardi comparison), give each to the AI with the question, show the answer change.
  Clearly labelled "simulation: what an AI says when it can read this page".
- **Page shape:** small report card on top (one headline sentence + 3 numbers: AI market share vs
  rivals, wrong claims found, before vs after the fix), then a scroll-down story: the problem ->
  real AI quotes -> what AIs get wrong -> the lawsuit chapter -> the fix -> the proof.
  Drew approves the headline wording before it is final.
- **Old sections:** lawsuit becomes a story chapter; the realpage.com checkup feeds the fix chapter;
  "how this was measured" becomes a small footnote. Drop the trend charts and per-AI panels.
- The page is only about how AIs see RealPage and how to fix it -- no tool-internals panels.

Safety rules (every task): tests never call any AI or the network (fixtures and `fake_ai.py` only).
Keep the 7-second Gemini throttle. Runs must resume: a stopped run keeps every saved answer.
No task in this file makes a real AI call. Never print, copy or commit any key.

Run with: `Do the next unticked task in PLAN-ai-visibility-v4.md, then tick it and stop.`
Check: `bash tooling/qa/check-ai-visibility.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765/ai-visibility.html

## How to try it (30 seconds)
1. Top of the page: a report card with one headline sentence and three numbers (market share vs
   rivals, wrong claims, before vs after the fix) -- on practice data, marked "practice data".
2. Scroll: real-looking AI quotes, a "what AIs get wrong" list (each wrong claim next to the correct
   fact and its source link), and a lawsuit chapter.
3. Bottom: the fix page excerpt with a side-by-side "before / after" AI answer, then a one-line
   method footnote.

## Tasks

- [ ] **T1 Question set (~40).** Rework `tooling/ai-visibility/questions.csv` to about 40 questions,
  keeping the 17 originals (same ids). Add columns `area` (rent pricing, resident screening,
  accounting, leasing / AI leasing, resident payments, utilities, affordable housing, platform
  overall), `buyer` (small landlord, mid-size manager, large operator / REIT, affordable operator,
  any) and `money` (true for ~10 high-intent ones). Mostly questions that do not name RealPage, plus
  comparisons and "is RealPage good for ..." questions; plain buyer wording. Test: loads, no
  duplicate ids, every area has 3+ questions. Commit.
- [ ] **T2 Four AIs, 3 asks each, resume.** Default `AI_VIS_MODELS` to
  `claude-web,chatgpt,gemini-web,gemini` in `run.sh` (Gemini-only still possible via the variable).
  Check whether `codex exec` can search the web; if yes add it to `chatgpt`, if no keep it and set its
  page label to "ChatGPT engine (from memory)". Each question asked `AI_VIS_SAMPLES` times (default 3;
  `--practice` = 1). Saving as it goes; a restarted run skips answers already saved for that run.
  Tests with the fake AI. Update the repo `AGENTS.md` "Run AI visibility" note. Commit.
- [ ] **T3 The 15 checked facts.** Write `09-ai-visibility/checked-facts.md`: ~15 facts an AI is
  likely to get wrong about RealPage (DOJ and state lawsuit status and settlements, product renames
  and retirements, major acquisitions, headquarters, ownership, flagship product names), each with
  date and 2 independent source links (court records, major news, realpage.com). Research with the
  web tools already on the machine (Jina first, Brave only if needed; no AI calls). Mark anything
  uncertain "unconfirmed" instead of guessing. Commit.
- [ ] **T4 Claim checker.** `tooling/ai-visibility/claims.py`: for each answer that names RealPage,
  one `gemini` JSON call pulls its factual claims about RealPage, then compares each claim with
  `checked-facts.md` and the library files, labelling it correct / wrong / outdated / can't check,
  with the fact and source it was compared against. Throttled, resumable, batched. Roll up: wrong
  claims per AI, top wrong claims with how many answers repeated them. Tests on fixture answers and a
  fake AI (no library needed in tests -- use fixture fact files). Commit.
- [ ] **T5 Market-share numbers.** In `build_ai_visibility.py`, per run and per area / buyer / money
  set: AI market share (each company's mentions / all six companies' mentions), top-pick win rate per
  company, named % and cited % (realpage.com link in the answer or in gemini-web's sources), average
  position, and a "shaky" flag where the 3 asks disagreed on the top pick. Old runs stay readable.
  Tests on fixtures. Commit.
- [ ] **T6 Fix pages.** Write `09-ai-visibility/fixes/realpage-facts.md` and
  `09-ai-visibility/fixes/realpage-vs-yardi.md` (optional third: the area RealPage loses most on
  practice data, e.g. screening), built only from the library and `checked-facts.md`, fair to rivals,
  every claim with its source link -- written as pages RealPage could actually publish. Commit.
- [ ] **T7 Before/after harness.** `tooling/ai-visibility/before_after.py`: picks up to 8 questions
  RealPage lost or where an AI got a fact wrong, asks the same AI again with the matching fix page
  given as reading material, and saves before vs after (winner, RealPage named?, wrong claims fixed?).
  `site/data/ai-visibility.json` gets a `beforeAfter` block. Tests with the fake AI. Commit.
- [ ] **T8 Page: report card + first chapters.** Rebuild the top of `site/ai-visibility.html` (match
  the app's current design): report card (headline sentence from a template filled by code, marked
  "draft headline -- Drew to approve"; 3 numbers), chapter 1 "What buyers are told" (market share bar
  vs the five rivals, areas RealPage wins / loses, shaky numbers marked "few answers"), chapter 2
  "In the AIs' own words" (3-5 short real quotes with AI name and date). Practice data works; phone
  size works. Commit.
- [ ] **T9 Page: wrong facts, lawsuit, fix, proof.** Chapter 3 "What AIs get wrong" (wrong claim ->
  correct fact -> source link, most repeated first), chapter 4 the lawsuit (how often AIs raise it,
  tone, the sources they quote -- from the v2 lawsuit data), chapter 5 "The fix" (fix page excerpts
  plus the realpage.com checkup items: llms.txt, sitemap, comparison pages, DOJ page), chapter 6
  "Proof" (before / after answers side by side, labelled simulation). Method footnote. Remove the old
  trend charts, per-AI panels and stacked lawsuit boxes. Plain empty states. Update
  `tooling/qa/check_ai_visibility_page.py`. Commit.
- [ ] **T10 Reports follow the page.** Update `report.py` (the Discord recap) and `to_research.py`
  (the chat's summary in `09-ai-visibility/`) to the new numbers: market share, wrong claims, top
  wrong claims, before/after. Tests on fixtures. Commit.
