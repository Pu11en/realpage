# PropertyStack: weekly Texas run (new leads every Monday, on Drew's computer)

Written 2026-09-14 with Drew (answers: `/home/drewp/main-projects/handoffs/2026-09-14-texas-weekly-answers.md`).
**Starts only when Drew says "go work"**, after the Texas build (`PLAN-lead-finder-texas.md`) and the map build
(`PLAN-map-markers.md`) are merged. All lead-finder rules still apply: area-agnostic code (Texas specifics only
in data recipes), never guess facts, Jina first + Brave second (keys in `/home/drewp/main-projects/realpage/.env`
or the build copy's `.env`; never commit keys), SearXNG banned, Collin County / Plano-Richardson never rerun,
RealPage-gap ranking (rank, don't ban), no quality gates (reports only). **Localhost only: the weekly run
commits locally and never pushes; Drew pushes by hand.**

Drew's decisions:
- **When:** every Monday morning, automatically, on Drew's computer (systemd user timer, `Persistent=true` so a
  missed Monday runs when the PC is next on).
- **What:** the 4 big metros (Dallas-Fort Worth, Houston, Austin, San Antonio) city by city from the Texas
  recipes + the statewide TDLR TABS registry for everywhere else. Each run = new records since the last run +
  a re-check of the last 90 days of leads for changes (started construction, leasing, sold, new phone).
- **Dallas + Houston:** all three: free records (Houston weekly "Sold Permits" sheets, DCAD/HCAD files,
  TABS) + one weekly Jina news search for new Dallas/Houston apartment projects + reading Dallas's public
  permit search site. If the Dallas site breaks or blocks us, skip it and say so in the note -- never stop the run.
- **No AI in gathering:** plain code on public records; Jina/Brave only for software, missing phones and the
  one news search.
- **One row per building:** a building found in several sources is one row with "found in 3 sources" listing them.
- **Tags:** "NEW this week" on new leads, "UPDATED: now leasing" (etc.) on changed leads; tags show for 7 days.
  **Leads are never removed.**
- **Answer key:** 25 real new or sold Texas buildings from news/developer announcements (never from sources
  the tool reads); each run reports "found X of 25" (report only). Refresh the key every 3 months.
- **Discord note (bot `/api/notify` to thread 1548911246705959072):** just totals + cost, e.g.
  "Texas: 12 new projects, 5 new sales, 3 updated · found 19 of 25 · cost this week $0.02". No spending cap.
- **Pre-approved, don't ask:** Jina searches for building this (answer key, tests, the one real run in W9);
  Brave under its 800/month free cap; free public downloads.
- **Not in the weekly run:** Agent Reach (its own section, planned separately).

Run with: `Do the next unticked task in PLAN-texas-weekly.md, then tick it and stop.`
Check: `bash tooling/qa/check-lead-finder.sh`
Try: `bash tooling/texas-weekly.sh --dry-run && bash tooling/dev.sh`
Open: http://localhost:8765 → Early Leads → Tx

## How to try it (30 seconds)
1. Early Leads → Tx: some rows have a "NEW this week" or "UPDATED" tag, and a building from several sources shows "found in N sources".
2. Ask the chat "what's new in Texas this week?": it lists the new leads.
3. Discord shows the Monday note with totals, "found X of 25" and the cost.

## Tasks

- [ ] **W1 Remember the last run.** `propertystack/runs/tx/state.json` keeps, per source, the date (or last
  record id) of the last successful pull. Every Texas puller built in `PLAN-lead-finder-texas.md` (T2-T5: TABS, city recipes, Houston sheets,
  DCAD/HCAD, TAD) and `PLAN-texas-round2.md` (Williamson, Bexar, College Station, Fort Bend) takes a `since` date and pulls only newer records. Seed `state.json` from the newest
  record date per source in the Texas build's run folder. Appraisal-district zips (~200 MB, updated about
  monthly) are re-downloaded only when the file changed (Last-Modified/size), else the cached copy is reused. Tests
  with saved responses. Commit.
- [ ] **W2 One row per building.** Extend the existing `merge.py` (don't write a second merger): merge matches the same building across sources (same address after
  cleanup, or same distinctive name in the same city -- reuse `lib.building_match`); the row keeps every
  source (name + link) and the best facts (record fields beat news). Fixture tests from real Texas rows
  (a TABS project that is also an Austin permit). Commit.
