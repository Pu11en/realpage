# AGENTS.md — RealPage / PropertyStack project notes

## "Run AI visibility"

When Drew says "run AI visibility" (in any RealPage Discord thread):

1. Run `bash tooling/ai-visibility/run-and-report.sh` inside `.worktrees/local-test` (the copy the
   localhost site serves). It asks the frozen questions to Gemini (memory + Google Search), rebuilds the
   AI Visibility tab and the chatbot's summary, and commits locally. Takes about 15–25 minutes.
2. Post the summary it prints (numbers vs last run, top lawsuit sources, localhost link) in plain words.
3. **Push only after Drew replies "push it".** Never schedule it; it runs only when he asks.

Gemini is the only AI for now (Claude/Codex plans are used up until later in Sept 2026); add
`claude,claude-web,chatgpt` back via `AI_VIS_MODELS` only when Drew says so.
