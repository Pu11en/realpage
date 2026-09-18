# AGENTS.md — PropertyStack project notes

## "Run AI visibility"

When Drew says "run AI visibility":

1. Run `bash tooling/ai-visibility/run-and-report.sh` inside `.worktrees/local-test` (the copy the
   localhost site serves). It asks the frozen questions to Gemini (memory + Google Search), rebuilds the
   AI Visibility tab and the chatbot's summary, and commits locally. Takes about 15–25 minutes.
2. Post the summary it prints (numbers vs last run, top lawsuit sources, localhost link) in plain words.
3. **Push only after Drew replies "push it".** Never schedule it; it runs only when he asks.

Gemini is the only AI for now (Claude/Codex plans are used up until later in Sept 2026); add
`claude,claude-web,chatgpt` back via `AI_VIS_MODELS` only when Drew says so.

## Site library, part 2 (Gemini step)

Part 1 (crawl public site + page index, no AI) was started as a
go-work loop on 2026-09-15. When Drew says he's ready for the Gemini step (any wording, e.g. "ready to
finish the library", "do the Gemini run now"): check part 1 is fully ticked and the shipcheck chatbot fixes (source-naming rule in SOUL.md) are merged, then start a
go-work loop on the site library part 2 plan (T5-T8: ~60-100 free Gemini calls for product
cards + key facts, then local chat hookup and test). Gemini use for that plan is pre-approved by Drew.

## AI Visibility v4 (queued)

`docs/plans/PLAN-ai-visibility-v4.md` (build on practice data, no real AI calls) starts as a go-work loop once
both site library plans are fully ticked -- when Drew says to start it or asks what's next after
the library. It is Drew's explicit exception to "task loops never touch AI Visibility".
`docs/plans/PLAN-ai-visibility-v4-run.md` (real Claude/Codex/Gemini runs, ~480 answers) starts only when Drew
explicitly says to run it. `docs/plans/PLAN-ai-visibility-v3.md` is superseded.
