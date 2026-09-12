# Progress: Eve chat parity

## 2026-09-11
- Reviewed PLAN-v3 against the code; added 2.0 (stuck "Thinking"/dead Retry after reload).
- Built 2.0 fix + Deep Chat trial page (commit aef8a7f), tested headless with faked
  replies: citations, tables, history, reload, errors OK. Serving at
  http://localhost:8765/chat-trial.html.
- Compared Eve vs site bot; wrote PLAN-v4.md (commit e82341e).
- Found: Hermes built-in memory is shared per profile → per-visitor memory needs
  Honcho or similar. PLAN-v4 A2 needs rewriting after Drew's decision D-1.
- Started this plan (planning-with-files), Phase 2 = Drew's decisions.
- D-1 answered: option 1 (saved chats now, memory add-on trial first). PLAN-v4 A2 → A2 trial + A2b pick.
- Drew: doesn't care about widget/tech choices, wants Eve-like behavior. Decided D-2 (hand-built), D-3 (show cost), D-4 (20 steps/120s) myself; PLAN-v4 Part B + B6 updated.
- Drew clarified the goal: hole-free chat experience. Added 13 holes (H1–H13) to PLAN-v4 mapped to fix tasks, new B7 (plain errors + annoyances), Z1 (test per hole), Z2 (hands-on hunt).
- A1 built + tested: proxy session_id → X-Hermes-Session-Id (Hermes loads chat from state.db); page keeps a random chat id, New chat makes a new one, localhost uses local Docker bot (?bot=live for Railway). Headless: remembered across reload + bot restart; new chat doesn't know. Local bot container `ps-a1` left running on :18080.
- A3 + B2 built + tested: proxy /chat/stream (SSE progress/delta/done/error, plain tool labels, disconnect interrupts Hermes); page streams words, grey progress line, Send↔Stop, 15s waking-up hint, note for unanswered question after reload, falls back to /chat on 404. New hole H14 (warm-up words flash).
- B7 done: plainError() map (proxy 429 now says 'try again in N minutes'), collapse remembered, Enter-while-busy hint keeps text, scroll follows only when near bottom, answers open at their start, warm-up words held in the status line (promote after 120 chars/newline/1.5s). Tests: /tmp/b7_test.py, /tmp/b7_scroll.py all pass.
- Direction change: Open WebUI + Google sign-in, linked from a Chat tab/Ask button. PLAN-v5.md written (A1–A5 local, B1–B2 site links, C1–C3 ship). PLAN-v4 marked superseded.
