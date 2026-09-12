# PropertyStack live-site QA — chunked plan

Live site: https://propertystack-production.up.railway.app · Repo: `/home/drewp/main-projects/realpage` (branch `main`, Railway auto-deploys on push).
Sweep script: `tooling/qa/sweep.py` (Playwright). Run it as `python3 tooling/qa/sweep.py <base-url> [--chat]`. It writes screenshots and `bugs.json` to `/tmp/qa/`. If you test against localhost, serve the site with `cd site && python3 -m http.server 8765`.
Bug log: `site/QA-BUGS.md` (page, width, steps, what's wrong, screenshot). Widths: desktop 1440, tablet 820, phone 390.

Trimmed to 3 tasks (Drew, 2026-09-10): the first sweep found no errors, so we only ship fixes, fix links and do one final check. Run them in order, one tab each. Each task ends with: commit, push, confirm live, tick the box here.

## Already found in the first sweep (session 1547708946704506920)
- Phone and tablet: the sidebar never collapsed, so every page except Master Table overflowed sideways. **Fixed and shipped in Task 1.**
- Property page "← Back" did nothing when the page was opened directly. **Fixed and shipped in Task 1.**
- The La Ventura website URL was cut off (`laventuraapartments.c`). **Fixed and shipped in Task 1.**
- The Junction 15 website URL is cut off (`junction15apartments.`). Fixed to `junction15apartments.com` and shipped in Task 1 (the domain answers, 403 to bots); Task 2 only needs to check for any other cut-off URLs.
- The 23Hundred @ Ridgeview website (`american-landmark-23hundred-old.multiscreensite.com`) is dead (404). Left for the next data refresh (not in scope).
- No console errors, failed requests, NaN/undefined values or dead buttons were found. The "not found" hits on property pages were a checker false alarm and are fixed in the script.

## Tasks

- [x] **Task 1 — Ship the fixes that are already made.**
  Prompt: `In /home/drewp/main-projects/realpage, read site/QA-PLAN.md and do Task 1 only. Uncommitted changes are: phone/tablet sidebar collapse in site/css/styles.css, removal of the duplicate rules in site/master-table.html, the property.html Back-link fix, and the La Ventura URL fix (3 CSVs + rebuilt site/data/*.json), plus tooling/qa/sweep.py and site/QA-PLAN.md. Check the diff, serve site/ locally, and screenshot all 5 pages at 390 and 820 wide. Look at the screenshots for broken layout. Commit, push, confirm live, and tick Task 1.`

- [x] **Task 2 — Fix cut-off website URLs in the data.** Done 2026-09-10: scanned every URL in all CSVs, none are cut off after Task 1.
  Prompt: `In /home/drewp/main-projects/realpage, read site/QA-PLAN.md and do Task 2 only. Scan propertystack/data/plano-richardson/*.csv for website URLs whose domain is cut off (e.g. "http://www.junction15apartments."). Fix each one only if the full domain is verified to exist (curl). Run python3 site/data/build_data.py, commit, push (the chatbot service redeploys too), confirm live, and tick Task 2.`

- [x] **Task 3 — Final live check and report.** Done 2026-09-10: 1 layout bug fixed (Under the Hood pipeline arrows), 1 dead link left for data refresh, 2 false alarms dropped. See site/QA-BUGS.md.
  Prompt: `In /home/drewp/main-projects/realpage, read site/QA-PLAN.md and do Task 3 only. Tasks 1 and 2 must be ticked first. Run python3 tooling/qa/sweep.py https://propertystack-production.up.railway.app --chat, then look at the phone and tablet screenshots in /tmp/qa/ for broken layout. Write site/QA-BUGS.md listing each real bug (page, width, steps, what's wrong, screenshot) and dropping false alarms. Fix only small real bugs, push, confirm live, tick Task 3, and report bugs found, fixed and left in 5 sentences or fewer.`
