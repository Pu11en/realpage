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
`propertystack/data/plano-richardson/` into SQLite, one table per file.

| Table | Cite as | What it is |
|---|---|---|
| `apartments` | `[1-apartments.csv]` | County-record buildings (204) |
| `websites` | `[2-websites.csv]` | Official website per building + confidence |
| `software` | `[3-software.csv]` | Detected vendor + `proof_url`, or `unknown` + reason |
| `sales` | `[5-sales.csv]` | 28 recent sales from county deeds |
| `upcoming` | `[6-upcoming.csv]` | 14 pipeline projects (permits/news) |
| `master` | `[master.csv]` | 1+2+3 joined, one row per building |
| `leads` | `[leads.csv]` | 42 ranked leads, score parts + one-sentence `why` |
| `contacts` | `[contacts.csv]` | Phone/email scraped from websites, where found |

Research files (01-company .. 08-voice-of-customer) are searched with
`ps_research_search` and read with `ps_research_read`; cite as `[04-reddit/index.md]`.

## Steps

1. `ps_schema` if you don't already know the columns.
2. `ps_sql` with one SELECT. Columns are TEXT -- `CAST(units AS INTEGER)` to sort or sum.
3. For research questions, `ps_research_search` then `ps_research_read` the best file.
4. Answer under the rules in SOUL.md: cite every claim, "I don't have that" when
   the data is silent, table for 3+ items, no invented numbers or contacts.

## Budget

One question, one answer. At most 6 tool calls. Read-only -- `ps_sql` rejects
anything but a single SELECT, and the database is opened read-only.
