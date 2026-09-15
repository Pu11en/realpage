"""Fast, free permit-only pull: saved permit recipes -> scored leads -> site data.

No web searches (no websites, software or phones) -- those come from the full chain in run.py.
Data-first extras that need no web search: (a) recently-sold apartment
buildings from the state's county sales+parcel recipe (`find_sold`), and
(b) a not-yet-built permit's current owner from the same parcel file, by
address (`find_owner_by_parcel`) -- both free public records, never a search.

T6: every recipe under `recipes/<state>/` is dispatched by its own
`system` field (same dispatch table `lead-finder-permits/live_self_test.py`
uses to hit each recipe's real endpoint), not by filename or a single
city+endpoint shape -- so a state whose free sources are a statewide
registry, a statewide affordable-housing list, a county-wide bulk
permits/sales zip and a handful of per-city permit feeds all run through
this one entry point alongside a state with only plain per-city recipes.
A recipe with no `system` key (a plain per-city ArcGIS/Socrata recipe, or
a county sales+parcel file) keeps the original city+endpoint / "sales"
stem handling.

Save as you go (S0, extended to sources for T6): each source's records are
committed to the run folder + this area's `leads.json` right after that
source finishes, so a gowork build copy that deletes uncommitted files at
the end of a task never loses an already-pulled source's leads.

Usage: python3 propertystack/skills/lead-finder/permit_only.py --state AZ
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import run as chain
from lib.building_match import clean_project_name
from score_leads import score_and_rank

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder-sales"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder-contact"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder-permits"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder-tabs"))
from find_sold import find_sold, default_fetch_rows  # noqa: E402
from contact import find_owner_by_parcel  # noqa: E402
from appraisal_zip import find_new_apartment_projects, find_sold_apartments  # noqa: E402
from ckan_sql import ckan_sql_http_get  # noqa: E402
from houston_sold_permits import fetch_rows as houston_fetch_rows  # noqa: E402
from tad_sales import find_apartment_sales  # noqa: E402
from tad_zip import find_new_apartment_permits  # noqa: E402
from tdhca import find_new_affordable_projects  # noqa: E402
from tabs import default_fetch_detail, default_fetch_search, find_tabs_projects  # noqa: E402

REPO_ROOT = chain.HERE.parents[2]


def _cached_fetch_rows(source: dict, cache: dict) -> list[dict]:
    """`default_fetch_rows` downloads a whole county zip file; memoize by
    source URL so the same parcel/sales file is only fetched once per run,
    however many records need an owner lookup."""
    key = source.get("url", "")
    if key not in cache:
        cache[key] = default_fetch_rows(source)
    return cache[key]


def commit_source_progress(repo_root: Path, state: str, source_name: str) -> None:
    """Same save-as-you-go rule as `run.commit_city_progress`, one source
    (not one city) at a time -- a no-op, not an error, if there's nothing
    new to commit for this source."""
    data_dir = repo_root / "propertystack" / "data" / state.lower()
    runs_dir = repo_root / "propertystack" / "runs" / state.upper()
    paths = [str(data_dir), str(runs_dir)]
    subprocess.run(["git", "add", *paths], cwd=repo_root, check=True)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet", "--", *paths], cwd=repo_root)
    if staged.returncode == 0:
        return
    subprocess.run(
        ["git", "commit", "-m", f"lead-finder {state}: {source_name} done"],
        cwd=repo_root, check=True,
    )


def _records_for_city_recipe(city: str, recipe: dict, state: str, folder, deps, sales_recipe, fetch_rows):
    if recipe.get("system") == "ckan-sql":
        deps = chain.ChainDeps(web=deps.web, http_get_json=ckan_sql_http_get(recipe["endpoint"], recipe.get("sql", "")))
    elif recipe.get("system") == "houston-sold-permits-xlsx":
        rows = houston_fetch_rows(recipe)
        deps = chain.ChainDeps(web=deps.web, http_get_json=lambda _endpoint, _rows=rows: _rows)
    folder.save_step(chain.STEP_SOURCES, city, recipe)
    got_dicts = chain.step_permits(folder, city, state, state.lower(), recipe, deps)
    got = chain._records_from(got_dicts)
    for rec in got:
        if not rec.developer and sales_recipe:
            owner = find_owner_by_parcel(rec.address, sales_recipe, fetch_rows)
            if owner:
                rec.developer = owner
    return got


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state", required=True)
    args = p.parse_args(argv)
    state = args.state.upper()
    area = state.lower()
    recipes = sorted((REPO_ROOT / "propertystack" / "recipes" / area).glob("*.json"))

    run_id = "permits-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    folder = chain.RunFolder(state=state, run_id=run_id)
    folder.ensure()
    deps = chain.ChainDeps(web=chain.WebHelper())
    parcel_cache: dict = {}
    fetch_rows = lambda source: _cached_fetch_rows(source, parcel_cache)  # noqa: E731

    sales_recipe = None
    for r in recipes:
        data = json.loads(r.read_text())
        if data.get("system") is None and "sales" in r.stem:
            sales_recipe = data

    records: list = []

    def _commit_and_save(source_name: str) -> None:
        chain.write_area_leads(state, score_and_rank(chain.merge_records(records)))
        commit_source_progress(REPO_ROOT, state, source_name)

    for r in recipes:
        recipe = json.loads(r.read_text())
        system = recipe.get("system")
        if system is None and recipe.get("city") and recipe.get("endpoint"):
            got = _records_for_city_recipe(recipe["city"], recipe, state, folder, deps, sales_recipe, fetch_rows)
            print(f"{recipe['city']}: {len(got)} projects")
            records.extend(got)
            _commit_and_save(recipe["city"])
        elif system is None:
            continue  # the state's own sales+parcel recipe, handled below
        elif system == "tabs":
            got = find_tabs_projects(area, recipe, default_fetch_search, default_fetch_detail)
            print(f"TABS: {len(got)} statewide projects")
            records.extend(got)
            _commit_and_save("TABS")
        elif system == "tdhca-affordable":
            got = find_new_affordable_projects(area, recipe)
            print(f"TDHCA: {len(got)} affordable projects")
            records.extend(got)
            _commit_and_save("TDHCA")
        elif system == "county-appraisal-zip":
            got = find_new_apartment_permits(area, recipe)
            print(f"{recipe.get('county', r.stem)}: {len(got)} county permit projects")
            records.extend(got)
            _commit_and_save(recipe.get("county", r.stem))
        elif system == "tad-improved-sales-zip":
            got = find_apartment_sales(area, recipe)
            print(f"{recipe.get('county', r.stem)}: {len(got)} county sold projects")
            records.extend(got)
            _commit_and_save(recipe.get("county", r.stem))
        elif system == "appraisal-district-bulk-file":
            got = find_new_apartment_projects(area, recipe) + find_sold_apartments(area, recipe)
            print(f"{recipe.get('county', r.stem)}: {len(got)} appraisal-file projects")
            records.extend(got)
            _commit_and_save(recipe.get("county", r.stem))
        elif recipe.get("city") and recipe.get("endpoint"):
            got = _records_for_city_recipe(recipe["city"], recipe, state, folder, deps, sales_recipe, fetch_rows)
            print(f"{recipe['city']}: {len(got)} projects")
            records.extend(got)
            _commit_and_save(recipe["city"])

    if sales_recipe:
        sold = find_sold(area, sales_recipe, fetch_rows)
        print(f"sold (county sales file): {len(sold)} properties")
        records.extend(sold)
        _commit_and_save("county sales file")

    records = score_and_rank(chain.merge_records(records))
    for r in records:
        r.name = clean_project_name(r.name)
    path = chain.write_area_leads(state, records)
    commit_source_progress(REPO_ROOT, state, "final merge/score")
    print(f"permit-only: {len(records)} leads for {state} -> {path} (run {folder.path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
