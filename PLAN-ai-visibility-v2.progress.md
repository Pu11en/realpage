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
