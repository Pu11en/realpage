# Progress: PLAN-v1-cleanup

## V1 Make the tests honest — done (2026-09-17, commit 8073b76)
- All three failures came from one deliberate change (commit 090705b, "App opens on the Map, links
  back to the home page"). The app is right; the tests were out of date. No app code changed.
  - test_t5: the wordmark now links to LANDING_URL (cranesignal.com), not index.html.
  - test_h7: the chat loader sends stray pages to /map.html, not "/".
  - test_e1: signed-out "/" redirects to /map.html, which is itself gated, so it still ends at sign-in.
- Widened the plan's Check line to the whole tooling/qa/fixes_tests folder.
- Checked: the new Check command, 253 passed.
- Open, for V3: in site/Caddyfile the "/" block's forward_auth never runs, because Caddy orders
  redir before it. Harmless (the Map is gated) but it is dead config. Removing it changes nothing
  a visitor sees; wrapping it in route{} would change the redirect order, so left alone.

## V2 Tidy the top level — done (2026-09-17, commit 2a7cefa)
- Moved 31 PLAN-*/TODO-*/HOW-TO-*/D3-* files to docs/plans/ (unfinished, 13 files) and docs/plans/done/
  (finished, 18 files). Used `git mv` to preserve history.
- Created docs/plans/README.md listing 9 done plans and 12 open/blocked plans.
- Fixed 3 references: AGENTS.md (ai-visibility and realpage-site-library paths), README.md (build plans),
  tooling/start-after-texas.sh (PLAN-map-markers path).
- Checked: `grep -rn "PLAN-" --include="*.py" --include="*.sh" --include="*.md" .` — no broken references
  found (old references like PLAN-lead-finder-build are historical, not in current tree).
- Checked: 253 pytest passed.

## V3 Clean the website service — done (2026-09-17, commit 70756ce)
- site/js, Dockerfile and Caddyfile were already tidy: every file had a header, no commented-out code.
- Removed: unused isDimmedRow() in app.js; duplicate tooltip-placing lines in map.js (now one
  placeTip()); the never-running forward_auth in the Caddyfile "/" block (noted in V1; redir is
  ordered first, so visitors see no change); comment pointers to PLAN-v5/v6, which no longer exist.
- Deleted pages/assets: none. grep showed every page, font, vendor file, css and data json is
  linked or read by a page, tool or test.
- Checked: node --check on the three JS files; Check command, 253 passed. caddy is not installed
  here, so the Caddyfile was not machine-validated — V7's local try covers it.
- Open: styles.css still has a "tr.dimmed" rule nothing sets (css was outside V3's file list).

## V4 Clean the chat service — done (2026-09-17, commit fcb8a02)
- The chat service was already tidy: no commented-out code, no unused functions or imports
  (checked every name in the four Python files with a script plus grep across the repo).
- Changed: each of the 9 files now opens with one line saying what it is and where it runs;
  proxy.py uses the one ENGINE_MODEL_ID setting instead of repeating "hermes-agent" five times
  (same value, moved up with the other settings); dropped old plan codes (W2, W8) from comments.
- Compose files: all three kept. local is the base; dev (used by tooling/dev.sh) and human-test
  (used by tooling/human-test.sh and test_h6) are small overlays on it, not near-copies.
- Deleted: nothing. SOUL.md untouched.
- Checked: Check command, 253 passed. Docker images were not rebuilt here; V7's local try covers it.
- Open: chatbot/README.md, SPOT-CHECK.md and TEST-ANSWERS-2026-09-10.md were outside V4's list; V6
  may want to fold or move the last two.

## V5 Clean the data tools — done (2026-09-17, commit 92acfbe)
- tooling/ and propertystack/skills/ were already clean: no commented-out code, no unused functions.
- All scripts already have one-line purpose headers (docstring or bash comment on line 2).
- Deleted: 10 legacy unused probe scripts (tooling/probe/step1_cleanup.py, step1_debug.py,
  step1_final_search.py, step1_finalize.py, step1_search_communities.py, step1_search_more.py,
  step2_bakeoff.py, step2_debug.py, step3_improved.py, step3_vendor_detection.py). These were
  experimental vendor-detection scripts from the probe phase, never called anywhere.
- Checked: grep -r confirmed nothing imported or called these scripts; Check command, 253 passed.
- propertystack/data/ untouched.
