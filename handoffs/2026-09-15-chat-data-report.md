# CraneSignal Chat Data Report

## ✅ What Changed

- The chat now has the data that was already in the repo, without doing new scraping or adding new lead-finder runs.
- The rebuilt chat image includes **27 new chat data CSV files** from this plan.
- The new data is loaded through the same Docker knowledge-base path the real local chat uses.
- The local stack is running now:
  - **Site:** http://localhost:8765
  - **Chat app:** http://localhost:3000
  - **Bot health endpoint:** http://localhost:18080/health

## ✅ What The Chat Can Answer Now

### Dallas Building Survey

- The chat can answer questions from the parked Dallas survey.
- It has **52 Dallas buildings**, **52 websites**, **52 software rows**, **52 contact rows**, and **7 sale rows**.
- This is labeled as a **separate Dallas building survey**, not extra leads.
- Texas, Dallas-Fort Worth, and map lead counts should not change because of this.

### Lead Map Numbers

- The chat can answer “where are most leads?” from the same map data the site uses.
- The map summary covers **20 states** and **260 mapped leads**.
- The top state is **Texas with 40 leads**.
- Texas top cities are **Houston 7**, **Fort Worth 5**, and **McKinney 5**.

### Software Market Share

- The chat can answer vendor-share questions from the site's software-share data.
- This scope is **Plano and Richardson only**.
- It has **10 vendors**.
- The top vendors are:
  - **Yardi:** 66 properties, 19,732 units, 43.4% of identified properties.
  - **RealPage:** 36 properties, 8,688 units, 23.7% of identified properties.
  - **Entrata:** 22 properties, 6,052 units, 14.5% of identified properties.

### Building Details

- The chat can join extra building-page details back to the existing building records.
- It now has **204 property rows** with fields like owner, website confidence, unknown reason, sale notes, and lead notes.
- The site data says those 204 apartments total **54,784 units**.
- The site has software identified for **152 properties**, or **74.5%**.

### CraneSignal's Own Numbers

- The chat can answer “how was CraneSignal built?” from real build and evaluation data.
- It now has small tables for pipeline steps, pipeline runs, review queue, review reasons, chat stats, eval checks, eval summary, eval failure types, accuracy docs, buildbot summary, and buildbot examples.
- The biggest build-history tables are **52 pipeline runs** and **52 review queue rows**.
- These are scoped only to questions about CraneSignal itself, not property facts.

### AI Visibility

- The chat can answer RealPage AI Visibility questions from the read-only site snapshot.
- The AI Visibility snapshot is dated **2026-09-15T08:01:07.603Z**.
- It covers **RealPage / realpage.com**.
- Snapshot numbers:
  - **34 answers**
  - **0 failed**
  - **85.3% mention rate**
  - **0% recommendation rate**
  - **50.0% first-position rate**
  - **31.2% share of voice**
- The recommended-action data is based on the September 12 and September 15 AI tests and says: **“AIs know RealPage -- but they recommend Yardi, and they bring up the lawsuit.”**

## ✅ Three Questions To Try

- **“What property software do Dallas buildings use?”**
- **“Which state has the most leads, and what are its top cities?”**
- **“How was CraneSignal built, and how accurate is it?”**

## ⚠️ What Is Still Missing On Purpose

- Software coverage outside Plano and Richardson still needs new scraping, so it was left out.
- The Dallas survey is included, but most Dallas software rows are still **unknown** in the existing repo data.
- No new web calls, scraping, paid AI checks, lead finding, Railway changes, pushing, or deployment happened.
- `tooling/qa/check_answers.py` has new questions from the earlier tasks, but those were not run because they cost money.

## ✅ Checks Run

- `bash tooling/qa/check-fixes.sh && python3 -m pytest -q chatbot/tests` passed.
- `bash tooling/qa/check-panel.sh` passed.
- `python3 -m pytest -q --ignore=propertystack/skills/client-map` passed with **542 tests**.
- Plain `python3 -m pytest -q` still cannot collect one client-map test because this worktree is missing the local `census` helper used by `propertystack/skills/client-map/targets.py`.
- The chat container was rebuilt with `bash tooling/dev.sh`.
- A direct container check confirmed all **27 new CSV files** are inside `/opt/propertystack/data`.
- The static site was restarted after the rebuild and `http://localhost:8765/map.html` returned **HTTP 200**.

