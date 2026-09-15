## T1 — cookie hookup, Agent Reach, check (2026-09-15)
- `tooling/reddit_search.py` now also reads `~/.config/propertystack/reddit-cookies.json` (dict or browser-export list, joined `name=value; ...`, never printed). Order: env var → DSH credentials → cookie file.
- Agent Reach 1.5.0 installed with pipx from GitHub (default safe mode, no --system). Added `--js-runtimes node` to `~/.config/yt-dlp/config` as doctor advised; `agent-reach doctor` now shows YouTube ✅ and web (Jina) ✅. Login channels skipped.
- New `tooling/street-talk/{tests,fixtures}` and `tooling/qa/check-street-talk.sh` (offline pytest, exit 5 = pass). 4 cookie tests pass.
- Live proof: `"realpage texas" --limit 3` with the cookie-file cookie returned 3 posts (1 Reddit request).
- Note: DSH credentials also hold a Reddit cookie, so it wins over the file unless `DSH_REDDIT_COOKIE` is set; collectors may want to pass the file cookie explicitly.
