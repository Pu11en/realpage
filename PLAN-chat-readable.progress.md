## R1 Check script — done (2026-09-13)
- Added `tooling/qa/check-readable.sh`: fails unless SOUL.md has a "Bottom line" rule and custom.css has a message/prose rule with font-size >= 17px and line-height >= 1.6.
- Ran it: fails on both parts, as intended (R2 and R3 will make it pass). check-panel.sh passes (0 problems).
- Note: the plan's full Check line will fail until R2+R3 are done — expected.
