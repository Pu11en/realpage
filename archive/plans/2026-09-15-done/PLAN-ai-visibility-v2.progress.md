## T1 Gemini answerer + the check — done (0f5dc1e)
- local_ai.py: models `gemini` (memory) and `gemini-web` (google_search grounding) via Gemini REST, gemini-2.5-flash, same public system prompt. Key from GEMINI_API_KEY env or repo .env, falling back to the main checkout's .env; never printed.
- Throttle: one Gemini call at a time, 7s apart. A 429 makes every later Gemini call fail fast and returns 429 to NiubiGEO.
- Structured (tool) calls through `gemini` ask for JSON output (responseMimeType); gemini-web can't combine search with JSON mode, so it relies on the schema prompt.
- gemini-web sources go to $AI_VIS_SOURCES (one line per answer: prompt, answer, sources url+title). run.sh sets it to a pending file and moves it into the run folder as gemini-sources.jsonl after the run.
- Tests: tooling/ai-visibility/tests (8, offline, fixtures in tooling/ai-visibility/fixtures). Check `bash tooling/qa/check-ai-visibility.sh` passes.
- Open: grounding URLs are Google redirect links; the title holds the website name (use title for the leaderboard in T4). NiubiGEO's reaction to a 429 is untested until T7.

## T2 Frozen questions — done (8a8135c)
- tooling/ai-visibility/questions.csv: the 17 questions from the 2026-09-12 run (audit.json; prompts.csv only had ids), with type, topic, category, names-RealPage flag, and the original id as baseline_id. New ids q01..q17 because the Sept 12 ids repeated (three pairs shared an id).
- NiubiGEO's --prompts-file refuses questions that don't name RealPage (and marks them all "brand"), so tooling/ai-visibility/frozen_audit.ts builds the confirmed plan itself (same target, aliases, competitors) and runs NiubiGEO's AuditRunner. No discovery/keyword/question-generation calls, so Gemini only answers + analyses.
- run.sh uses it; models default to gemini,gemini-web (AI_VIS_MODELS overrides). --practice checked with a temp runs dir: 17 questions x 2 fake AIs = 34 answers, build ran. Restored site/data/ai-visibility.json after (practice had overwritten it).
- Tests: tests/test_questions.py (3). Check passes, 11 tests.
- Open: the keyword metrics (keywords.csv) are now empty since frozen plans carry no keywords; question ids differ from Sept 12, join by baseline_id or text in T3.

## T3 Run history — done (dbbecd1)
- build_ai_visibility.py now also saves each real run to site/data/ai-visibility-history/<date>.json (per AI: answers, failed, mentioned %, mentioned % on questions that don't name RealPage, top pick %, named first %, lawsuit %, missed questions, top picks by company; no full answers) and rewrites index.json (date, file, label, baseline flag, models). A second run on the same day replaces that day's file.
- Practice (--demo) runs skip history. `--baseline "<label>"` adds a run to history only and leaves ai-visibility.json alone; used once to import Sept 12 as "Claude / ChatGPT, Sept 12" (chatgpt, claude, claude-web). Existing tab data unchanged.
- Added gemini / gemini-web friendly names ("Gemini (memory)", "Gemini + Google Search"). Per-model entries in ai-visibility.json gained unbrandedMentionPct, missedQuestions, topPicks.
- Tests: tests/test_history.py (4) on fixtures/report-gemini.json (small hand-made Gemini report). Check passes, 15 tests.
- Open: T4 should add lawsuit data into the same history entry (history_entry/save_history).

## T4 Lawsuit data — done (6d0e43c)
- New site/data/ai_visibility_lawsuit.py: every answer (any question) with a sentence about the antitrust case / DOJ / lawsuit / settlement / price- or rent-fixing / collusion / state AGs becomes a mention: exact sentence(s), model + friendly name, question, namesBrand, tone, toneBy (gemini | words), and for *-web models the websites from gemini-sources.jsonl (matched by answer text, else by question in the prompt; website = title when it looks like a domain, deduped).
- Tone: harsh / neutral / settled. Real builds make one `gemini` JSON call per mention (local_ai.ask_gemini, so same 7s throttle; after a 429 it falls back). Fallback + --demo + --baseline + `--word-tone` use a word list (settle/resolved/agreed to → settled; price-fixing/collusion/alleg… → harsh; else neutral).
- Leaderboard: websites by number of mentions citing them, previous count + change vs the newest earlier non-baseline run with lawsuit data (null on the first run), dropped sites kept with count 0, isTarget for realpage.com.
- Saved as `lawsuit` {mentions, toneMix per model, sources, comparedWith} in each history file. ai-visibility.json unchanged (checked byte-identical).
- Sept 12 baseline re-imported with word-list tone: 10 mentions (claude 4 harsh/1 neutral, claude-web 2 harsh/3 settled), no sources (that run had no source file).
- Tests: tests/test_lawsuit.py (8) with fixtures/lawsuit-run + gemini-tone.json; test_history patches the tone call. Check passes, 23 tests.
- Open for T5: page reads history files' `lawsuit` (quote wall newest first = iterate history files by date desc). Word list is crude (e.g. an FTC screening settlement counts as "settled"); Gemini labels real runs.

## T5 The page — done (47573aa)
- site/ai-visibility.html now loads data/ai-visibility-history (index + run files; if missing, the old page still renders). Under the headline: "Last run: <date>, Gemini" (or "No Gemini run yet" while only the baseline exists), then three SVG trend charts (mentioned %, top pick % with no brand asked, lawsuit % on brand questions): one line per AI across its own runs, Sept 12 Claude/ChatGPT as hollow labelled points, legend with latest value. "One run so far" note when there is a single Gemini run.
- Lawsuit section (latest Gemini run): source leaderboard (bar per website, ▲/▼/same/new vs comparedWith run, realpage.com in accent + ★), tone bars per AI per run newest first (baseline included), quote wall of every mention newest run first with website links. Existing to-do list, tables and evidence all kept.
- Check: tooling/qa/check_ai_visibility_page.py (added to check-ai-visibility.sh) copies site/ to a temp folder, adds practice Gemini runs built from fixtures (word-list tone), serves on port 8794 (CHECK_AIVIS_PORT), Playwright at 1440 and 390 wide, once with one run and once with two; checks last-run line, chart points/lines, baseline in legend, one-run note, realpage highlight, tone bar, quotes + links, to-do list, no phone overflow, no script errors. Real site/ untouched. Check passes (~7s), 23 tests. Also eyeballed screenshots.
- Open: the real site shows the charts with only the baseline until T7's first Gemini run. The old "Tested <date>" meta line and stat cards still come from ai-visibility.json.
