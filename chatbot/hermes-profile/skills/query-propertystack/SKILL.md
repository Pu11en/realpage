---
name: query-propertystack
description: "Answer questions about CraneSignal buildings, software, sales, upcoming projects, and leads -- read-only, with citations."
version: 1.0.0
author: cranesignal
platforms: [linux]
metadata:
  hermes:
    tags: [propertystack, cranesignal, sqlite, read-only]
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
| `leads` | CraneSignal lead ranking | 42 ranked Plano/Richardson leads, score parts + one-sentence `why` |
| `contacts` | Contact info from building websites | Phone/email scraped from websites, where found |
| `state_leads` | CraneSignal lead ranking | Every tracked state's leads, one flat row each -- filter with `WHERE area='<slug>'`. Texas (`tx`) also holds the 42 Plano/Richardson leads (region Dallas–Fort Worth), so counts match the site: count a state or region here only, never add `leads` on top |
| `street_talk` | Reddit posts | What Texas people say on Reddit/YouTube: `part` = rivals / buildings / unhappy, `companies` (`LIKE '%Yardi%'`), `sentiment`, `city`, `building_id`, `warm_lead`. Quote briefly, always `SELECT` the `url` column, and put **each post's `url` as a link on the same line as its claim**; say how many posts the answer uses ("from 2 posts"); a row with no `url` is left out, never quoted |
| `dallas_buildings`, `dallas_websites`, `dallas_software`, `dallas_sales`, `dallas_contacts` | Dallas-area building survey | A separate Dallas-wide building survey, **not leads** -- never add these buildings/units to a Texas or Dallas-Fort Worth lead count. `dallas_software` is almost all `unknown` (not checked yet), so don't use it for vendor market share. |
| `map_summary` | CraneSignal lead map | One row per state/top-city pair, matching the site's lead map exactly -- use this (not `state_leads`) for "which state/city has the most leads" so the numbers match the map. `state_total` repeats per city row (don't sum it across a state's own rows). |
| `software_share` | Property software market share (Plano/Richardson only) | The site's vendor market-share chart -- one row per vendor with `properties`, `units`, `pct_of_identified_properties` already computed. Same Plano/Richardson-only scope as `software`/`master`; never present it as covering any other area. |
| `building_extras` | Building owner, sale and lead detail (Plano/Richardson only) | One row per building (join to `master` on `apt_id`) with `owner`, `website_confidence`, `unknown_reason` (same values as `master`, no join needed), plus `sale_date`/`sale_new_owner`/`sale_previous_owner` and `lead_rank`/`lead_total_leads`/`lead_why` -- blank when that building has no sale or isn't a ranked lead (most of them). |
| `cranesignal_pipeline_steps`, `cranesignal_pipeline_runs`, `cranesignal_review_reasons`, `cranesignal_review_queue`, `cranesignal_accuracy_docs` | CraneSignal build pipeline and review notes | CraneSignal's own pipeline counts, run history, accuracy links, and review queue from the Under the Hood page. Use only for questions about CraneSignal itself (how it was built or checked), not for property/lead/software facts. |
| `cranesignal_how_tested`, `cranesignal_chat_stats`, `cranesignal_eval_summary`, `cranesignal_eval_failure_types`, `cranesignal_buildbot_summary`, `cranesignal_buildbot_examples` | CraneSignal measurements | How CraneSignal was built and tested (start here for "how do you know it works?"), chat timing, eval results, failure types, and AI build-agent progress from the Under the Hood page. These rows have `measured_at` dates; state the date because eval numbers may be old. |

**Software scope:** only Plano and Richardson have software data (`software`, `master`, and the
Plano/Richardson rows of `state_leads`). Other areas' `software` is blank. Any vendor count or
"which vendor runs the most" answer must say it covers Plano and Richardson only.

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
3. Follow SOUL.md's layout and glossary: deep dives start with **Who to call**
   and inline source links; other answers end with `**Sources:**`. Use lead
   lines for lists, not tables. Show matching data before describing gaps;
   never invent numbers or contacts.

## Deep dive: who to call

For research or a contact request about one building:

1. **Our data first.** Match the building by name and city/address. For any
   tracked area, query its `state_leads` row, including `office_phone` (the
   site's `officePhone`), `website`, `website_link`, `developer`, `buyer`,
   `permit_link`, `news_link` and `agenda_link`. For Plano/Richardson, also
   use the relevant `leads`, `master`, `upcoming`, `contacts`, `sales` and
   `building_extras` rows. Use schema column names, not CSV filenames as
   table names: `sales` is loaded from `5-sales.csv`. Contact evidence is in
   `contacts.source_url`; sale evidence is in `sales.source_url`, paired
   with `new_owner`. `building_extras.sale_new_owner` is another buyer field.
2. **Fill the gaps.** After the saved data, use `ps_web_search` and
   `ps_web_read` if available to find the management company, office phone,
   official website and role to ask for. Prefer the building/manager's own
   site for contact details. Match the city/address, not just a similar
   name. Use saved `developer` as a research lead or a sourced developer
   fallback; do not relabel a developer as the management company. Label
   permit office phones as **(permit contact)**.
3. **Recent sale.** Include **New owner** even if the user did not separately
   ask for it. Use `buyer`, `sales.new_owner` or `sale_new_owner` from our
   data first, with the record/article that identifies that buyer. If the
   buyer or its evidence is missing, search county deed/property records
   or sale news for this building and sale. Never substitute `previous_owner`,
   the developer, or an undated `owner` value for the buyer.
4. **Answer contact-first.** Use SOUL.md's short **Who to call** block with
   Company, Office phone, Website and Ask for (role), then New owner for a
   sale, before Why now. Each contact/owner value must have its own source
   link beside it, including phones/websites from our data. Use only a URL
   in the queried data or a search result/page read this turn that supports
   that specific value; merely sharing a row with a permit/news URL is not
   proof. A verified official website can link to itself. If no supporting
   source is found, retain the field with **not found** and no invented link.
   Never guess a number or infer a role. Keep found details when others are
   missing, and answer with these explicit gaps if web tools are unavailable
   or the budget is exhausted.

## Budget

One question, one answer. Ordinary questions: at most 6 tool calls.
Deep dives: at most 6 web searches and 12 tool calls total, counting schema,
SQL, searches and page reads; stop early once the requested details are
sourced. Read-only -- `ps_sql` rejects anything but a single SELECT, and the
database is opened read-only.
