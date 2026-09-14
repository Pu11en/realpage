#!/usr/bin/env python3
"""lead-finder entry point (Part 6.1: wire the full chain).

Area-agnostic: takes the state to run as an argument, never a literal in
code. Runs every part-2/3/4 step in order for one state, city by city, and
writes each step's output to the run folder (`runfolder.RunFolder`) so a
rerun with the same `--run-id` resumes instead of redoing finished work.

Investigation for this task turned up no step that needs a human-in-the-loop
"to-read" queue: every lead-finder-* module already does its own page
classification with plain code (regexes for units/case numbers/addresses,
keyword windows for agenda packets, vendor-marker matching for software).
Each of those modules takes its web/search/fetch calls as injected callables
rather than doing network I/O itself, so this file supplies real ones (via
`fetch.WebHelper` for search/page reads, plain urllib helpers for the JSON/
bytes API calls a few steps need) and calls each module's already-tested
function directly. See the 6.1 progress-log entry for the full reasoning.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent
for _extra in (
    "lead-finder-cities", "lead-finder-sources", "lead-finder-permits",
    "lead-finder-details", "lead-finder-hud", "lead-finder-awards",
    "lead-finder-agendas", "lead-finder-legistar", "lead-finder-civic",
    "lead-finder-agenda-projects", "lead-finder-sales-news",
    "lead-finder-contact", "score-leads",
):
    p = SKILLS / _extra
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from runfolder import RunFolder, RunCaps, pick_state  # noqa: E402
from record import LeadRecord  # noqa: E402
from merge import merge_records  # noqa: E402
from fetch import WebHelper  # noqa: E402
from quality import check_quality, write_quality_json  # noqa: E402

import rank as cities_rank  # noqa: E402
import find_sources  # noqa: E402
import find_sources_fallback  # noqa: E402
import find_upcoming  # noqa: E402
import project_details  # noqa: E402
import hud_loans  # noqa: E402
import awards as awards_mod  # noqa: E402
import agendas as agendas_mod  # noqa: E402
import legistar as legistar_mod  # noqa: E402
import civic_agendas  # noqa: E402
import agenda_projects  # noqa: E402
import sales_news  # noqa: E402


def _load_software_run():
    """lead-finder-software/run.py is also named `run.py`, so it can't be
    `import run`-ed without clashing with this module's own name -- load it
    by path under a distinct module name instead."""
    path = SKILLS / "lead-finder-software" / "run.py"
    spec = importlib.util.spec_from_file_location("lead_finder_software_run", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CITIES_DATA_DIR = HERE.parents[2] / "propertystack" / "data"

STEP_CITIES = "cities"
STEP_SOURCES = "sources"
STEP_PERMITS = "permits"
STEP_DETAILS = "details"
STEP_HUD = "hud"
STEP_AWARDS = "awards"
STEP_AGENDAS = "agendas"
STEP_LEGISTAR = "legistar"
STEP_CIVIC = "civic"
STEP_AGENDA_PROJECTS = "agenda-projects"
STEP_SALES = "sales"
STEP_MERGED = "merged"
STEP_SOFTWARE = "software"
STEP_CONTACT = "contact"
STEP_SCORE = "score"

STATE_CITY_KEY = "_state"


def _http_get_json(url: str):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def _http_get_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def _census_geocode(query: str):
    url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?" + urllib.parse.urlencode(
        {"address": query, "benchmark": "Public_AR_Current", "format": "json"}
    )
    return _http_get_json(url)


@dataclass
class ChainDeps:
    """Every network-touching callable the chain steps need, injectable so
    tests never hit the network. `web` (fetch.WebHelper) handles search and
    cached page reads; the rest are plain JSON/bytes HTTP GETs for the
    steps that talk to an API directly instead of reading a web page."""

    web: WebHelper
    http_get_json: Callable[[str], object] = _http_get_json
    http_get_bytes: Callable[[str], bytes] = _http_get_bytes
    geocode_fn: Callable[[str], object] = _census_geocode
    gdelt_fetch_fn: Callable[[str], bytes] | None = None
    cities_fetcher: Callable | None = None  # rank.py's `fetcher`, Census BPS files
    hud_fetcher: Callable[[], bytes] | None = None  # zero-arg, returns the HUD workbook bytes
    agency_name: str | None = None  # state housing finance agency, for awards (3.2)
    legistar_clients: dict = field(default_factory=dict)  # city -> legistar client slug
    ocr_fn: Callable[[bytes], str] | None = None
    today: object = None  # injectable "today" for deterministic tests
    recipes_dir: Path | None = None  # override for find_sources/find_sources_fallback/agendas

    def search_fn(self, query: str, n: int = 10) -> list[dict]:
        return self.web.search(query, n)

    def fetch_html(self, url: str) -> str:
        result = self.web.fetch(url)
        return result.html if result.ok else ""


def _skip(city: str, state: str, reason: str) -> dict:
    return {"city": city, "state": state, "skipped": True, "reason": reason}


def _run_step(run_folder: RunFolder, step: str, city: str, fn) -> object:
    """Resumable single step: skip if this step already has output for this
    city, else run `fn()` and save the result (or a skip note on error)."""
    if run_folder.step_done(step, city):
        return run_folder.load_step(step, city)
    try:
        result = fn()
    except Exception as exc:  # every chain step must be resumable, never fatal
        result = _skip(city, run_folder.state, f"{step} failed: {exc}")
    run_folder.save_step(step, city, result)
    return result


def _records_from(data) -> list[LeadRecord]:
    if isinstance(data, dict) and data.get("skipped"):
        return []
    if data is None:
        return []
    return [d if isinstance(d, LeadRecord) else LeadRecord.from_dict(d) for d in data]


# -- per-city steps --------------------------------------------------------


def step_sources(run_folder: RunFolder, city: str, state: str, deps: ChainDeps) -> dict:
    def _do():
        kwargs = {"recipes_dir": deps.recipes_dir} if deps.recipes_dir else {}
        if deps.today is not None:
            kwargs["today"] = deps.today
        recipe = find_sources.find_sources(city, state, deps.http_get_json, **kwargs)
        if recipe is not None:
            return recipe
        recipe = find_sources_fallback.find_sources_fallback(
            city, state, deps.search_fn, deps.fetch_html, **kwargs
        )
        return recipe or _skip(city, state, "no permit data source found")

    return _run_step(run_folder, STEP_SOURCES, city, _do)


def step_permits(run_folder: RunFolder, city: str, state: str, area: str, recipe: dict, deps: ChainDeps) -> list:
    def _do():
        if recipe.get("skipped"):
            return []
        records = find_upcoming.find_upcoming(
            city, state, area, recipe, deps.http_get_json, today=deps.today
        )
        return [r.to_dict() for r in records]

    return _run_step(run_folder, STEP_PERMITS, city, _do)


def step_details(run_folder: RunFolder, city: str, records: list[LeadRecord], deps: ChainDeps) -> list:
    def _do():
        filled = []
        for record in records:
            result = project_details.fill_project_details(
                record, deps.search_fn, lambda u: deps.web.fetch(u), deps.geocode_fn
            )
            if result is not None:
                filled.append(result.to_dict())
        return filled

    return _run_step(run_folder, STEP_DETAILS, city, _do)


def step_agendas(run_folder: RunFolder, city: str, state: str, deps: ChainDeps) -> dict:
    def _do():
        kwargs = {"recipes_dir": deps.recipes_dir} if deps.recipes_dir else {}
        return agendas_mod.find_meeting_system(city, state, deps.search_fn, deps.fetch_html, **kwargs)

    return _run_step(run_folder, STEP_AGENDAS, city, _do)


def step_legistar(run_folder: RunFolder, city: str, state: str, area: str, recipe: dict, deps: ChainDeps) -> list:
    def _do():
        if recipe.get("system") != "legistar":
            return []
        client = deps.legistar_clients.get(city)
        if not client:
            return {"city": city, "state": state, "skipped": True, "reason": "no legistar client configured"}
        result = legistar_mod.find_legistar_matters(
            city, state, area, client, deps.http_get_json, today=deps.today
        )
        if isinstance(result, dict):
            return result
        return [r.to_dict() for r in result]

    return _run_step(run_folder, STEP_LEGISTAR, city, _do)


def step_civic(run_folder: RunFolder, city: str, state: str, area: str, recipe: dict, deps: ChainDeps) -> list:
    def _do():
        if recipe.get("system") not in civic_agendas.SUPPORTED_SYSTEMS:
            return []
        hits = civic_agendas.find_civic_agenda_items(
            city, state, recipe, deps.http_get_bytes, ocr_fn=deps.ocr_fn
        )
        if isinstance(hits, dict):
            return hits
        projects = agenda_projects.agenda_hits_to_projects(hits, area, city)
        return [r.to_dict() for r in projects]

    return _run_step(run_folder, STEP_CIVIC, city, _do)


def step_sales(run_folder: RunFolder, city: str, area: str, deps: ChainDeps) -> list:
    def _do():
        records = sales_news.find_sales_news(
            city, area, deps.search_fn, gdelt_fetch_fn=deps.gdelt_fetch_fn, today=deps.today
        )
        return [r.to_dict() for r in records]

    return _run_step(run_folder, STEP_SALES, city, _do)


# -- state-level steps ------------------------------------------------------


def step_hud(run_folder: RunFolder, state: str, deps: ChainDeps) -> list:
    def _do():
        if deps.hud_fetcher is None:
            return _skip(STATE_CITY_KEY, state, "no HUD workbook fetcher configured")
        records = hud_loans.find_hud_loans(state, today=deps.today, fetcher=deps.hud_fetcher)
        return [r.to_dict() for r in records]

    return _run_step(run_folder, STEP_HUD, STATE_CITY_KEY, _do)


def step_awards(run_folder: RunFolder, state: str, deps: ChainDeps) -> list:
    def _do():
        if not deps.agency_name:
            return _skip(STATE_CITY_KEY, state, "no housing finance agency name configured")
        records = awards_mod.find_awards(
            state, deps.agency_name, deps.search_fn, deps.http_get_bytes, today=deps.today
        )
        return [r.to_dict() for r in records]

    return _run_step(run_folder, STEP_AWARDS, STATE_CITY_KEY, _do)


# -- orchestration ------------------------------------------------------


def load_or_build_cities(run_folder: RunFolder, state: str, deps: ChainDeps, cities: list[str] | None) -> list[str]:
    """Step 1: cities. If a city list is given explicitly, use it (also true
    for the sample fixture, which has no Census data behind it). Otherwise
    rank the state's cities from the Census Building Permits Survey (2.1),
    resumed from run_folder like every other step."""
    if cities is not None:
        run_folder.save_step(STEP_CITIES, STATE_CITY_KEY, {"cities": cities, "source": "explicit"})
        return list(cities)

    if run_folder.step_done(STEP_CITIES, STATE_CITY_KEY):
        data = run_folder.load_step(STEP_CITIES, STATE_CITY_KEY)
        return [c["city"] for c in data.get("cities", [])]

    if deps.cities_fetcher is None:
        raise ValueError("no city list given and no cities_fetcher configured")
    out = cities_rank.rank_cities(state, fetcher=deps.cities_fetcher)
    run_folder.save_step(STEP_CITIES, STATE_CITY_KEY, out)
    return [c["city"] for c in out["cities"]]


def run_chain(
    state: str,
    run_folder: RunFolder,
    deps: ChainDeps,
    cities: list[str] | None = None,
) -> list[LeadRecord]:
    """Run every step of the lead-finder chain for `state`, resumably, and
    return the final scored/ranked list of LeadRecords."""
    area = state.lower()
    city_list = load_or_build_cities(run_folder, state, deps, cities)

    all_records: list[LeadRecord] = []
    caps = run_folder.load_caps()

    for city in city_list:
        if caps.any_cap_hit():
            print(f"lead-finder: cap hit ({caps.project_count} projects, "
                  f"{caps.total_searches} searches) -- stopping before {city}")
            break

        recipe = step_sources(run_folder, city, state, deps)
        permit_dicts = step_permits(run_folder, city, state, area, recipe, deps)
        permit_records = _records_from(permit_dicts)

        detailed_dicts = step_details(run_folder, city, permit_records, deps)
        detailed_records = _records_from(detailed_dicts)

        agenda_recipe = step_agendas(run_folder, city, state, deps)
        legistar_data = step_legistar(run_folder, city, state, area, agenda_recipe, deps)
        civic_data = step_civic(run_folder, city, state, area, agenda_recipe, deps)
        sales_dicts = step_sales(run_folder, city, area, deps)

        city_records = (
            detailed_records
            + _records_from(legistar_data)
            + _records_from(civic_data)
            + _records_from(sales_dicts)
        )
        merged_city = merge_records(city_records)
        run_folder.save_step(STEP_MERGED, city, [r.to_dict() for r in merged_city])
        all_records.extend(merged_city)

        caps.project_count = len(merge_records(all_records))
        counts = getattr(deps.web, "counts", None)
        if counts is not None:
            caps.jina_searches = counts.jina
            caps.brave_searches = counts.brave
        run_folder.save_caps(caps)

    hud_dicts = step_hud(run_folder, state, deps)
    award_dicts = step_awards(run_folder, state, deps)
    all_records.extend(_records_from(hud_dicts))
    all_records.extend(_records_from(award_dicts))

    merged = merge_records(all_records)

    if not run_folder.step_done(STEP_SOFTWARE, STATE_CITY_KEY):
        merged = _load_software_run().fill_software(merged, deps.web)
        run_folder.save_step(STEP_SOFTWARE, STATE_CITY_KEY, [r.to_dict() for r in merged])
    else:
        merged = _records_from(run_folder.load_step(STEP_SOFTWARE, STATE_CITY_KEY))

    if not run_folder.step_done(STEP_CONTACT, STATE_CITY_KEY):
        from contact import fill_contacts

        merged = fill_contacts(merged, deps.search_fn, lambda u: deps.web.fetch(u))
        run_folder.save_step(STEP_CONTACT, STATE_CITY_KEY, [r.to_dict() for r in merged])
    else:
        merged = _records_from(run_folder.load_step(STEP_CONTACT, STATE_CITY_KEY))

    if not run_folder.step_done(STEP_SCORE, STATE_CITY_KEY):
        from score_leads import score_and_rank

        merged = score_and_rank(merged)
        run_folder.save_step(STEP_SCORE, STATE_CITY_KEY, [r.to_dict() for r in merged])
    else:
        merged = _records_from(run_folder.load_step(STEP_SCORE, STATE_CITY_KEY))

    return merged


def cities_with_real_source(run_folder: RunFolder, city_list: list[str]) -> int:
    """Count cities whose `sources` step found a real (non-skipped) permit
    recipe, for F9's quality report."""
    count = 0
    for city in city_list:
        if not run_folder.step_done(STEP_SOURCES, city):
            continue
        recipe = run_folder.load_step(STEP_SOURCES, city)
        if isinstance(recipe, dict) and not recipe.get("skipped"):
            count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", help="two-letter state code or slug to run")
    parser.add_argument("--run-id", help="resume an existing run folder")
    parser.add_argument("--city", action="append", help="run only these cities (repeatable)")
    args = parser.parse_args(argv)

    if args.state:
        state = args.state
    else:
        pick = pick_state()
        state = pick["state"]
        print(f"picked state: {state} (backup order: {pick['backup_order']})")

    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_folder = RunFolder(state=state, run_id=run_id)
    run_folder.ensure()
    print(f"lead-finder: run folder ready at {run_folder.path}")

    agencies_path = HERE.parents[2] / "propertystack" / "data" / "state-agencies.json"
    agencies = json.loads(agencies_path.read_text()) if agencies_path.exists() else {}

    deps = ChainDeps(
        web=WebHelper(),
        cities_fetcher=cities_rank.fetch,
        hud_fetcher=hud_loans.fetch_workbook_bytes,
        agency_name=agencies.get(state.upper()),
    )
    records = run_chain(state, run_folder, deps, cities=args.city)
    print(f"lead-finder: {len(records)} leads for {state} -> {run_folder.path}")

    city_list = run_folder.load_step(STEP_CITIES, STATE_CITY_KEY)["cities"]
    city_names = [c["city"] if isinstance(c, dict) else c for c in city_list]
    real_sources = cities_with_real_source(run_folder, city_names)
    report = check_quality(state, records, real_sources, len(city_names))
    write_quality_json(run_folder.path, report)

    if not report["passed"]:
        print(f"lead-finder: FAILED quality bar for {state}: {report['fail_reasons']}")
        print("lead-finder: not built into the site")
        return 1

    leads_path = write_area_leads(state, records)
    print(f"lead-finder: wrote {len(records)} records to {leads_path}")
    return 0


def write_area_leads(state: str, records: list[LeadRecord], data_dir: Path | None = None) -> Path:
    """Write a state's final scored records to `propertystack/data/<slug>/leads.json`
    (part-1 format, 1.2) so `site/data/build_data.py` (5.1) picks the area up."""
    data_dir = data_dir or (HERE.parents[2] / "propertystack" / "data")
    area_dir = data_dir / state.lower()
    area_dir.mkdir(parents=True, exist_ok=True)
    leads_path = area_dir / "leads.json"
    leads_path.write_text(json.dumps([r.to_dict() for r in records], indent=1))
    return leads_path


if __name__ == "__main__":
    raise SystemExit(main())
