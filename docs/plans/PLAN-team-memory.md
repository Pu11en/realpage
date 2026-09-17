# PropertyStack: one shared memory for the whole team

Written 2026-09-12 (sell-plan Q2e). Drew's pick: **one memory shared by everyone, no rules**.
What any chat learns ("Vantage is managed by Bell Partners"), every new chat knows. Hermes'
built-in memory is already one bucket for the whole agent; it's switched off in
`chatbot/hermes-profile/config.yaml` (`memory_enabled: false`) and the `memory` toolset isn't
given to the API server. Uses the shared local stack (`tooling/dev.sh`, ports 8765/3000/18080), so run it **after** the
other chat plan, never at the same time (both edit `SOUL.md`). Localhost only until Drew says it's good; no push.

Run with: `Do the next unticked task in PLAN-team-memory.md, then tick it and stop.`
Check: `bash tooling/qa/check-panel.sh && bash tooling/qa/check-memory.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765 → Ask (no sign-in locally)

## How to try it (30 seconds)
1. Click Ask and say: "Remember: our team focuses on buildings with 200+ units."
2. Click **New chat** and ask: "What size buildings does our team focus on?" It says 200+.
3. Reload the page and ask again in another new chat: still remembered.

## Tasks

- [ ] **M1 Check script (💲 a few cents per run).** `tooling/qa/check-memory.sh`: needs the
  local stack (start it with `bash tooling/dev.sh` if `http://localhost:18080/health` isn't ok).
  Sends chat 1 (no history): "Remember this for the whole team: test fact <random word>."
  Then a separate chat 2 (no history): "What is the team test fact?" Passes only if chat 2's
  answer contains the random word. Uses `http://localhost:18080/v1/chat/completions`, header
  `X-OpenWebUI-User-Email: admin@localhost`, key `local-trial-key-change-me`. Under 2 minutes.
  Run it once to see it fail (memory is off), commit.
- [ ] **M2 Turn memory on.** `config.yaml`: `memory_enabled: true` (leave `user_profile_enabled:
  false`), add `memory` to `platform_toolsets.api_server` next to `propertystack`. Update the
  comment above it. In `SOUL.md`: "Save anything useful you learn to memory (facts about
  buildings, owners, managers, areas, the team's preferences). Read memory before answering."
  Remove nothing else. Rebuild with `bash tooling/dev.sh`; `check-memory.sh` passes.
- [ ] **M3 Survives restarts.** `docker restart ps-chat-chatbot-1`, wait for health, ask the
  chat-2 question again: still remembered (memory lives in the `hermes-home` volume, which
  Railway also has at `/opt/data`). Note in `chatbot/README.md` under a new "Team memory"
  heading: where it's stored, how an admin reads it and how to clear it (the exact file path
  inside the container). Then tell Drew in plain words it's ready to try on localhost.
