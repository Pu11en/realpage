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
