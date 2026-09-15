"""Fast, free permit-only pull: saved permit recipes -> scored leads -> site data.

No web searches (no websites, software or phones) -- those come from the full chain in run.py.
Usage: python3 propertystack/skills/lead-finder/permit_only.py --state AZ
"""
import argparse
import json
from datetime import datetime, timezone

import run as chain
from lib.building_match import clean_project_name
from score_leads import score_and_rank


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state", required=True)
    args = p.parse_args(argv)
    state = args.state.upper()
    recipes = sorted((chain.HERE.parents[2] / "propertystack" / "recipes" / state.lower()).glob("*.json"))
    cities = []
    for r in recipes:
        data = json.loads(r.read_text())
        if data.get("city") and data.get("endpoint") and "sales" not in r.stem:
            cities.append(data["city"])
    run_id = "permits-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    folder = chain.RunFolder(state=state, run_id=run_id)
    folder.ensure()
    deps = chain.ChainDeps(web=chain.WebHelper())
    records = []
    for city in cities:
        recipe = chain.step_sources(folder, city, state, deps)
        rows = chain.step_permits(folder, city, state, state.lower(), recipe, deps)
        got = chain._records_from(rows)
        print(f"{city}: {len(got)} projects")
        records.extend(got)
    records = score_and_rank(chain.merge_records(records))
    for r in records:
        r.name = clean_project_name(r.name)
    path = chain.write_area_leads(state, records)
    print(f"permit-only: {len(records)} leads for {state} -> {path} (run {folder.path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
