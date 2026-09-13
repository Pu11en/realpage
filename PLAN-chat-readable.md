# PropertyStack: chat answers that are easy to read

Written 2026-09-12 (sell-plan Q7). Drew finds the chat hard to read: too much text, packed
together, too small. Long answers are fine, but every answer must **end with a short summary
of what matters**, and the panel text must be bigger and airier. Uses the shared local stack (`tooling/dev.sh`, ports 8765/3000/18080), so run it **after** the
other chat plan, never at the same time (both edit `SOUL.md`). Localhost only until Drew
says it's good; no push.

Run with: `Do the next unticked task in PLAN-chat-readable.md, then tick it and stop.`
Check: `bash tooling/qa/check-panel.sh && bash tooling/qa/check-readable.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765 → Ask (no sign-in locally)

## How to try it (30 seconds)
1. Open http://localhost:8765, click Ask, ask "Which Yardi buildings sold recently?"
2. The answer ends with a bold **Bottom line** and 2–4 short bullets you can read at a glance.
3. The text is clearly bigger than before, with space between paragraphs and table rows.

## Tasks

- [x] **R1 Check script.** `tooling/qa/check-readable.sh` (free, no bot calls, under 10 s):
  fails unless `chatbot/hermes-profile/SOUL.md` contains a "Bottom line" rule and
  `chatbot/branding/custom.css` sets the chat message font size to at least 17px and
  line-height to at least 1.6. Run it once to see it fail (both parts missing), commit.
- [ ] **R2 Answer shape rule.** In `SOUL.md` "How to answer": every answer longer than 3
  sentences ends with a line `**Bottom line**` followed by 2–4 bullets (max ~15 words each):
  the answer itself, the one number or name that matters, and the next useful step. Short
  paragraphs (max 3 sentences), a blank line between blocks, headings only for call sheets.
  One-paragraph answers need no Bottom line. **Exception: deep dives / call sheets put the Bottom
  line first** (sell-plan H9/H10), since they're long. Keep every existing rule. `check-readable.sh`
  part 1 passes.
- [ ] **R3 Bigger, airier text.** In `chatbot/branding/custom.css` (panel mode): message text
  17px, line-height 1.65, 12px gap between paragraphs/list items, table cells padded 8px,
  bold text clearly heavier. Don't touch colors. Restart with `bash tooling/dev.sh`; screenshot
  a long answer in the panel to `/tmp/readable.png` and look at it. Check passes.
- [ ] **R4 Real answer check (💲 a few cents).** With the local stack up, ask the bot 3
  questions through `http://localhost:18080/v1/chat/completions` (header
  `X-OpenWebUI-User-Email: admin@localhost`, key `local-trial-key-change-me`): "Which vendor
  runs the most buildings?", "Which Yardi buildings sold recently?", "Prep me to cold call
  Vantage At Spring Creek." The long ones end with `**Bottom line**` + bullets; the short one
  doesn't need it. Save the three answers to `/tmp/readable-answers.md`. Fix SOUL.md wording
  if not. Then tell Drew in plain words it's ready to try on localhost.
