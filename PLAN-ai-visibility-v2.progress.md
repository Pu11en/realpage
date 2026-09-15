## T1 Gemini answerer + the check — done (0f5dc1e)
- local_ai.py: models `gemini` (memory) and `gemini-web` (google_search grounding) via Gemini REST, gemini-2.5-flash, same public system prompt. Key from GEMINI_API_KEY env or repo .env, falling back to the main checkout's .env; never printed.
- Throttle: one Gemini call at a time, 7s apart. A 429 makes every later Gemini call fail fast and returns 429 to NiubiGEO.
- Structured (tool) calls through `gemini` ask for JSON output (responseMimeType); gemini-web can't combine search with JSON mode, so it relies on the schema prompt.
- gemini-web sources go to $AI_VIS_SOURCES (one line per answer: prompt, answer, sources url+title). run.sh sets it to a pending file and moves it into the run folder as gemini-sources.jsonl after the run.
- Tests: tooling/ai-visibility/tests (8, offline, fixtures in tooling/ai-visibility/fixtures). Check `bash tooling/qa/check-ai-visibility.sh` passes.
- Open: grounding URLs are Google redirect links; the title holds the website name (use title for the leaderboard in T4). NiubiGEO's reaction to a 429 is untested until T7.
