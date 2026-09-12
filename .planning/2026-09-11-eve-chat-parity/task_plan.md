# Task Plan: Website chat that works like Eve

## Goal
Plan (not build) the PropertyStack website chat so it works like Eve, the Hermes agent
on Railway: its own memory, saved chats, live answers, polished UI. The result is a
final `PLAN-v4.md` that `/gowork` can run one small task at a time.

## Next Step
Drew answers decision D-1 (what "memory" means on a public site).

## Current Phase
Phase 2: Drew's decisions

## Phases

### Phase 1: Research — COMPLETE
- [x] Compare Eve's config with the site bot's config
- [x] Check what Hermes' web API supports (sessions, streaming, memory)
- [x] Check what Deep Chat does and doesn't ship
- [x] Check the current chat code (2.0 bug fixed, trial page built)
- **Status:** complete (see findings.md)

### Phase 2: Drew's decisions (one question at a time)
- [ ] D-1 Memory: per-visitor (needs Honcho or similar), Drew-only, or chats-only
- [ ] D-2 Chat box: Deep Chat vs today's hand-built chat (try /chat-trial.html)
- [ ] D-3 Show cost per answer like Eve?
- [ ] D-4 Cost cap per question (steps / time)
- **Status:** in_progress

### Phase 3: Finish PLAN-v4.md
- [ ] Rewrite A2 to match D-1 (Honcho setup task if picked)
- [ ] Rewrite Part B to match D-2
- [ ] Every task: one outcome, 15–30 min, its own Check line
- **Status:** pending

### Phase 4: Review
- [ ] Run `/mvp-plan-review` on PLAN-v4.md, apply fixes
- [ ] Drew OKs the plan
- **Status:** pending

### Phase 5: Hand off
- [ ] Merge plan to main (local only), give Drew the `/gowork` start prompt
- **Status:** pending

## Decisions Made
| Decision | Why |
|---|---|
| Public site stays read-only (no terminal/files/web tools) | Anyone on the internet can type into it |
| Test on localhost + local Docker before any Railway deploy | Drew's GitHub-last rule |
| Website tests fake the bot's replies | No cost, repeatable |

## Errors Encountered
| Error | Attempt | Resolution |
|---|---|---|
| Worktree kept disappearing between messages | 1–3 | Re-add it each message; plan files moved into it |
| init-session ran in main checkout | 1 | Moved `.planning/` into the worktree |
