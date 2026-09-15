# CraneSignal: "Street Talk" tab (what Texas people say on Reddit, powered by Agent Reach)

Written 2026-09-14 with Drew. **Starts only when Drew says "go work".** Localhost only, never push.
Minimal styling (Drew does design himself). **Texas only.** Research notes: `docs/agent-reach-research.md`.

Drew's answers:
- One new tab with all three parts: (1) RealPage vs Yardi / Entrata / AppFolio talk, (2) chatter about
  specific Texas buildings on our lead list, (3) unhappy Yardi/Entrata/AppFolio customers = warm leads.
- Sources: **Reddit** (Drew's cookies, already saved privately at `~/.config/propertystack/reddit-cookies.json`,
  chmod 600, outside git -- never print, copy or commit them) plus the free no-login Agent Reach parts
  (YouTube transcripts via yt-dlp, web pages via Jina). No X, no LinkedIn.
- **Separate section** (Drew, 2026-09-15): do NOT touch the AI Visibility tab or its files at all.
- The chat (CraneSignal Agent) can answer from this data.
- Runs with the weekly Texas refresh. The website only shows saved files; nothing scrapes live on page load.

Reddit safety rules (every task): read-only GET requests, at most 1 request every 3 seconds, at most 80
Reddit requests per full run, stop on the first 403/429 and keep what was saved. No posting, voting or
account actions. Tests never call Reddit -- they use saved sample files in `tooling/street-talk/fixtures/`.
Commit after every chunk so a crash never loses collected posts.

Prerequisites met (2026-09-15): Texas leads are merged (`propertystack/data/tx/`, 586 chat leads) and the
map build is done. User-facing name is **CraneSignal** (tab, chat answers): never show "PropertyStack"
or "Hermes" to users; code and folders keep their internal names. Texas buildings = every area under
`propertystack/data/` whose leads are in TX (area-agnostic, no hard-coded area list). No paid AI calls
anywhere in this plan (the paid `check-answers.sh` is left for Drew to run himself).

AI for the build: same as the planning session (`"harness": "same"`, Drew picked 2026-09-15).

Runs fully automatic, start to finish, after "go work" (Drew, 2026-09-15): **no stops to ask Drew**. Each live
pull (T2-T4) instead writes its counts (requests used, posts kept, posts dropped and why) plus 5 sample posts
to `propertystack/data/street-talk/raw/<date>/<part>-report.md` and moves on. Only stop early if Reddit
blocks (403/429) -- keep what was saved and report it. A fix Drew
asks for becomes a new checkbox, never an edit to a running task. The Check tests the saved data too: once
`site/data/street-talk.json` exists, every post has a reddit.com or youtube.com link, a date, a part, no
duplicate links, and part 1/3 posts name at least one of the four companies.

