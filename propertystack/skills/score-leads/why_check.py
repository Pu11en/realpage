"""Flag leads.csv `why` lines that contain a number, year, or capitalized name-like token not
traceable to that lead's record in leads-facts.jsonl. Run after the agent's WHY step.

Usage: python3 skills/score-leads/why_check.py --area plano-richardson
"""
import argparse, csv, json, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from lib.paths import area_dir

NUMBER_RE = re.compile(r"\d[\d,]*")
# individual capitalized words -- candidate proper-noun tokens (checked one at a time so a
# sentence-leading word like "Sold" next to a real name doesn't get treated as one phrase)
NAME_WORD_RE = re.compile(r"\b[A-Z][a-zA-Z\'\.-]{2,}\b")
STOPWORDS = {"Sold", "Zoning", "Software", "Units", "Approved", "Opens", "Not", "Yet",
             "Under", "Site", "Plan", "Construction", "Leasing", "Filed", "Permit", "The",
             "Now", "New", "May", "Re-pick"}
MONTHS = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
          "January", "February", "March", "April", "June", "July", "August", "September",
          "October", "November", "December"}


def facts_blob(fact):
    """Flatten a facts record to one searchable string."""
    parts = []
    for k, v in fact.items():
        if isinstance(v, list):
            parts.extend(str(x) for x in v)
        else:
            parts.append(str(v))
    return " ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", required=True)
    a = ap.parse_args()
    d = area_dir(a.area)
    leads_f = d / "leads.csv"
    facts_f = d / "leads-facts.jsonl"
    if not leads_f.exists() or not facts_f.exists():
        print(f"MISSING: {leads_f} or {facts_f}")
        sys.exit(1)

    facts_by_id = {}
    for line in open(facts_f):
        fact = json.loads(line)
        facts_by_id[fact["ref_id"]] = fact

    problems = []
    with open(leads_f, newline="") as fh:
        rows = list(csv.DictReader(fh))

    for row in rows:
        why = row.get("why", "")
        if not why:
            problems.append(f"{row.get('ref_id')} ({row.get('name')}): empty why")
            continue
        fact = facts_by_id.get(row.get("ref_id"))
        if not fact:
            problems.append(f"{row.get('ref_id')}: no facts record found")
            continue
        blob = facts_blob(fact)

        blob_lower = blob.lower()
        for m in NUMBER_RE.finditer(why):
            num = m.group().replace(",", "")
            if num not in blob and m.group() not in blob:
                problems.append(f"{row.get('ref_id')} ({row.get('name')}): "
                                 f"number '{m.group()}' not found in facts -- why: {why!r}")

        for m in NAME_WORD_RE.finditer(why):
            word = m.group()
            if word in STOPWORDS or word in MONTHS:
                continue
            if word.lower() not in blob_lower:
                problems.append(f"{row.get('ref_id')} ({row.get('name')}): "
                                 f"name-like token '{word}' not found in facts -- why: {why!r}")

        if len(why.split()) > 25:
            problems.append(f"{row.get('ref_id')} ({row.get('name')}): "
                             f"why is {len(why.split())} words, over the 25-word limit")

    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print(f" - {p}")
        sys.exit(1)
    else:
        print(f"OK: {len(rows)} leads checked, no problems found.")


if __name__ == "__main__":
    main()
