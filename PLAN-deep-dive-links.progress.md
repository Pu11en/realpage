# Progress: PLAN-deep-dive-links

## K1 Deep dive layout + link rules — done (commit f178b8d)
- SOUL.md: deep dive adds 📍 Address and 📅 Opens (or Sold) lines, then one link row
  (🗺️ Map · 📄 Permit · 📰 News · 🌐 Website, only links found). Link rules: URLs only from our
  data or pages/search results read this turn; Map built from the address; ~60 words excl. row.
  Web lookups now also look for address, opening date, permit/record page, website. Address
  rule loosened to allow web pages read this turn (deep dives).
- Rebuilt with dev.sh, cleared /opt/data/deep-dives/*.json, ran Sherman Street + Orchards by curl:
  both show address, date, link row; Sherman has Map · Permit (city council video) · News; all
  4 non-map URLs returned HTTP 200. Check command passes (17 tests, panel, readable).
- Open: Sherman's "Call" line still links TDLR there instead of in the row's Permit slot; bot
  once leaked "(7 words)" into Why now. Sources line still plain names (K2 fixes that).

## K1 fix — check command (2026-09-13)
- The bot runs `Check:` without a shell, so `&&` was passed to pytest as a filename and nothing ran.
- Wrapped the three checks in `tooling/qa/check-deep-dive.sh`; plan's Check line now calls that one script.
- Ran it: 17 tests pass, panel check clean, readable check OK (exit 0).

## K2 Clickable sources everywhere — done (commit a67aacd)
- SOUL.md: Sources line is short markdown links ([County sales record](url) · [News](url));
  our own data with no URL stays a plain name; never plain "(project record)"/"(news)" labels.
  Sale list items shortened to "sold <Mon year>", no buyer name (sold-list answer ran 62-65 words).
- check_answers.py: deep dive fails with no `](http` link; any Sources line naming
  record/news/website outside a link fails (our own "Say it as" names allowed); deep-dive limit 70
  words excluding link row and Sources.
- check-answers.sh: runs 1-2 failed only on sold-list length; after the rule fix, runs 4 and 5 both 5/5.
  Plan Check passes (17 tests, panel clean, readable OK).
- Open: the bot sometimes gives "County sales records" plain, sometimes a data.texas.gov link -- both allowed.

## K3 + fixes with Drew — done (2026-09-13, live session)
- Link guard: `chatbot/linkfix.py`; the plugin records every URL its tools return in
  `/opt/data/seen-urls.txt`; a link never seen is removed with its label (Maps links always OK).
- Labels come from the web address (Community Impact, Texas building record, "<City> city video").
- 📄 Permit = official building record (TDLR / city permit page; agenda only if none); never a video.
- Deep dives have no Sources line (link row covers it); normal answers keep Sources.
- 27 chatbot tests pass; real Sherman/Orchards deep dives + sold list checked.
