# PropertyStack: deep dives you can click through (links, address, opening date)

Written 2026-09-13 with Drew (answers: `/home/drewp/main-projects/handoffs/2026-09-13-deep-dive-v3-plan-answers.md`).
Follows `PLAN-chat-finish.md` (done). Trigger: the Sherman Street deep dive gave a name, phone
and size but **no clickable links** ("(project record)", "(news)" were plain labels), no street
address and no opening date -- not enough to go on.

Decided: keep the same short deep dive on top, add **📍 address** and **📅 opens** lines, then
**one row of short links**: 🗺️ Map · 📄 Permit or county record · 📰 News · 🌐 Website -- each
only if actually found, never made up. Normal answers: every source becomes a clickable link,
nothing else changes. **Not wanted:** manager, developer's other buildings, call scripts.
Simple words, ADHD shape and ~40-word normal answers stay. Localhost only; no push.

Tasks touch `SOUL.md` / `proxy.py`: run in order, never in parallel with another chat plan.
Rebuild with `bash tooling/dev.sh` after each bot change (plain `docker restart` keeps old rules).

Run with: `Do the next unticked task in PLAN-deep-dive-links.md, then tick it and stop.`
Check: `python3 -m pytest -q chatbot/tests && bash tooling/qa/check-panel.sh && bash tooling/qa/check-readable.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765 → Early Leads → ✦ Deep dive

## How to try it (30 seconds)
1. Deep dive on "Apartment complex on Sherman Street, Richardson": it shows 📍 an address and
   📅 an opening date (or says it isn't public), then a row like 🗺️ Map · 📄 Permit · 📰 News.
2. Click each link: each opens a real page about that building (no dead or made-up links).
3. Ask "Which buildings sold recently?": the Sources line is clickable links, answer still short.

## Tasks

- [x] **K1 Deep dive layout + link rules.** In `chatbot/hermes-profile/SOUL.md` change the
  deep-dive layout to: the existing Call / Why now / Size+Software / Ask for lines, then
  `- **📍 Address:** <street, city>` and `- **📅 Opens:** <month year or "not public yet">`
  (sold buildings: `**Sold:** <date>` instead), then one line
  `🗺️ [Map](...) · 📄 [Permit](...) · 📰 [News](...) · 🌐 [Website](...)` with only the links
  found. Rules: every URL must come from our data or from a search result / page the bot
  actually read this turn -- never typed from memory; the Map link is built from the address as
  `https://www.google.com/maps/search/?api=1&query=<url-encoded address>`; the Permit link is
  the city/state/county record (e.g. the TDLR project page, the city agenda item, the county
  record); no link = leave it out. Deep dive stays ~60 words not counting the link row. Update
  the deep-dive web lookups to also look for the address, opening date, permit/record page and
  website. Clear saved deep dives (`/opt/data/deep-dives/*.json` in the chatbot container) so
  old ones don't replay. Rebuild; run the Sherman Street and Orchards deep dives by curl and
  read them. Commit.
- [ ] **K2 Clickable sources everywhere.** In `SOUL.md`: the `**Sources:**` line in every answer
  is short markdown links (`[County sales record](url) · [News](url)`), never plain labels like
  "(project record)" or "(news)"; our own data with no URL stays a plain name. Update
  `tooling/qa/check_answers.py`: fail a deep dive with no `](http` link, fail any answer whose
  Sources line names "record"/"news"/"website" without a link, deep-dive word limit ~70
  excluding the link row and Sources. Run `bash tooling/qa/check-answers.sh` (💲 a few cents)
  until it passes twice. Commit.
- [ ] **K3 Link guard (no made-up links).** The propertystack plugin
  (`chatbot/hermes-profile/plugins/propertystack/__init__.py`) appends every URL its tools
  return (data rows, research, web search results, pages read) to a seen-URLs file on the
  volume (`/opt/data/seen-urls.txt`, deduped, capped size). In `chatbot/proxy.py`, before an
  answer leaves (streamed, non-streamed, saved replays), turn any markdown link whose URL was
  never seen into plain text -- except Google Maps search links and our own site. Never change
  other text. Unit tests in `chatbot/tests/test_link_guard.py` (seen link kept, unseen link
  unlinked, maps link kept, link split across stream chunks). Rebuild; run `check-answers.sh`;
  click every link in one real deep dive in the panel. Commit. Tell Drew in plain words it's
  ready to try.
