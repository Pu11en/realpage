# PropertyStack: AI Visibility v2 (Gemini runs on demand, trend lines, lawsuit story)

Written 2026-09-14 with Drew. **Starts only when Drew says "go work".** Localhost only, never push
during the build. Minimal styling (Drew does design himself). **RealPage only** -- no other companies' audits.

Drew's answers:
- **Gemini is the only AI for now.** Claude and Codex subscriptions are used up until later this month, and
  Drew wants no other AIs (no Perplexity, Grok, OpenRouter). Key: `GEMINI_API_KEY` in the repo-root `.env`
  (gitignored; worktrees fall back to `/home/drewp/main-projects/realpage/.env` like `tooling/dev.sh` does).
  Never print, copy or commit the key. Model: `gemini-2.5-flash`.
- **Gemini answers every question two ways:** `gemini` (from memory, no tools) and `gemini-web` (Google
  Search grounding on, keep the source URLs it returns).
- **Gemini gets its own trend line.** The 2026-09-12 Claude / ChatGPT results stay on the page as a
  labelled baseline next to it; Claude and ChatGPT come back later by adding them to the model list, no
  rebuild. Each AI is only ever compared with itself.
- **Same questions every run** so trends are fair: freeze the 2026-09-12 question list and reuse it.
- **Lawsuit section = all three, stacked:** (1) source leaderboard (which websites Gemini-with-search quotes
  when it raises the antitrust case, count per run, up/down vs last run, highlight realpage.com), (2) tone
  meter (each lawsuit mention labelled harsh / neutral / "it's settled now", mix per run), (3) quote wall
  (the actual sentences, newest first, with links).
- **On demand, never scheduled.** Drew types "run AI visibility" in a Discord RealPage thread; the session
  runs it on this machine, commits locally, posts the new numbers + the localhost link, and **pushes only
  after Drew replies "push it"**.

Gemini safety rules (every task): tests never call Gemini -- they use saved sample responses in
`tooling/ai-visibility/fixtures/`. At most 1 Gemini request every 7 seconds (free-tier friendly), stop
cleanly on a 429 and keep what was saved. Only task T7 makes real Gemini calls.

Run with: `Do the next unticked task in PLAN-ai-visibility-v2.md, then tick it and stop.`
Check: `bash tooling/qa/check-ai-visibility.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765/ai-visibility.html

## How to try it (30 seconds)
1. Open the AI Visibility tab: a trend chart shows "Gemini (memory)" and "Gemini + Google Search" lines for
   mentioned %, top pick % and lawsuit %, with the Sept 12 Claude / ChatGPT results shown as a labelled
   baseline, and a "last run: <date>" line at the top.
2. Scroll to the lawsuit section: a list of websites Gemini quotes (realpage.com highlighted), a
   harsh / neutral / settled bar, and a wall of real quotes with links.
3. In a Discord RealPage thread type "run AI visibility": a few minutes later the session posts the new
   numbers compared with last run and a localhost link, and nothing is pushed until you say "push it".

## Tasks

- [x] **T1 Gemini answerer + the check.** In `tooling/ai-visibility/local_ai.py` add models `gemini` and
  `gemini-web`, answered by the Gemini REST API (`generativelanguage.googleapis.com`, key from `.env`,
  `gemini-2.5-flash`, the same "member of the public" system prompt). `gemini-web` turns on the
  `google_search` tool and saves the grounding source URLs + titles per answer to a side file in the run
  folder (`gemini-sources.jsonl`, one line per answer). NiubiGEO's structured (tool/JSON) calls must also
  work through `gemini`. Add the 1-call-per-7-seconds throttle and 429 handling. List the new models in
  `do_GET`. Create `tooling/ai-visibility/tests/` with offline tests using fixtures, and
  `tooling/qa/check-ai-visibility.sh` (runs those tests with pytest; must work with no network and no key).
  Commit.
- [x] **T2 Frozen questions.** Save the question list from the 2026-09-12 real run
  (`~/.local/state/realpage-ai-visibility/runs/2026-09-12T15-39-48-714Z-realpage/prompts.csv`) into the repo
  as `tooling/ai-visibility/questions.csv`. Make `run.sh` reuse exactly those questions (use a NiubiGEO
  option if one exists; otherwise feed them in with the smallest wrapper) and default the models to
  `gemini,gemini-web`. `--practice` still works with the fake AI and the frozen questions. Test it. Commit.
- [x] **T3 Run history.** `site/data/build_ai_visibility.py` saves each run as
  `site/data/ai-visibility-history/<date>.json` (per AI: answers, mentioned %, top pick %, named first %,
  lawsuit %, missed questions, top picks by company) and a small `index.json` listing runs. Import the
  2026-09-12 run once as the baseline, labelled "Claude / ChatGPT, Sept 12". The existing tab data keeps
  working. Tests on fixtures; extend the check. Commit.
- [x] **T4 Lawsuit data.** From each run, pull every answer that raises the antitrust case / DOJ /
  settlement / price-fixing: the exact sentence(s), the AI, the question, and (for `gemini-web`) the source
  URLs. Label the tone harsh / neutral / settled with one extra `gemini` call per mention during real runs
  (fixture in tests; fall back to a simple word list if the call fails). Build the source leaderboard by
  website, with change vs the previous run and a flag for realpage.com. Save into the run's history file.
  Tests on fixtures. Commit.
- [x] **T5 The page.** `site/ai-visibility.html`: top line "last run: <date>, Gemini"; a trend chart per
  number (mentioned %, top pick %, lawsuit %) with one line per AI and the Sept 12 baseline as labelled
  points; then the lawsuit section stacked: source leaderboard, tone bar, quote wall (newest first, links).
  Keep the existing to-do list. Plain "one run so far" state when there is only one Gemini run. Works on
  phone size. Use the practice data to check it; extend the check to start the site on its own spare port,
  load the page and confirm the new sections render, then stop it. Commit.
- [x] **T6 "Run AI visibility" in Discord.** `tooling/ai-visibility/run-and-report.sh`: runs `run.sh`,
  builds, commits the new data on the current branch (never pushes), and prints a short plain summary: each
  number vs the last run, the top 3 lawsuit sources, and the localhost link. Add a short section to the
  repo's `AGENTS.md`: when Drew says "run AI visibility", run this script, post the summary, and push only
  after he replies "push it". Also refresh the chatbot's AI Visibility summary (`to_research.py`) from the
  newest run. Commit.
- [ ] **T7 First real Gemini run.** Run `run-and-report.sh` for real (about 100-150 Gemini calls on Drew's
  key, throttled). If Gemini rate-limits, keep what was saved and report how far it got. Open the page on
  localhost and confirm real numbers show. Recap in plain words for Drew: the new Gemini numbers, how they
  compare with the Sept 12 Claude / ChatGPT baseline, and the top lawsuit sources. Do not push. Commit.
