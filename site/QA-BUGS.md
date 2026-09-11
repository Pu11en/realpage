# PropertyStack QA bug log

Final live check (QA Task 3, 2026-09-10) against https://propertystack-production.up.railway.app with `python3 tooling/qa/sweep.py <url> --chat`. Widths: desktop 1440, tablet 820, phone 390. Screenshots live in `/tmp/qa/` (not committed).

## Real bugs

| # | Page | Width | Steps | What's wrong | Screenshot | Status |
|---|------|-------|-------|--------------|------------|--------|
| 1 | under-the-hood.html | phone 390, tablet 820 | Open Under the Hood, look at the Pipeline cards | The pipeline cards wrap, leaving a "→" arrow dangling at the end of a row pointing at nothing, and the last card stretches full width alone on tablet. | `/tmp/qa/phone-under-the-hood.png`, `/tmp/qa/tablet-under-the-hood.png` | Fixed: below 900px the cards sit in an even grid (3 columns tablet, 2 phone) with the arrows hidden. |
| 2 | property.html (23Hundred @ Ridgeview) | all | Open the property, click its website | The website is dead (404). | -- | Left for the next data refresh (from the first sweep, out of scope). |

## Checked and fine

- No page scrolls sideways on phone or tablet; wide tables (Master Table, Run History) scroll inside their own box.
- Chat panel opens full screen on phone; the 3-turn chat test answered with sources and kept context.
- No console errors, failed requests, NaN/undefined values or dead buttons.

## False alarms dropped

- "under-the-hood.html link returns 404: http://evanagrove.com/" — the site answers 200 to a normal browser; the checker's request was refused.
- "Under the Hood" nav item shows bright white on the property page screenshots — that is just the mouse hover left over from the sweep, not an active-state bug.

## 2026-09-10 deep pass (post-Dallas-removal, 204 buildings)
- Full sweep + all 204 property pages + 3-turn live chat: 0 real bugs.
- `http://evanagrove.com/` 404 was a checker false positive (curl gets 200); sweep.py now retries external links once.
- Chat spot answers: 8 RealPage buildings, sizes and year_built all matched data with citations.