Run with: `Do the next unticked task in PLAN-street-talk.md, then tick it and stop.`
Check: `bash tooling/qa/check-street-talk.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765/street-talk.html

## How to try it (30 seconds)
1. Open the Street Talk tab: three parts (RealPage vs rivals, Texas buildings, unhappy rival customers), each
   post showing a short quote, subreddit, date, happy/angry label and a link to the real Reddit thread.
2. At the top of Street Talk, the totals per company read sensibly (e.g. "RealPage: 40 posts, 70% angry").
3. Ask the chat "What are people on Reddit saying about Yardi in Texas?" -- it answers with quotes and links.

## Tasks

- [x] **T1 Hook up the cookie + install Agent Reach + the check.** `tooling/reddit_search.py` also reads the
  cookie from `~/.config/propertystack/reddit-cookies.json` (join name=value pairs; never print it); keep the
  existing env/DSH sources working. Install Agent Reach in default (non-system) mode and confirm
  `agent-reach doctor` shows YouTube and web working (skip anything needing a login). Create
  `tooling/street-talk/` and `tooling/qa/check-street-talk.sh` (runs the street-talk tests offline with
  pytest; treat pytest's "no tests found" exit code 5 as a pass; no network). The existing tool already works with this cookie when it is passed in `DSH_REDDIT_COOKIE` (checked
  2026-09-14). One live search `"realpage texas" --limit 3` to prove the cookie
  works. Commit.
- [x] **T2 Part 1 collector: RealPage vs rivals in Texas.** `tooling/street-talk/collect.py --part rivals`
  searches Reddit for RealPage, Yardi, Entrata and AppFolio together with Texas words (Texas, Dallas,
  Houston, Austin, San Antonio, Fort Worth, Plano) and in r/PropertyManagement, r/multifamily, r/Dallas,
  r/houston, r/Austin, r/sanantonio, r/texas. Last 12 months. Saves raw results to
  `propertystack/data/street-talk/raw/<date>/rivals.json` (URL, subreddit, title, short excerpt, top 2
  comment excerpts, score, date). De-duplicate by URL. Test with a fixture. Run it live once (request cap from the safety rules), commit the raw file + its report, continue.
- [x] **T3 Part 2 collector: Texas buildings.** `--part buildings` takes the biggest Texas lead buildings
  (every TX area, top 40 by units) and searches Reddit for "<building name> <city>";
  also a YouTube search per building via Agent Reach (title + link, transcript excerpt only if it names the
  building). Keeps a post only if it names the building. Saves `raw/<date>/buildings.json` with the building
  id attached. Test with a fixture. Run it live once (request cap from the safety rules), commit the raw file + its report, continue.
- [x] **T4 Part 3 collector: unhappy rival customers.** `--part unhappy` searches property-manager subreddits
  for Yardi / Entrata / AppFolio with complaint words (switching, leaving, support, hate, migrate, alternative)
  plus Texas words. Saves `raw/<date>/unhappy.json`. Test with a fixture. Run it live once (request cap from the safety rules), commit the raw file + its report, continue.
- [ ] **T5 Labels + the saved tab data.** `tooling/street-talk/build.py` turns the raw files into
  `site/data/street-talk.json` and `propertystack/data/street-talk/street_talk.csv`: each post gets which
  companies it names, happy / angry / mixed (a simple word list, no paid AI), the Texas city if any, the
  building id (part 2), and "warm lead" for part 3 when the poster sounds like a manager/owner. Also totals
  per company (posts, % angry, % happy). Tests on fixtures. Commit.
- [ ] **T6 The Street Talk tab.** `site/street-talk.html` shows the totals at top, then the three parts,
  newest first, each post: quote, subreddit, date, label, link. Part 2 groups by building and links to that
  building's page (`property.html?id=<id>`); part 3 marks warm leads. Add "Street Talk" to the tab bar on every page. Works on phone
  size. Plain "no posts yet" if a part is empty. Commit.
- [x] **T7 (dropped by Drew 2026-09-15: Street Talk stays separate from AI Visibility -- skip, change nothing.)**
- [ ] **T8 The chat can use it.** The `propertystack` chat plugin also loads `street_talk.csv` as table
  `street_talk`; the query-propertystack skill lists it ("Reddit posts" in Sources, always with the thread
  link). Add an offline plugin test (table loads, a sample query returns rows with links) to
  `check-street-talk.sh`. Add 2 Street Talk questions to `tooling/qa/check_answers.py` but do NOT run it
  (it costs money; Drew runs it). Commit.
- [ ] **T9 Weekly refresh.** Write `tooling/street-talk/weekly.sh` (runs the three collectors + build, then
  commits the new data). If a weekly Texas refresh script exists by then, call it from there; otherwise leave
  weekly.sh ready and tell Drew -- do not set up any timer yourself. Same safety limits; a failed Reddit run keeps last week's data and says so on the tab
  ("last updated <date>"). Recap in plain words for Drew what changed, including each part's counts from the reports. Commit.
