#!/usr/bin/env python3
"""Rebuild site/data/*.json from the real PropertyStack pipeline output.

Sources (see propertystack/CONTRACTS.md):
  propertystack/data/plano-richardson/master.csv  -> properties.json, software-share.json
  propertystack/data/plano-richardson/leads.csv   -> leads.json
  propertystack/data/plano-richardson/6-upcoming.csv -> leads.json (openingNext12mo)
  propertystack/runs/*.json                       -> pipeline.json (Under the Hood)

Run this any time master.csv / leads.csv / runs/*.json change.
No dependencies beyond stdlib. Usage: python3 site/data/build_data.py
"""
import csv
import glob
import json
import re
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = "plano-richardson"
DATA_DIR = ROOT / "propertystack" / "data" / AREA
RUNS_DIR = ROOT / "propertystack" / "runs"
OUT_DIR = Path(__file__).resolve().parent

MASTER_CSV = DATA_DIR / "master.csv"
LEADS_CSV = DATA_DIR / "leads.csv"
UPCOMING_CSV = DATA_DIR / "6-upcoming.csv"
CONTACTS_CSV = DATA_DIR / "contacts.csv"
CONTACTS_DALLAS_CSV = DATA_DIR / "contacts-dallas.csv"
LEADS_FACTS_JSONL = DATA_DIR / "leads-facts.jsonl"
SALES_CSV = DATA_DIR / "5-sales.csv"
SALES_DALLAS_CSV = DATA_DIR / "5-sales-dallas.csv"

TODAY = date.fromisoformat("2026-09-10")  # matches score-leads' fixed TODAY, see run.py

VENDOR_COLORS = {
    "RealPage": "#f472b6",
    "Yardi": "#60a5fa",
    "Entrata": "#fb923c",
    "Yotta": "#c084fc",
    "AppFolio": "#facc15",
    "ResMan": "#22d3ee",
    "MRI/RentManager": "#34d399",
    "in-house:Camden": "#94a3b8",
    "in-house:UDR": "#fca5a5",
    "unknown": "#52525b",
}


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def lead_score(r: dict) -> dict:
    return {
        "rank": int(r["rank"]),
        "total": int(r["score"]),
        "size": int(r["score_size"]),
        "timing": int(r["score_timing"]),
        "signal": int(r["score_signal"]),
        "open": int(r["score_open"]),
        "why": r["why"],
    }


def split_urls(s: str) -> list[str]:
    return [u.strip() for u in s.split(";") if u.strip()]


def build_properties_and_share() -> tuple[list[dict], dict]:
    rows = read_csv(MASTER_CSV)
    leads_by_ref = {r["ref_id"]: r for r in read_csv(LEADS_CSV)}
    sale_files = [SALES_CSV] + ([SALES_DALLAS_CSV] if SALES_DALLAS_CSV.exists() else [])
    sales = {r["apt_id"]: r for f in sale_files for r in read_csv(f)}
    contacts = load_contacts()

    properties = []
    for r in rows:
        sale = sales.get(r["apt_id"])
        lead = leads_by_ref.get(r["apt_id"])
        properties.append({
            "id": r["apt_id"],
            "community": r["name"],
            "city": r["city"],
            "county": r.get("county") or "Collin",
            "address": r["address"],
            "units": int(r["units"]) if r["units"] else None,
            "yearBuilt": int(r["year_built"]) if r["year_built"] else None,
            "owner": r["owner"],
            "software": r["software"] or None,
            "proof": r["proof_url"] or None,
            # Page 4 (Property Detail) fields
            "website": r["website"] or None,
            "websiteConfidence": r["website_confidence"] or None,
            "checkedAt": r["checked_at"] or None,
            "unknownReason": r["unknown_reason"] or None,
            "contact": contacts.get(r["apt_id"]),
            "sale": {
                "date": sale["sale_date"],
                "newOwner": sale["new_owner"],
                "previousOwner": sale["previous_owner"],
                "source": sale["source_url"] or None,
            } if sale else None,
            "lead": lead_score(lead) if lead else None,
            "sources": split_urls(lead["sources"]) if lead else [],
        })

    upcoming = []
    for r in read_csv(UPCOMING_CSV):
        lead = leads_by_ref.get(r["project_id"])
        upcoming.append({
            "id": r["project_id"],
            "community": r["project"],
            "city": r["city"],
            "address": r["address"],
            "units": int(r["units"]) if r["units"] else None,
            "developer": r["developer"] or None,
            "stage": r["stage"],
            "stageDate": r["stage_date"] or None,
            "expectedOpen": r["expected_open"] or None,
            "sourceType": r["source_type"],
            "lead": lead_score(lead) if lead else None,
            "sources": split_urls(lead["sources"]) if lead else split_urls(r["source_url"]),
        })

    total_units = sum(p["units"] or 0 for p in properties)
    identified = [p for p in properties if p["software"] and p["software"] != "unknown"]
    not_checked = sum(1 for r in rows if r["unknown_reason"] == "no-website")
    checked = len(properties) - not_checked
    vendor_counts = Counter(p["software"] for p in identified)
    top_vendor = vendor_counts.most_common(1)[0][0] if vendor_counts else None

    properties_json = {
        "generatedFrom": "propertystack/data/plano-richardson/master.csv",
        "stats": {
            "apartments": len(properties),
            "totalUnits": total_units,
            "softwareIdentified": len(identified),
            "softwareIdentifiedPct": round(100 * len(identified) / len(properties), 1),
            "topSoftware": top_vendor,
        },
        "funnel": {
            "inArea": len(properties),
            "websiteFound": checked,
            "checked": checked,
            "identified": len(identified),
            "unknown": len(properties) - len(identified),
        },
        "vendorColors": VENDOR_COLORS,
        "properties": properties,
        "upcoming": upcoming,
    }

    share = []
    for vendor, count in vendor_counts.most_common():
        vendor_units = sum(p["units"] or 0 for p in identified if p["software"] == vendor)
        share.append({
            "vendor": vendor,
            "color": VENDOR_COLORS.get(vendor, "#52525b"),
            "properties": count,
            "units": vendor_units,
            "pctOfIdentifiedProperties": round(100 * count / len(identified), 1) if identified else 0,
        })

    share_json = {
        "generatedFrom": "propertystack/data/plano-richardson/master.csv",
        "note": "changeSinceLastRun is not tracked yet -- needs a second run to diff against.",
        "share": share,
    }

    return properties, properties_json, share_json


