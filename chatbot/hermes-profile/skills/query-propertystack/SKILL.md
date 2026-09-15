---
name: query-propertystack
description: "Answer questions about PropertyStack buildings, software, sales, upcoming projects, leads and the RealPage research folders -- read-only, with citations."
version: 1.0.0
author: realpage
platforms: [linux]
metadata:
  hermes:
    tags: [propertystack, realpage, sqlite, read-only]
---

# query-propertystack

The tools come from the `propertystack` plugin
(`hermes-profile/plugins/propertystack/`). At startup it loads every CSV in
`propertystack/data/plano-richardson/` into SQLite (one table per file), plus
every other area's `chat-leads.csv` (5.4) merged into one `state_leads` table,
plus the Street Talk posts (`propertystack/data/street-talk/street_talk.csv`) as `street_talk`.

| Table | Say it as (in Sources) | What it is |
|---|---|---|
| `apartments` | County property records | County-record buildings (204) |
| `websites` | Building websites | Official website per building + confidence |
| `software` | Software check (with proof link) | Detected vendor + `proof_url`, or `unknown` + reason |
| `sales` | County sales records | 28 recent sales from county deeds |
| `upcoming` | City permits and news | 14 pipeline projects (permits/news) |
| `master` | County property records + software check | 1+2+3 joined, one row per building |
| `leads` | PropertyStack lead ranking | 42 ranked Plano/Richardson leads, score parts + one-sentence `why` |
| `contacts` | Contact info from building websites | Phone/email scraped from websites, where found |
| `state_leads` | PropertyStack lead ranking | Every other tracked area's leads, one flat row each -- filter with `WHERE area='<slug>'` |
| `street_talk` | Reddit posts | What Texas people say on Reddit/YouTube: `part` = rivals / buildings / unhappy, `companies` (`LIKE '%Yardi%'`), `sentiment`, `city`, `building_id`, `warm_lead`. Quote briefly and **always link each post's `url`** (the real thread) |

Research files (01-company .. 09-ai-visibility) are searched with
`ps_research_search` and read with `ps_research_read`; in Sources, say
"RealPage research notes" plus the topic (e.g. "Reddit comments").

## Glossary -- never show the code, say the words

| Code | Say |
|---|---|
| `SWDNL` | special warranty deed (a sale) |
| `WDNL` | warranty deed (a sale) |
| `owner-change (no qualifying sale deed on file)` | owner changed, no sale deed on file |
| `signal` = `sold` / `upcoming` / `asset` | recently sold / new project / owner's other buildings |
| `software` = `unknown` | software not confirmed |
| `hop-portal` | resident portal link redirects to the vendor |
| `portal` | resident portal link on the website |
| `in-house-portal` | own-built resident portal |
| `no-portal-link` | no resident portal link on the website |
| `no-website` | no website found |
| `score_size`, `score_timing`, `score_signal`, `score_open` | size, timing, sales signal, software not locked in -- describe in words ("large and recently sold"), never "open 5" |
| `apt_id`, `ref_id`, `cad_prop_ids`, `cad_use_code` | internal -- don't show |

## Steps

1. `ps_schema` if you don't already know the columns.
2. `ps_sql` with one SELECT. Columns are TEXT -- `CAST(units AS INTEGER)` to sort or sum.
3. For research questions, `ps_research_search` then `ps_research_read` the best file.
4. Answer under the rules in SOUL.md: plain words (glossary above), one
   `**Sources**` list at the end instead of inline brackets, "I don't have
   that" when the data is silent, table for 3+ items, no invented numbers or
   contacts.

## Budget

One question, one answer. At most 6 tool calls. Read-only -- `ps_sql` rejects
anything but a single SELECT, and the database is opened read-only.
