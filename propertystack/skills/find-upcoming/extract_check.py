"""Validate data/<area>/6-upcoming.csv against CONTRACTS.md. Run after the agent's EXTRACT
step. Prints problems; exits 1 if any found.

Usage: python3 skills/find-upcoming/extract_check.py --area plano-richardson
"""
import argparse, csv, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from lib.paths import area_dir

REQUIRED_COLS = ["project_id", "project", "address", "city", "units", "developer", "stage",
                  "stage_date", "expected_open", "source_type", "source_url", "first_seen"]
ALLOWED_STAGES = {"zoning-filed", "zoning-approved", "site-plan-approved", "permit",
                   "under-construction", "leasing"}
ALLOWED_CITIES = {"Plano", "Richardson"}


def norm_addr(s):
    return "".join(c for c in (s or "").lower() if c.isalnum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", required=True)
    a = ap.parse_args()
    f = area_dir(a.area) / "6-upcoming.csv"
    if not f.exists():
        print(f"MISSING: {f}")
        sys.exit(1)

    problems = []
    with open(f, newline="") as fh:
        r = csv.DictReader(fh)
        missing_cols = [c for c in REQUIRED_COLS if c not in (r.fieldnames or [])]
        if missing_cols:
            problems.append(f"missing columns: {missing_cols}")
        extra_cols = [c for c in (r.fieldnames or []) if c not in REQUIRED_COLS]
        if extra_cols:
            problems.append(f"unexpected columns: {extra_cols}")
        rows = list(r)

    seen_addrs = {}
    seen_ids = set()
    for i, row in enumerate(rows, start=2):  # 1-indexed + header
        pid = row.get("project_id", "")
        if not pid:
            problems.append(f"row {i}: empty project_id")
        elif pid in seen_ids:
            problems.append(f"row {i}: duplicate project_id '{pid}'")
        seen_ids.add(pid)

        if not row.get("project"):
            problems.append(f"row {i}: empty project name")

        stage = row.get("stage", "")
        if stage not in ALLOWED_STAGES:
            problems.append(f"row {i} ({row.get('project')}): invalid stage '{stage}'")

        city = row.get("city", "")
        if city not in ALLOWED_CITIES:
            problems.append(f"row {i} ({row.get('project')}): city '{city}' not in {ALLOWED_CITIES}")

        if not row.get("source_url"):
            problems.append(f"row {i} ({row.get('project')}): missing source_url")

        source_type = row.get("source_type", "")
        if source_type not in {"legistar", "tabs", "news", "city"}:
            problems.append(f"row {i} ({row.get('project')}): invalid source_type '{source_type}'")

        units = row.get("units", "")
        if units and not units.isdigit():
            problems.append(f"row {i} ({row.get('project')}): units '{units}' not numeric/blank")

        addr = norm_addr(row.get("address"))
        if addr:
            if addr in seen_addrs:
                problems.append(
                    f"row {i} ({row.get('project')}): duplicate address with row "
                    f"{seen_addrs[addr]} ({rows[seen_addrs[addr]-2].get('project')})")
            else:
                seen_addrs[addr] = i

    if problems:
        print(f"{len(problems)} problem(s) in {f}:")
        for p in problems:
            print(f" - {p}")
        sys.exit(1)
    else:
        print(f"OK: {len(rows)} rows in {f}, no problems found.")


if __name__ == "__main__":
    main()