SOLD_DATE_RE = re.compile(r"^(Sold \S+ \d{4})")


def short_signal(signal: str, why: str) -> str:
    if signal == "sold":
        m = SOLD_DATE_RE.match(why)
        return m.group(1) if m else why.split(" · ")[0]
    return why.split(" · ")[0].split(" → ")[0].strip()


def source_tag(url: str) -> str:
    if "data.texas.gov" in url:
        return "county record"
    if "legistar" in url or "zabalist.com" in url:
        return "permit"
    if any(d in url for d in ("communityimpact.com", "dallasnews.com", "candysdirt.com")):
        return "news"
    return "website"


def load_leads_facts() -> dict:
    facts = {}
    with open(LEADS_FACTS_JSONL) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            facts[d["ref_id"]] = d
    return facts


def load_contacts() -> dict:
    contacts = {}
    contact_files = [CONTACTS_CSV] + ([CONTACTS_DALLAS_CSV] if CONTACTS_DALLAS_CSV.exists() else [])
    for f in contact_files:
        for r in read_csv(f):
            if r["phone"] or r["email"]:
                contacts[r["apt_id"]] = {
                    "phone": r["phone"] or None,
                    "email": r["email"] or None,
                }
    return contacts


def build_leads() -> dict:
    rows = read_csv(LEADS_CSV)
    facts = load_leads_facts()
    contacts = load_contacts()

    leads = []
    for r in rows:
        software = r["software"]
        if software in ("not chosen yet", "unknown", ""):
            software = None
        sources = []
        for tag in (source_tag(u.strip()) for u in r["sources"].split(";") if u.strip()):
            if tag not in sources:
                sources.append(tag)

        ref_id = r["ref_id"]
        is_sold = r["signal"] == "sold"
        fact = facts.get(ref_id, {})

        # isNew: sale/stage happened within the last 30 days of TODAY.
        date_str = fact.get("sale_date") if is_sold else fact.get("stage_date")
        is_new = False
        if date_str:
            try:
                is_new = (TODAY - date.fromisoformat(date_str)).days <= 30
            except ValueError:
                is_new = False

        # Sold leads -> apt_id; upcoming leads -> project_id (properties.json "upcoming").
        property_id = ref_id
        contact = contacts.get(ref_id) if is_sold else None

        leads.append({
            "id": f"l{r['rank']}",
            "propertyId": property_id,
            "score": int(r["score"]),
            "property": r["name"],
            "city": r["city"],
            "units": int(r["units"]) if r["units"] else None,
            "signalType": "Upcoming" if r["signal"] == "upcoming" else "Sold",
            "signal": short_signal(r["signal"], r["why"]),
            "software": software,
            "why": r["why"],
            "sources": sources,
            "contact": contact,
            "isNew": is_new,
        })

    units_in_play = sum(l["units"] or 0 for l in leads)
    new_count = sum(1 for l in leads if l["isNew"])

    horizon = TODAY + timedelta(days=365)
    opening_soon_units = 0
    for r in read_csv(UPCOMING_CSV):
        if r["stage"] not in ("leasing", "under-construction"):
            continue
        if not r["units"]:
            continue
        opens_ok = True
        if r["expected_open"]:
            try:
                opens_ok = TODAY <= date.fromisoformat(r["expected_open"]) <= horizon
            except ValueError:
                opens_ok = True
        if opens_ok:
            opening_soon_units += int(r["units"])

    return {
        "stats": {
            "leads": len(leads),
            "newThisWeek": new_count,
            "unitsInPlay": units_in_play,
            "openingNext12mo": opening_soon_units,
        },
        "leads": leads,
    }


