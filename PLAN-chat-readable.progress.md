## R1 Check script — done (2026-09-13)
- Added `tooling/qa/check-readable.sh`: fails unless SOUL.md has a "Bottom line" rule and custom.css has a message/prose rule with font-size >= 17px and line-height >= 1.6.
- Ran it: fails on both parts, as intended (R2 and R3 will make it pass). check-panel.sh passes (0 problems).
- Note: the plan's full Check line will fail until R2+R3 are done — expected.

## R2 Answer shape rule — done (2026-09-13)
- SOUL.md "How to answer": added "Easy to read" (short paragraphs, blank lines, headings only for call sheets) and "Bottom line" rule (2-4 short bullets at the end of answers over 3 sentences; first for deep dives/call sheets; none for one-paragraph answers). All existing rules kept.
- check-readable.sh part 1 now passes; only the CSS part fails (R3). check-panel.sh: 0 problems.
