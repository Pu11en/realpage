## R1 Check script — done (2026-09-13)
- Added `tooling/qa/check-readable.sh`: fails unless SOUL.md has a "Bottom line" rule and custom.css has a message/prose rule with font-size >= 17px and line-height >= 1.6.
- Ran it: fails on both parts, as intended (R2 and R3 will make it pass). check-panel.sh passes (0 problems).
- Note: the plan's full Check line will fail until R2+R3 are done — expected.

## R2 Answer shape rule — done (2026-09-13)
- SOUL.md "How to answer": added "Easy to read" (short paragraphs, blank lines, headings only for call sheets) and "Bottom line" rule (2-4 short bullets at the end of answers over 3 sentences; first for deep dives/call sheets; none for one-paragraph answers). All existing rules kept.
- check-readable.sh part 1 now passes; only the CSS part fails (R3). check-panel.sh: 0 problems.

## R3 Bigger, airier text — done (2026-09-13), commit 89e3feb
- custom.css: chat message text 17px / line-height 1.65, 12px gap under paragraphs and list items, table cells padded 8px (Open WebUI keeps its own 12px sideways padding) at 15px text, bold 700. No colors changed.
- Checked: loaded a real long call-sheet chat in Open WebUI (port 3000) at panel width 480px with the new CSS injected; computed styles confirmed 17px/28px lines, 12px paragraph gaps, 15px table text. Screenshot at /tmp/readable.png looks clearly bigger and airier.
- Did NOT restart `tooling/dev.sh`: the running shared stack mounts custom.css from the `.worktrees/local-test` checkout, not this branch; restarting from here would swap it under other sessions. Drew sees the new look once this branch is merged into local-test (or dev.sh is run from here).
- check-panel.sh: 0 problems; check-readable.sh: OK (full Check passes).

## Paused (2026-09-13)
- Drew asked to save and close while he plans the "finished bot" picture (memory / data editing / self-building) in another session. R4 (real answer check, costs a few cents) not started. Nothing uncommitted.