- [ ] **W3 NEW and UPDATED tags.** Compare the new `leads.json` to the last committed one (`git show HEAD:<path>`): new building →
  `tag: "NEW"`, changed stage/sale/phone/software → `tag: "UPDATED"` + what changed ("now leasing",
  "sold to X"); `tagged_on` date; tags older than 7 days are cleared. Leads are never deleted. Weekly
  totals (new projects, new sales, updated) written to the run folder. Tests. Commit.
- [ ] **W4 90-day re-check.** For leads first seen in the last 90 days, re-read their own records (TABS
  detail page, permit row, CAD account) for stage/finish date/sale changes, feeding W3. Cache, 1-2 s between
  requests to one site. Tests. Commit.
- [ ] **W5 Weekly news search for Dallas + Houston.** One or two Jina searches ("new apartment
  development Dallas", same for Houston, last 7 days); keep only results that name a building/project
  with 20+ units in that city (F2 "is this about this building" check); merge via W2 with source "news";
  never guess units. Tests with saved results. Commit.
- [ ] **W6 Dallas permit site.** Find Dallas's current public permit search (the city's online permit
  portal); check its terms/robots allow reading. If allowed: a recipe that searches new multifamily /
  commercial building permits since the last run, 2 s between pages, cached, capped at 200 pages a run.
  If not allowed or no public search: record "Dallas permit site: not usable (reason)" in the source
  notes and skip -- no workaround. Any error at run time = skip + mention in the note. Commit.
- [ ] **W7 Texas answer key.** `propertystack/answer-keys/tx.json`: 25 real new or recently sold Texas
  apartment buildings (20+ units, not Collin County) from news, developer press releases and apartment
  association lists only, each with its link, spread across the 4 metros and smaller cities; `made_on`
  date. Each run writes "found X of 25" + the missed names to the run folder. Commit.
- [ ] **W8 Cost line.** Count Jina and Brave calls per run (Brave also toward its 800/month free cap in
  `propertystack/runs/brave-usage.json`), convert to dollars (Jina ~$0.0005/search; Brave free under
  the cap), write per-run and month-to-date cost. Tests. Commit.
- [ ] **W9 The weekly script.** `tooling/texas-weekly.sh` (absolute paths, log to
  `propertystack/runs/tx/weekly.log`): if a gowork build is active on this repo (see
  `~/.local/state/ccdb/gowork-loops.json`) or the tree has uncommitted changes, wait and retry hourly
  for up to a day; else W1 pulls → W4 → W5 → W6 → merge (W2) → tags (W3) → software/phone lookups for new
  leads only → answer-key score → cost → `bash tooling/dev.sh` rebuild (site + chat) → local commit
  "Texas weekly <date>" (**never push**) → Discord note: `POST $CCDB_API_URL/api/notify` with `Authorization: Bearer $CCDB_API_SECRET` and
  `{"message": ..., "channel_id": 1548911246705959072}`; URL + secret read from
  `~/.config/propertystack/weekly.env` (chmod 600, never in the repo; create it from the session's
  `CCDB_API_URL`/`CCDB_API_SECRET` env vars if missing). If the bot is down, save the note in the run folder. If the answer key is older than 3 months, the
  note adds "answer key due for refresh". `--dry-run` skips the commit and note. A failing source is
  skipped and listed in the note. Run it once for real; paste the note in the progress log. Commit.
- [ ] **W10 Monday timer.** systemd user unit + timer (`OnCalendar=Mon 08:00`, `Persistent=true`) in
  `tooling/systemd/`, an install script that copies them to `~/.config/systemd/user/` and enables the
  timer; confirm with `systemctl --user list-timers`. **The unit runs the real checkout's script by
  absolute path, `/home/drewp/main-projects/realpage/.worktrees/local-test/tooling/texas-weekly.sh`, never
  the build copy (it is deleted after the build).** If that file isn't there yet (build not merged), the
  unit logs "not installed yet" and exits 0. Also check WSL has systemd on (`systemctl --user status`);
  if not, write that in the progress log and use a user crontab line instead. Commit.
- [ ] **W11 Show it on the site + chat.** Texas table: small "NEW this week" / "UPDATED: …" badges, a
  "found in N sources" note that expands to the source links, and a line at the top "Updated Monday
  <date>: N new, M updated". Chat data includes the tags so "what's new in Texas this week?" works
  (`tooling/qa/check-answers.sh` case). Minimal styling (Drew does design). Rebuild with
  `bash tooling/dev.sh`. Commit. Recap in plain words for Drew what changed.
