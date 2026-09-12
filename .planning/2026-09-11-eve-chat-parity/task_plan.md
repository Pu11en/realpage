# Task Plan: Website chat that works like Eve

## Goal
Plan (not build) the PropertyStack website chat so it works like Eve, the Hermes agent
on Railway: its own memory, saved chats, live answers, polished UI. The result is a
final `PLAN-v4.md` that `/gowork` can run one small task at a time.

## Next Step
Review PLAN-v4.md (Phase 4), then Drew OKs it and starts A1.

## Current Phase
Phase 4: Review

## Phases

### Phase 1: Research — COMPLETE
- [x] Compare Eve's config with the site bot's config
- [x] Check what Hermes' web API supports (sessions, streaming, memory)
- [x] Check what Deep Chat does and doesn't ship
- [x] Check the current chat code (2.0 bug fixed, trial page built)
- **Status:** complete (see findings.md)

### Phase 2: Drew's decisions (one question at a time)
- [x] D-1 Memory: saved chats now; memory add-ons get a trial first (PLAN-v4 A2/A2b)
- [x] D-2 Chat box: today's hand-built chat (my call; Drew doesn't want tech questions)
- [x] D-3 Show cost per answer like Eve: yes (B6)
- [x] D-4 Cost cap: 20 steps, 120s per answer (A4)
- **Status:** complete

### Phase 3: Finish PLAN-v4.md
- [x] Rewrite A2 to match D-1 (now A2 trial + A2b Drew picks)
- [x] Rewrite Part B to match D-2
- [x] Every task: one outcome, 15–30 min, its own Check line
- **Status:** complete

### Phase 4: Review
- [ ] Run `/mvp-plan-review` on PLAN-v4.md, apply fixes
- [ ] Drew OKs the plan
- **Status:** in_progress

### Phase 5: Hand off
- [ ] Merge plan to main (local only), give Drew the `/gowork` start prompt
- **Status:** pending

## Decisions Made
| Decision | Why |
|---|---|
| Public site stays read-only (no terminal/files/web tools) | Anyone on the internet can type into it |
| Test on localhost + local Docker before any Railway deploy | Drew's GitHub-last rule |
| Website tests fake the bot's replies | No cost, repeatable |
| D-1: saved chats first, memory add-on trial later | Built-in memory is shared by all visitors; add-on costs unknown |
| D-2: keep hand-built chat, drop Deep Chat | Eve-like parts are custom anyway; ours already renders citations/tables |
| D-3: show cost under answers | Matches Eve's `show_cost` |
| D-4: 20 steps, 120s cap | Longer chats like Eve, bounded cost |

## Errors Encountered
| Error | Attempt | Resolution |
|---|---|---|
| Worktree kept disappearing between messages | 1–3 | Re-add it each message; plan files moved into it |
| init-session ran in main checkout | 1 | Moved `.planning/` into the worktree |
