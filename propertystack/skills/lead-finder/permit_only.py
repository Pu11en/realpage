"""Fast, free permit-only pull: saved permit recipes -> scored leads -> site data.

No web searches (no websites, software or phones) -- those come from the full chain in run.py.
Data-first extras that need no web search: (a) recently-sold apartment
buildings from the state's county sales+parcel recipe (`find_sold`), and
(b) a not-yet-built permit's current owner from the same parcel file, by
address (`find_owner_by_parcel`) -- both free public records, never a search.
Usage: python3 propertystack/skills/lead-finder/permit_only.py --state AZ
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import run as chain
from lib.building_match import clean_project_name
from score_leads import score_and_rank

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder-sales"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder-contact"))
from find_sold import find_sold, default_fetch_rows  # noqa: E402
from contact import find_owner_by_parcel  # noqa: E402


def _cached_fetch_rows(source: dict, cache: dict) -> list[dict]:
    """`default_fetch_rows` downloads a whole county zip file; memoize by
    source URL so the same parcel/sales file is only fetched once per run,
    however many records need an owner lookup."""
    key = source.get("url", "")
    if key not in cache:
        cache[key] = default_fetch_rows(source)
    return cache[key]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state", required=True)
    args = p.parse_args(argv)
    state = args.state.upper()
    recipes = sorted((chain.HERE.parents[2] / "propertystack" / "recipes" / state.lower()).glob("*.json"))
    cities = []
    sales_recipe = None
    for r in recipes:
        data = json.loads(r.read_text())
        if "sales" in r.stem:
            sales_recipe = data
        elif data.get("city") and data.get("endpoint"):
            cities.append(data["city"])
    run_id = "permits-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    folder = chain.RunFolder(state=state, run_id=run_id)
    folder.ensure()
    deps = chain.ChainDeps(web=chain.WebHelper())
    parcel_cache: dict = {}
    fetch_rows = lambda source: _cached_fetch_rows(source, parcel_cache)  # noqa: E731
    records = []
    for city in cities:
        recipe = chain.step_sources(folder, city, state, deps)
        rows = chain.step_permits(folder, city, state, state.lower(), recipe, deps)
        got = chain._records_from(rows)
        for rec in got:
            if not rec.developer and sales_recipe:
                owner = find_owner_by_parcel(rec.address, sales_recipe, fetch_rows)
                if owner:
                    rec.developer = owner
        print(f"{city}: {len(got)} projects")
        records.extend(got)

    if sales_recipe:
        sold = find_sold(state.lower(), sales_recipe, fetch_rows)
        print(f"sold (county sales file): {len(sold)} properties")
        records.extend(sold)

    records = score_and_rank(chain.merge_records(records))
    for r in records:
        r.name = clean_project_name(r.name)
    path = chain.write_area_leads(state, records)
    print(f"permit-only: {len(records)} leads for {state} -> {path} (run {folder.path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
