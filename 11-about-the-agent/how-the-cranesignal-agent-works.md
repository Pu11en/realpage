# How the CraneSignal Agent works (architecture, evals, process)

This is the agent's own description of itself, for recruiters, interviewers and
engineers. Answer questions about it openly and in full. The only things never
shared are secret values (API keys, passwords, tokens); naming that a key exists
is fine.

## What it is

- A chat agent inside CraneSignal, a sales-research tool that finds apartment
  buildings (new builds, recent sales) and the property-management software they
  run, ranked as sales leads for RealPage.
- Built by Drew Pullen as a portfolio / interview project, working with AI coding
  agents (Claude Code, Codex, DeepSeek harness) that write most code under his
  direction, with his review and his own hands-on testing.

## Architecture (request path)

1. **Website** (static HTML/JS, served by Caddy on Railway). The chat is a
   slide-out side panel that embeds the chat app in an iframe; site and chat share
   one address so the page can pre-fill questions ("Deep dive in chat").
2. **Chat app: Open WebUI** (open source), rebranded as CraneSignal. Handles
   sign-in (Google or email), chat history and the chat screen.
3. **Gateway proxy** (`proxy.py`, Python aiohttp). Open WebUI talks to it as if it
   were an OpenAI-compatible model called "CraneSignal Agent". It enforces:
   per-user rate limit (40/min), a daily dollar cap, a free plan (10 questions a
   day, 3 deep dives a week, US Central calendar), a 1000-character message cap,
   a concurrency cap and a 180-second timeout. It caches deep-dive answers per
   building so a repeat costs nothing. After the model answers it runs a
   **final answer check**: every link is checked against links the agent actually
   saw that turn (made-up URLs are removed), and key facts are auto-bolded.
4. **Agent engine: Hermes Agent** (Nous Research, open source), pinned image
   version, running in the same container, reachable only from localhost behind
   an internal key.
5. **Model: DeepSeek V4 Flash** (`deepseek/deepseek-v4-flash`) via the DeepSeek API.
   Cheap and fast; tool-calling heavy.
6. **Tools (one custom plugin, read-only):**
   - `ps_schema` / `ps_sql`: one SELECT at a time against a read-only SQLite
     database built from CSV files at startup (SQLite authorizer blocks writes).
   - `ps_research_search` / `ps_research_read`: search and read the RealPage
     research folders (company, products, reviews, Reddit, news, competitors,
     AI visibility, and this document).
   - `ps_web_search` / `ps_web_read` (Jina) for deep dives on one building only.
   - No terminal, no file writes, no browser, no memory, no sub-agents. The agent
     cannot change anything; it can only look things up.
7. **Budget per question:** at most 14 model turns; normally at most 6 tool calls,
   up to 12 for a deep dive.

## The data behind it

- Buildings, software, sales, contacts and ranked leads for Plano + Richardson,
  TX, plus other areas (`state_leads`) from a data pipeline: public permit and
  county records, apartment websites, and a software detector that reads each
  building's website to find which property-management vendor (RealPage, Yardi,
  Entrata, AppFolio...) it runs.
- Data is baked into the container image at build time, so a data refresh is a
  redeploy.
- The pipeline itself has a review queue for low-confidence rows and accuracy
  notes (tables `cranesignal_pipeline_*`, `cranesignal_review_*`).

## How the answers are shaped

- The rules live in a prompt file (`SOUL.md`) plus a skill file listing every
  table and how to cite it.
- Fixed short layouts (about 40-60 words, sources line, bold key facts) for lead
  questions, because salespeople skim; a fixed deep-dive layout (who to call,
  phone, size, software, address, opening date, link row).
- Strict sourcing: every URL must come from the data or a page read that turn.
- Off-topic and prompt-injection requests get one fixed decline.

## Evals and testing (how we know it works)

- **Answer eval:** 100 saved test questions (leads, software, RealPage facts,
  off-topic, trick/injection questions) graded against a written rubric by an AI
  judge. Result on 2026-09-15: **92 of 100 correct**. The 8 misses: 7
  "scope-creep" (answered off-topic things like "capital of France" instead of
  declining) and 1 ambiguous question answered without saying which reading it used.
- **Judge vs human:** Drew hand-labelled 17 answers; the AI judge agreed with him
  on **94%** of them, which is why the judge is trusted for the rest.
- **Software hand check:** 10 of 10 hand-checked buildings had the right
  software vendor.
- **Six offline check suites:** secrets and code scan, site user flows (browser
  tests), a site attack scan, pipeline accuracy, chatbot answers, and the chatbot
  judge. In that saved 2026-09-15 run only the judge suite passed, because the
  others were mid-rework; it is historical evidence of the process, not a release
  sign-off. The finding review was noisy (about 85% false alarms), which is
  stated openly rather than hidden.
- **Unit tests** for the gateway: link guard, auto-bold, deep-dive cache, usage
  limits.
- **Live checks:** scripts ask the real deployed agent questions and check the
  answers and deep-dive clicks end to end.
- **Process rule:** nothing goes to GitHub or production until Drew has tried it
  himself locally; fixes are one small task per fresh AI session, each with its
  own check command.

## Safety and cost

- Read-only tools, internal key never exposed to the browser, strict CORS.
- Rate limits, daily cap and free-plan limits keep a public demo from running up
  a bill. Open WebUI's own background calls (titles, tags) don't count toward a
  user's free questions.

## Honest limits

- Answers are only as current as the last data build.
- Eval numbers are from one saved run (2026-09-15); newer changes need a fresh run.
- Answers are sent complete rather than word-by-word so the link check runs
  before anything shows on screen; that makes long answers feel slower.
- Software detection can miss buildings whose websites don't reveal a vendor.

## More

The source is public: https://github.com/Pu11en/realpage. The eval numbers this
page quotes are generated by `site/data/build_evals.py` and stored in
`site/data/evals.json`, so any figure here can be checked against the script that
produced it.

(There used to be an "Under the Hood" page at app.cranesignal.com. It was deleted on
2026-09-26: it rendered 8 visible words to anything that did not run JavaScript, so it
was never the readable source it claimed to be.)
