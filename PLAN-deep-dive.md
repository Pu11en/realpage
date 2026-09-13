# PropertyStack: the deep dive (designed here first, then given to the site chat)

Written 2026-09-12 (sell-plan H7–H11). The site's chat agent does the deep dive in the
conversation, but **first we pin down exactly what it outputs** by building it as a skill in
this local harness and running it on real leads until Drew likes it. Then the same recipe goes
into the site agent. Localhost only; no push.

**The fixed layout (every deep dive, in this order):**
1. **Bottom line** (first, 2–4 bullets: call or not, why, who to ask for)
2. **Who they are** (name, city, units, owner, manager, current software + proof link)
3. **Why now** (sale, new manager, lease-up, resident complaints about portal/payments, each with a link)
4. **Who to ask for** (the regional/operations person at the management company from **public
   pages only**, with the link; never guessed emails or phones; "not found" if not found)
5. **30-second opener** (uses "[your name], [your company]"; never claims RealPage)
6. **3 questions**
7. **2 objections + answers**
8. **Sources** (every link used)

Taking it away: **text in the chat + the chat's Copy button** (no PDF).

Run with: `Do the next unticked task in PLAN-deep-dive.md, then tick it and stop.`
Check: `python3 propertystack/skills/deep-dive/validate.py --self-test`
Try: in this harness, "Use the deep-dive skill on Vantage At Spring Creek"
Open: `propertystack/data/plano-richardson/briefs/` (local) · http://localhost:8765 → Ask (after D4)

## How to try it (30 seconds)
1. Open the Vantage brief: Bottom line first, then the 7 sections in order, links everywhere.
2. "Who to ask for" names a real person with a public link, or clearly says not found.
3. After D4: in the site chat, "Deep dive on Vantage At Spring Creek" gives the same layout.

## Tasks

- [x] **D1 Validator.** `propertystack/skills/deep-dive/validate.py`: given a brief (markdown
  file or text), checks the 8 headings exist **in order**, every "Why now" and "Who to ask for"
  line has a URL, no email/phone appears unless it's in `contacts.csv`, and the opener doesn't
  say "with RealPage". `--self-test` runs it on 1 good + 3 bad fixture briefs. Fails first, commit.
- [ ] **D2 The skill.** `propertystack/skills/deep-dive/SKILL.md`: inputs (area + lead `ref_id`
  or name), steps (pull the lead's rows from `leads.csv`/`master.csv`/`5-sales.csv`/`contacts.csv`;
  web: owner/manager, resident reviews, news; public page for the decision-maker; crawl4ai at
  `http://localhost:11235` for reading, Jina for search, max ~12 searches per brief), the layout
  above, and the write-out: `propertystack/data/<area>/briefs/<ref_id>.md`. Upcoming projects:
  same layout, "Who they are" = developer + opening date, software = "not chosen yet".
- [ ] **D3 Run it on 3 real leads (💲 ~36 searches).** Vantage At Spring Creek (sold, on Yardi),
  Legacy Arapaho (upcoming, 443 units), Creekside At Legacy (runs RealPage, just sold: the "at
  risk" case). All three pass `validate.py`. **Stop and show Drew the three briefs in plain words;
  apply his changes to SKILL.md before D4.**
- [ ] **D4 Give it to the site agent.** **Blocked** until Drew has OK'd the D3 briefs (noted under
  this task) **and** every task in PLAN-chat-readable.md and PLAN-team-memory.md is ticked; if
  not, change nothing and stop with a one-line note. Runs **after** PLAN-chat-readable and PLAN-team-memory
  (all three edit `SOUL.md`). Copy the layout + rules into `chatbot/hermes-profile/SOUL.md` (deep
  dives lead with Bottom line) and the query-propertystack skill; rebuild with `bash
  tooling/dev.sh`; ask the local bot "Deep dive on Vantage At Spring Creek" through
  `http://localhost:18080/v1/chat/completions` (header `X-OpenWebUI-User-Email: admin@localhost`,
  key `local-trial-key-change-me`); the answer passes `validate.py`. Then tell Drew in plain
  words it's ready to try in the site chat.
