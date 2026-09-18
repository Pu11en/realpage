---
name: query-propertystack
description: "Answer questions about CraneSignal buildings, software, sales, upcoming projects, leads and research data -- read-only, with citations."
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
| `ai_visibility_summary`, `ai_visibility_models`, `ai_visibility_competitors`, `ai_visibility_questions`, `ai_visibility_top_picks` | AI Visibility score snapshot | The read-only AI Visibility page data: overall score, model scores, competitor scores, top picks, and individual question outcomes. Use only for questions about vendor visibility in AI answers. State `generated_at` because it is a point-in-time score. |
| `ai_visibility_actions`, `ai_visibility_site_facts`, `ai_visibility_caveats` | AI Visibility recommended actions | Recommended website/content actions and caveats from the AI Visibility actions file. Use with the score tables when asked what vendors should fix for AI answers. State `based_on` because the recommendations depend on the tested dates. |

**Software scope:** only Plano and Richardson have software data (`software`, `master`, and the
Plano/Richardson rows of `state_leads`). Other areas' `software` is blank. Any vendor count or
"which vendor runs the most" answer must say it covers Plano and Richardson only.

Research files (01-company .. 09-ai-visibility) are searched with
`ps_research_search` and read with `ps_research_read`; in Sources, say
"Research notes" plus the topic (e.g. "Reddit comments").

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
