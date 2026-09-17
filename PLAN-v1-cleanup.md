# CraneSignal v1: clean the project and certify the release

Goal: the code we already have is clean and professional — a clear README, no leftover planning
clutter at the top level, simple code in the two live services and the data tools, honest tests —
and the result is tagged `v1.0`. Nothing new is built.
Done when: every task below is ticked, Check passes, the live site and chat still work, and
`git tag v1.0` is pushed.

Written 2026-09-17 (thread 1549874755622928477). Drew's words: "just clean up the codebase ...
make it clean ... then tag it version one." Interview material is a separate, later session — do
not write anything interview-flavoured here.

Method for the code tasks (V3, V4, V5): use the `simplify` skill on the folder named in the task
(it reviews the changed code for reuse, simplification, efficiency and then applies the fixes).
Then hand-check the result against the rules below before committing.

Rules for every task:
- **Behaviour must not change.** This is tidying, not redesign. If a cleanup would change what the
  site or the agent does, don't do it — write it in the progress file instead.
- Delete nothing that the running services read. Check with `grep -r` before moving any file.
- Local only; **never push**. Drew pushes after trying it. (V7 is the exception, and only after
  Drew says so in the thread.)
- Do not touch `09-ai-visibility/` or the AI Visibility work.

Check: `python3 -m pytest -q chatbot/tests tooling/realpage-library/tests tooling/qa/fixes_tests`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765

## How to try it (30 seconds)
1. Open the project folder: the top level is short and you can tell what each folder is for.
2. Open README.md: it says what CraneSignal is, what runs where, and how to start it locally.
3. Start it with the Try command and ask the chat one question — same answers as before.

## Tasks

- [x] **V1 Make the tests honest.** Three checks in `tooling/qa/fixes_tests/` fail today and failed
  before any recent change: `test_e1_signin`, `test_h7_novice_browser_dry_run`,
  `test_t5_logo_links_home`. For each: decide if the app is wrong or the test is out of date, then
  fix the test (or the app, if it is genuinely broken) so the whole folder passes. Then widen the
  `Check:` line in this plan to `python3 -m pytest -q chatbot/tests tooling/realpage-library/tests
  tooling/qa/fixes_tests`. Commit.
- [x] **V2 Tidy the top level.** 31 `PLAN-*`, `TODO-*`, `HOW-TO-*` and `D3-*` files sit in the
  project root. Move finished ones to `docs/plans/done/` and unfinished ones to `docs/plans/`,
  keeping git history (`git mv`). Leave `README.md`, `AGENTS.md` and the folders. Add
  `docs/plans/README.md` listing what is done and what is still open, one line each. Check
  nothing references the old paths (`grep -rn "PLAN-" --include=*.py --include=*.sh --include=*.md`
  and fix links). Run Check. Commit.
- [x] **V3 Clean the website service.** `site/` only: read `site/js/*.js`, `site/Dockerfile` and
  `site/Caddyfile`. Remove dead code and commented-out blocks, give each file a one-line header
  saying what it does, make names say what they mean, and delete any page or asset nothing links
  to (prove it with grep first, and list what you deleted in the progress file). No visual or
  behaviour change. Run Check. Commit.
- [x] **V4 Clean the chat service.** `chatbot/` only: `proxy.py`, `linkfix.py`, `autobold.py`,
  `signup_alerts.py`, the two Dockerfiles and the three compose files. Same rules as V3. Say in
  one line at the top of each file what it is for and where it runs. If two compose files are
  near-identical, merge or delete the unused one (prove it is unused). Keep `SOUL.md` untouched.
  Run Check. Commit.
- [ ] **V5 Clean the data tools.** `tooling/` and `propertystack/skills/`: delete scripts nothing
  calls (prove with grep and list them), and give every kept script a one-line purpose header.
  Do not touch anything under `propertystack/data/`. Run Check. Commit.
- [ ] **V6 Write the README a stranger can follow.** Rewrite `README.md` as the front door of a
  finished product: what CraneSignal is in two lines, who it is for, a screenshot or two, what
  runs where (website service, chat service, data), how to start it locally in one command, where
  the tests are, and what is deliberately not built yet. Keep the outside-in constraint paragraph.
  Run Check. Commit.
- [ ] **V7 Certify v1.0.** Confirm `git status` is clean and Check passes. Write
  `CHANGELOG.md` with one `## v1.0 — 2026-09-17` section listing in plain words what this version
  does. Commit. **Then stop and ask Drew** to try it locally; only after he says yes, push `main`
  and `git tag -a v1.0 -m "CraneSignal v1.0"` and `git push origin v1.0`.
