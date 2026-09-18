# Progress Log

## Session: 2026-09-17

### Current Status
- **Phase:** 1 - Requirements & Discovery
- **Started:** 2026-09-17

### Actions Taken
- Confirmed the live page is healthy and the user confusion is presentation, not input format.
- Applied the redesign and landing-page guidance: human decision first, exact JSON second.
- Initialized a dedicated planning folder and claimed the narrow case-study UI scope.
- Audited the HTML, JavaScript, CSS, and browser coverage; the existing payload needs no backend change.
- Added a human decision badge, plain channel and time, next step, message preview, explicit AI/template note, and no-message state.
- Moved exact JSON and diagnostics into secondary expandable details while preserving all copy and download controls.
- Verified the human result visually at phone, tablet, and desktop sizes with no horizontal overflow.
- Saved the implementation in local commit `d24e074`; nothing from this change has been pushed yet.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Existing production rehearsal | 31 results process successfully | Passed before this UI change | Baseline |
| Focused web suite | Human states and exact exports remain correct | 6 passed | Pass |
| Full case-study suite | No regressions | 223 passed | Pass |
| JavaScript syntax and diff check | Clean | Passed | Pass |

### Production Verification
- Deployed commit `2f59a43` successfully with a Railway reference to the existing protected DeepSeek key and the current `deepseek-flash` model.
- The first authorized live request safely returned the validated template after 2,042 ms because the model request failed during the strict first-call budget; no unsafe or partial model output reached the user.
- A second request with the preflight cache warm confirmed the provider request itself was timing out at the two second ceiling.
- Reworked the bounded writer so the p95 field remains an evaluation target while the provider has a separate configurable 8,000 ms hard safety timeout.
- The first request after that change reached the provider but reported `finish_reason=length`; official DeepSeek documentation confirmed thinking is on by default.
- Explicitly disabled thinking for the short structured drafting call and added a regression assertion for the provider request.
| Responsive visual check | Human view works at 390, 820, and 1440 pixels | Passed | Pass |

### Errors
| Error | Resolution |
|-------|------------|
| Planning initializer lacked execute permission | Invoked it through `sh`; plan created normally. |
| Browser test saw empty text inside collapsed details | Changed the assertion to read DOM text content; user-visible details remain collapsed. |
| CSS grid overrode the subject row's hidden attribute | Added `[hidden] { display: none !important; }` for reliable state changes. |

## Session: 2026-09-17, AI default and live verification

### Current Status
- **Phase:** 6 - Make AI the normal path
- **Authorization:** Drew selected the option to enable DeepSeek, push the human results screen, and spend the live model credit needed for verification.

### Actions Taken
- Confirmed the backend already implements the intended hybrid AI agent instead of needing a new architecture.
- Traced the offline behavior to the browser checkbox being selected by default and the production service having no writer model configured yet.
- Kept the deterministic safety boundary: AI writes wording only after consent, channel, timing, and next action are decided.
- Verified the current provider endpoint and fast model name against DeepSeek's official API documentation.
- Changed the browser and API defaults to the configured AI writer; the manual checkbox now plainly says it forces the template fallback.
- Verified the browser posts `offline: false` by default and still supports a deliberate template rehearsal.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Focused browser and web suite | AI selected by default; fallback remains usable | 6 passed | Pass |
| Full case-study suite | No regressions | 223 passed | Pass |
| JavaScript syntax and diff check | Clean | Passed | Pass |