REPO_BLOB = "https://github.com/Pu11en/realpage/blob/main/"


def summarize_counts(counts: dict) -> str:
    """Flatten a run's top-level scalar counts into a short 'k=v' string."""
    parts = [f"{k}={v}" for k, v in counts.items() if isinstance(v, (int, float, str))]
    sw = counts.get("software")
    if isinstance(sw, dict) and "identified" not in counts:
        parts.append(f"identified={sum(v for k, v in sw.items() if k != 'unknown')}")
        parts.append(f"unknown={sw.get('unknown', 0)}")
    return ", ".join(parts)


def build_pipeline(properties: list[dict]) -> dict:
    run_files = sorted(glob.glob(str(RUNS_DIR / "*.json")))
    runs_by_skill: dict[str, list[dict]] = {}
    runs = []
    for path in run_files:
        with open(path) as f:
            run = json.load(f)
        runs_by_skill.setdefault(run["skill"], []).append(run)
        runs.append({
            "runId": Path(path).stem,
            "started": run.get("started"),
            "skill": run["skill"],
            "area": run.get("area"),
            "status": run.get("status"),
            "counts": summarize_counts(run.get("counts", {})),
            "errors": len(run.get("errors", [])),
            "durationSec": run.get("duration_s"),
        })
    runs.reverse()  # newest first

    def latest_counts(skill: str) -> dict:
        return runs_by_skill[skill][-1]["counts"] if runs_by_skill.get(skill) else {}

    bt = latest_counts("build-table")
    sales = latest_counts("find-sales")
    leads = latest_counts("score-leads")
    steps = [
        {"name": "find-apartments", "label": "buildings", "count": bt.get("in_area")},
        {"name": "find-website", "label": "with websites", "count": bt.get("website_found")},
        {"name": "detect-software", "label": "software identified", "count": bt.get("identified")},
        {"name": "find-sales", "label": "recent sales", "count": sales.get("sold")},
        {"name": "find-upcoming", "label": "upcoming projects", "count": leads.get("upcoming_leads")},
        {"name": "score-leads", "label": "ranked leads", "count": leads.get("total_leads")},
    ]

    queue = [
        {
            "id": p["id"],
            "community": p["community"],
            "city": p["city"],
            "units": p["units"],
            "reason": p["unknownReason"] or "unknown",
            "website": p["website"],
        }
        for p in properties
        if not p["software"] or p["software"] == "unknown"
    ]
    queue.sort(key=lambda r: (r["reason"] != "no-website", -(r["units"] or 0)))

    return {
        "steps": steps,
        "runs": runs,
        "accuracy": {
            "reviewDoc": REPO_BLOB + "propertystack/evals/review-weak-spots.md",
            "spotcheckDoc": REPO_BLOB + "propertystack/evals/manual-spotcheck-2026-09-10.md",
        },
        "costPerArea": {"note": "PLACEHOLDER -- run logs record API call counts, not dollars."},
        "reviewQueue": {
            "byReason": dict(Counter(r["reason"] for r in queue).most_common()),
            "rows": queue,
        },
    }


def main() -> None:
    properties, properties_json, share_json = build_properties_and_share()
    (OUT_DIR / "properties.json").write_text(json.dumps(properties_json, indent=2))
    (OUT_DIR / "software-share.json").write_text(json.dumps(share_json, indent=2))

    leads_json = build_leads()
    (OUT_DIR / "leads.json").write_text(json.dumps(leads_json, indent=2))

    pipeline_json = build_pipeline(properties)
    (OUT_DIR / "pipeline.json").write_text(json.dumps(pipeline_json, indent=2))

    print(f"wrote properties.json ({len(properties)} rows)")
    print(f"wrote software-share.json ({len(share_json['share'])} vendors)")
    print(f"wrote leads.json ({len(leads_json['leads'])} leads)")
    print(f"wrote pipeline.json")


if __name__ == "__main__":
    main()
