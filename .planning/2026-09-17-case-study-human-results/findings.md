# Findings & Decisions

## Requirements
- The result must be readable by a human, not lead with raw JSON.
- Each result should plainly show send or do not send, channel, time, message, and next action.
- Exact JSON copy and download behavior must remain unchanged.
- Diagnostics remain available but visually secondary.

## Research Findings
- The current page labels the primary pane `Exact export object`, which makes the machine format the first thing a person sees.
- The existing page already receives both the exact public submission and separate diagnostics, so the change can stay in the browser layer.
- Record tabs say only `Record 1`, so a person cannot scan a batch for send, suppress, or escalation decisions.
- The output contract already contains everything needed for a human summary: message channel, time, subject, body, call to action, and next action.
- The new layout fits without horizontal overflow at 390, 820, and 1440 pixels and keeps the exact export one disclosure below the human result.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Render from the exact submission object | Avoid duplicating decision logic in the browser. |
| Use plain labels and message preview | A leasing employee can judge the result without understanding JSON. |
| Keep copy controls next to the exact export | Prevent accidental changes to submission bytes. |
| State the writing engine in plain language | People should know immediately whether AI or a validated template wrote the message. |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| The live service currently defaults to offline templates | Treat AI enablement as a separate provider decision; this task fixes human presentation. |

## Resources
- `casestudy/web_assets/index.html`
- `casestudy/web_assets/app.js`
- `casestudy/web_assets/styles.css`
- `casestudy/tests/test_web.py`
