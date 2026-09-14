# Progress log: PLAN-lead-finder-build

## 1.1 Skeleton + check + no-place-names test -- done

- Created `propertystack/skills/lead-finder/` with `SKILL.md` (describes all 6 parts,
  area-agnostic rule, caps) and a `run.py` stub (`--state`, `--run-id` args, not yet wired).
- Added `propertystack/skills/lead-finder/tests/test_no_place_names.py`: scans every
  `propertystack/skills/lead-finder*/**/*.py` (excluding fixtures and the test file itself)
  for literal US state names and a list of big cities/counties (including Plano, Richardson,
  Collin, Dallas); fails the check if any show up. Data files (csv/json) are exempt by design
  -- only code is scanned.
- Added `tooling/qa/check-lead-finder.sh`: runs pytest on every `lead-finder*/tests` dir plus
  `tooling/qa/check-panel.sh`, matching the pattern used by `check-client-map.sh`.
- Deleted the 4 old Plano-only skills: `propertystack/skills/{find-apartments,find-sales,
  build-table,scout-areas}` (code only -- checked first that nothing else in the repo imports
  their code; their historical run JSON files under `propertystack/runs/` and the Dallas data
  in `propertystack/data/dallas-parked/` were left alone since `site/data/build_data.py` reads
  those run files by skill name, not the skill code).
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (2 tests + panel check clean).
  Also ran `python3 site/data/build_data.py` directly to confirm the site still builds after
  the deletions -- it does (properties, leads, pipeline, client-map all wrote fine).
- Nothing left open for this task. Next task (1.2) adds the actual lead record format and
  `docs/LEAD-FORMAT.md`.

## 1.2 One lead format -- done

- Added `propertystack/skills/lead-finder/record.py`: `LeadRecord` dataclass with every field
  from the plan (area, city, name, address, lat/lon, units, stage, permit_date, opening_date,
  sale_date, buyer, developer, office_phone, website, software, links, sources, why),
  `STAGE_ORDER`/`stage_rank` for planned < permitted < under construction < leasing < sold,
  `save_records`/`load_records` for JSON round-trips, `normalize_address` (self-contained --
  no `usaddress` dependency, since it's not installed and there's no venv/requirements file in
  this repo to add it to; wrote a small suffix/unit-word normalizer instead that passes the
  plan's example: "123 Main St" and "123 Main Street Bldg B" normalize the same), and
  `haversine_meters` for the 75m geocode check.
- Added `propertystack/skills/lead-finder/merge.py`: `same_building()` (normalized address
  match, or within 75m + shared developer/name word) and `merge_records()` (one record per
  building, keeps the most advanced stage, keeps every source and link from both records --
  a planned project that gets a permit is upgraded in place, not duplicated).
- Added `docs/LEAD-FORMAT.md` describing every field and the merge rules.
- Added `propertystack/data/_sample/leads.json` (+ README marking it clearly fake) -- two
  fixture records for later parts' tests, never built into the real site.
- Tests: `tests/test_record.py` (stage ordering, address normalization incl. the tricky
  "123 Main St" vs "123 Main Street Bldg B" pair, save/load round-trip, sample fixture loads)
  and `tests/test_merge.py` (address match, geocode+name match, geocode-without-shared-name
  stays separate, far-apart stays separate, stage upgrade keeps all sources/links, distinct
  buildings stay distinct, planned-then-permitted upgrades not duplicates).
- Checked: `bash tooling/qa/check-lead-finder.sh` -- 17 tests pass (was 2), panel check clean.
  Also reran `python3 site/data/build_data.py` to confirm the site still builds unaffected.
- Nothing left open. Next task (1.3) adds the web helper (SearXNG/Jina search + cached page
  reads).
