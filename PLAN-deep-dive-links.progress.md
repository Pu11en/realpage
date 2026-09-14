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
