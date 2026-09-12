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
