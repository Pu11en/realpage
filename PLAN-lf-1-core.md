# PropertyStack lead finder, part 1: shared base

Part of the lead finder. **Read the rules in `PLAN-lead-finder.md` first** (area-agnostic: no place
names in code; Plano is never rerun; never guess facts; SearXNG first, Jina fallback; localhost only,
no push). **NOT approved to run yet.** **Runs first**; parts 2-5 start only after this is merged into `local-test`.

Run with: `Do the next unticked task in PLAN-lf-1-core.md, then tick it and stop.`
Check: `bash tooling/qa/check-lead-finder.sh`
Try: `bash tooling/dev.sh`
Open: (nothing new on the site yet -- this part is behind the scenes)

## How to try it (30 seconds)
1. Run the Check line: it passes, and it lists the lead-finder tests.
2. The old Plano-only tools (county building list, county sales, table-join, old scout) are gone; the Plano leads still show on Early Leads.
3. Stop a fake run halfway and start it again: it says which steps it is skipping because they are already done.

## Tasks

- [ ] **1.1 Skeleton + check + no-place-names test.** `propertystack/skills/lead-finder/`
  (`SKILL.md` describing the whole chain and the 6 plans; `run.py` stub). `tooling/qa/check-lead-finder.sh`
  runs every `tests/` under `propertystack/skills/lead-finder*/` and the other lead-finder skills,
  plus `check-panel.sh`, in under 2 minutes, no network. Test that **fails if any lead-finder step's
  code has a place name** (Plano, Richardson, Collin, Dallas, any US state or big-city literal).
  Delete the 4 old Plano-only skills (`find-apartments`, `find-sales`, `build-table`, `scout-areas`);
  Plano data files stay; check the site still builds. Commit.
- [ ] **1.2 One lead format.** `lead-finder/record.py` + `docs/LEAD-FORMAT.md`: one record per
  project/building used by every part: area, city, name, address, lat/lon, units, **stage**
  (planned / permitted / under construction / leasing / sold), permit date, opening date (or blank),
  sale date + buyer, developer/owner, office phone, website, software (RealPage / competitor name /
  not picked / unknown), links (map, permit, agenda, news, website), sources (URL per fact), why.
  Save/load as JSON per step; a sample state area under `propertystack/data/_sample/` (fake, clearly
  marked, never shown as a real area) for other parts' tests. Tests. Commit.
- [ ] **1.3 Web helper.** `lead-finder/fetch.py` used by every part: search = SearXNG
  (`tooling/searx_search.py`) first, Jina only if SearXNG returns nothing or is down; page reads via
  crawl4ai, Scrapling if blocked, Playwright last; every page cached on disk (never read twice); 2 s
  between visits to one site; 3 blocks → site marked skipped with the reason; every search counted
  (Jina logged separately). Fixture tests (fake SearXNG down, cache hit, 3 blocks). Commit.
- [ ] **1.4 Run folder, resume, caps, state pick.** `propertystack/runs/<state>/<run-id>/` with one
  file per step per city; rerunning skips finished steps. State = fewest RealPage buildings among
  the 15 fastest-growing (client-map `counts.json`). Caps: stop at **150 projects or ~450 searches**;
  **<30 projects → roll into the next state**, which becomes its own area. Fixture tests. Commit.
