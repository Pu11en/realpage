# Task Plan: Human-readable case-study results

## Goal
Make each case-study result understandable to a nontechnical human, use DeepSeek for normal message writing, and keep the exact JSON export and deterministic safety checks intact.

## Next Step
Give Drew the exact employer Sample.jsonl records to paste into the verified live page.

## Current Phase
Phase 8

## Phases

### Phase 1: Requirements & Discovery
- [x] Understand user intent
- [x] Identify constraints
- [x] Document in findings.md
- **Status:** complete

### Phase 2: Planning & Structure
- [x] Define the smallest human-first result layout
- [x] Identify focused test updates
- **Status:** complete

### Phase 3: Implementation
- [x] Add a human decision summary and message preview
- [x] Keep the exact JSON export available for copying and submission
- **Status:** complete

### Phase 4: Testing & Verification
- [x] Run focused UI tests and the full case-study suite
- [x] Verify responsive rendering and accessibility labels
- **Status:** complete

### Phase 5: Delivery
- [x] Commit the focused change locally
- [x] Report the human-visible behavior and ask whether to push
- **Status:** complete

### Phase 6: Make AI the normal path
- [x] Default the page to the configured DeepSeek writer
- [x] Rename offline mode so it is clearly an emergency template fallback
- **Status:** complete

### Phase 7: Regression verification
- [x] Test the default AI selection and the explicit template fallback
- [x] Run the focused and full case-study suites
- **Status:** complete

### Phase 8: Production AI verification
- [x] Configure the case-study service to reference the existing Railway DeepSeek secret
- [x] Push the approved commits and wait for a successful deployment
- [x] Run one authorized live model example and verify the result reports the model engine
- **Status:** complete

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Lead with the human decision | Drew needs to understand and judge each result without reading JSON. |
| Keep JSON secondary | The exact export remains necessary for the interview submission. |
| Preserve the deterministic safety boundary | The presentation change must not weaken consent, timing, or safety checks. |
| Use AI for wording, not policy decisions | The model can make the message natural while deterministic gates protect consent, timing, channel, and next actions. |
| Keep templates as a visible fallback | A provider failure must not break the interview, but fallback is no longer the normal selected path. |
| Report the live smoke test without generalizing it | One passing call proves wiring and safety flow, not p95 performance or overall model quality. |

## Errors Encountered
| Error | Resolution |
|-------|------------|
| `init-session.sh` was not executable | Ran the same installed script explicitly with `sh`. |
| Browser test read hidden JSON with `inner_text()` | Use `text_content()` for the intentionally collapsed submission details. |
| Subject row stayed visible when marked hidden | Added a global author-level hidden rule so layout display styles cannot override visibility. |
| First production AI smoke test fell back after 2,042 ms | The one-time model-list preflight consumed part of the record's 2,000 ms budget; inspect the recorded writer error and retry with the now-warm preflight cache before changing the architecture. |
| First request with the new timeout ended at the 400-token cap | DeepSeek enables thinking by default; explicitly disable thinking for this short structured writing task so hidden reasoning cannot consume the output budget. |
| Deployment wait compared against a mistyped full hash | Stopped that poll after the correct deployed commit was already successful and used Railway's returned hash for later verification. |
