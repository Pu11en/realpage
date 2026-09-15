"""T6 (second half): "Data first" web enrichment for an area's free-source
leads.json, capped and resumable.

`permit_only.py` gets every fact a public record already holds with no web
search at all. This script adds the two facts that only a search can find,
in the order the plan sets ("Data first, search last"):
(a) the software running on a building that's already leasing or sold
(`fill_software`, via `project_details.fill_project_details` filling the
website first -- both already gate on `record.stage in BUILT_STAGES`, so a
not-yet-built project's website is never searched); (b) a developer/owner's
office phone when the record didn't already have one (`fill_contacts`,
which never overwrites a phone/website already known).

Caps: stops before starting a new batch once the run's own Jina + Brave
search count reaches `--max-searches` (an area's own pre-approved search
budget), never mid-batch, and commits progress after every batch so a
capped-out or interrupted run keeps whatever it already enriched.

Usage: python3 propertystack/skills/lead-finder/enrich_leads.py --state <STATE> --max-searches <N>
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import run as chain
from lib.building_match import clean_project_name
from record import LeadRecord
from score_leads import score_and_rank

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder-details"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder-contact"))
import project_details  # noqa: E402
from contact import fill_contacts  # noqa: E402

BATCH_SIZE = 25
LOOKUP_WORKERS = 6  # S1: same rationale as run.py's chain -- WebHelper enforces the per-site gap
REPO_ROOT = chain.HERE.parents[2]


def _searches_so_far(web: chain.WebHelper) -> int:
    return web.counts.jina + web.counts.brave


def _commit(state: str, label: str) -> None:
    data_dir = REPO_ROOT / "propertystack" / "data" / state.lower()
    subprocess.run(["git", "add", str(data_dir)], cwd=REPO_ROOT, check=True)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet", "--", str(data_dir)], cwd=REPO_ROOT)
    if staged.returncode == 0:
        return
    subprocess.run(["git", "commit", "-m", f"lead-finder {state}: enrich {label}"], cwd=REPO_ROOT, check=True)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state", required=True)
    p.add_argument("--max-searches", type=int, default=1500)
    args = p.parse_args(argv)
    state = args.state.upper()

    data_dir = REPO_ROOT / "propertystack" / "data" / state.lower()
    leads_path = data_dir / "leads.json"
    records = [LeadRecord.from_dict(d) for d in json.loads(leads_path.read_text())]

    web = chain.WebHelper()
    already_built = [r for r in records if r.stage in project_details.BUILT_STAGES]
    still_needs_details = [r for r in already_built if not r.website]
    still_needs_phone = [r for r in records if not r.office_phone]

    by_id = {id(r): r for r in records}

    print(f"{len(still_needs_details)} built records missing a website, "
          f"{len(still_needs_phone)} records missing office_phone, "
          f"cap {args.max_searches} total searches")

    for i in range(0, len(still_needs_details), BATCH_SIZE):
        if _searches_so_far(web) >= args.max_searches:
            print(f"search cap reached ({_searches_so_far(web)}) -- stopping before website batch {i}")
            break
        batch = still_needs_details[i:i + BATCH_SIZE]
        with ThreadPoolExecutor(max_workers=LOOKUP_WORKERS) as pool:
            results = list(pool.map(
                lambda r: project_details.fill_project_details(r, web.search, lambda u: web.fetch(u), None),
                batch,
            ))
        for old, new in zip(batch, results):
            if new is not None:
                by_id[id(old)] = new
        print(f"website batch {i // BATCH_SIZE}: {_searches_so_far(web)} searches so far")
        chain.write_area_leads(state, score_and_rank(list(by_id.values())))
        _commit(state, f"website batch {i // BATCH_SIZE}")

    records = list(by_id.values())
    records = chain._load_software_run().fill_software(records, web)
    chain.write_area_leads(state, score_and_rank(records))
    _commit(state, "software")

    still_needs_phone = [r for r in records if not r.office_phone]
    for i in range(0, len(still_needs_phone), BATCH_SIZE):
        if _searches_so_far(web) >= args.max_searches:
            print(f"search cap reached ({_searches_so_far(web)}) -- stopping before phone batch {i}")
            break
        batch = still_needs_phone[i:i + BATCH_SIZE]
        fill_contacts(batch, web.search, lambda u: web.fetch(u))
        print(f"phone batch {i // BATCH_SIZE}: {_searches_so_far(web)} searches so far")
        chain.write_area_leads(state, score_and_rank(records))
        _commit(state, f"phone batch {i // BATCH_SIZE}")

    for r in records:
        r.name = clean_project_name(r.name)
    final = score_and_rank(records)
    path = chain.write_area_leads(state, final)
    _commit(state, "final")
    print(f"enrich-leads: {len(final)} leads for {state} -> {path}, {_searches_so_far(web)} total searches used")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
