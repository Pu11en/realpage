# Task Plan: Website chat that works like Eve

## Goal
No holes: the chat never breaks, loses things or confuses you (Drew, 2026-09-11).
Plan (not build) the PropertyStack website chat so it works like Eve, the Hermes agent
on Railway: its own memory, saved chats, live answers, polished UI. The result is a
final `PLAN-v4.md` that `/gowork` can run one small task at a time.

## Next Step
PLAN-v5 A1 done (Open WebUI running locally). Next: A2 Google sign-in (Drew does the Google console steps).

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
- [x] Drew OKs the plan (picked "start A1")
- **Status:** complete (review skipped by Drew's choice)

### Phase 6: Build (PLAN-v4)
- [x] A1 server-side chats (local)
- [x] A3 + B2 live words, progress line, Stop (local)
- [x] B7 plain errors, scroll, collapse, busy hint, warm-up line
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
| Goal is a hole-free experience, not features | Drew clarified; holes table + Z1 test suite + Z2 hunt added |

## Errors Encountered
| Error | Attempt | Resolution |
|---|---|---|
| Worktree kept disappearing between messages | 1–3 | Re-add it each message; plan files moved into it |
| init-session ran in main checkout | 1 | Moved `.planning/` into the worktree |

## Drew's direction (2026-09-11, late)
- Site pages stay open to everyone, no sign-in to look.
- The chat is locked: Google sign-in (one click, no passwords, no made-up accounts);
  signed-in people get unlimited chat with their own saved history.
- Chat must feel part of PropertyStack and be reachable from everywhere in it.
- Under the Hood needs its own plan in a separate session (not this one).
- Proposed: Open WebUI with Google login as the chat app; PropertyStack gets a "Chat" tab
  + the Ask button opening it; branded to match. Awaiting Drew's pick on how it appears.
- Drew picked: Chat tab + Ask button open full-screen branded Open WebUI (option 1). PLAN-v5.md written.
