# Findings & Decisions

## Requirements
- The result must be readable by a human, not lead with raw JSON.
- Each result should plainly show send or do not send, channel, time, message, and next action.
- Exact JSON copy and download behavior must remain unchanged.
- Diagnostics remain available but visually secondary.
- DeepSeek must be the normal writer on the live page, not a mode Drew has to discover and enable.
- The template writer remains available only as an explicit rehearsal or automatic failure fallback.

## Research Findings
- The current page labels the primary pane `Exact export object`, which makes the machine format the first thing a person sees.
- The existing page already receives both the exact public submission and separate diagnostics, so the change can stay in the browser layer.
- Record tabs say only `Record 1`, so a person cannot scan a batch for send, suppress, or escalation decisions.
- The output contract already contains everything needed for a human summary: message channel, time, subject, body, call to action, and next action.
- The new layout fits without horizontal overflow at 390, 820, and 1440 pixels and keeps the exact export one disclosure below the human result.
- The browser currently sends `offline: true` because the visible offline checkbox is checked in the HTML; this bypasses the configured model even when Railway has an API key.
- The backend already supports the desired hybrid: deterministic policy and scheduling first, one bounded DeepSeek wording call second, validation third, and a template fallback on provider failure.
- DeepSeek's current official OpenAI compatible base URL remains `https://api.deepseek.com`; its current low latency model identifier is `deepseek-flash`, while the older `deepseek-chat` name has been retired.
- Two production calls reached DeepSeek but timed out at the old 2,000 ms hard cutoff. That sample field is a p95 performance target, not a safe per-request cancellation deadline; keeping it as an evaluation and using an 8,000 ms hard ceiling preserves honest measurement and lets the AI finish.
- DeepSeek's current models enable thinking by default. The first longer-budget request spent the 400-token cap on reasoning and returned no complete JSON, so this short writing task must explicitly request non-thinking mode.
- With non-thinking mode explicit, the production sample completed in 1,887.4 ms end to end, used the model engine, produced no writer errors, and needed no template fallback.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Render from the exact submission object | Avoid duplicating decision logic in the browser. |
| Use plain labels and message preview | A leasing employee can judge the result without understanding JSON. |
| Keep copy controls next to the exact export | Prevent accidental changes to submission bytes. |
| State the writing engine in plain language | People should know immediately whether AI or a validated template wrote the message. |
| Default the checkbox to AI | The interface should match the intended interview behavior without requiring hidden setup knowledge. |
| Reuse the existing Railway secret by service reference | The case-study service gets authorization without copying or exposing the credential. |
| Configure `deepseek-flash` | It is the current official fast model and better fits the assignment's strict latency budget than the larger Pro model. |
| Separate the p95 target from the hard timeout | A statistical performance target remains reportable without forcing every individual live call to fail at exactly that number. |
| Disable thinking for message drafting | The task is constrained rewriting, and the visible JSON needs the small output budget more than hidden reasoning does. |
| Describe the production result as a smoke test | A single successful call proves the deployment path, not a latency distribution or general quality score. |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| The live service currently defaults to offline templates | Treat AI enablement as a separate provider decision; this task fixes human presentation. |

## Resources
- `archive/realpage/casestudy/web_assets/index.html`
- `archive/realpage/casestudy/web_assets/app.js`
- `archive/realpage/casestudy/web_assets/styles.css`
- `archive/realpage/casestudy/tests/test_web.py`
