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


def build_properties_and_share() -> tuple[list[dict], dict]:
    rows = read_csv(MASTER_CSV)

    properties = []
    for r in rows:
        properties.append({
            "id": r["apt_id"],
            "community": r["name"],
            "city": r["city"],
            "address": r["address"],
            "units": int(r["units"]) if r["units"] else None,
            "yearBuilt": int(r["year_built"]) if r["year_built"] else None,
            "owner": r["owner"],
            "software": r["software"] or None,
            "proof": r["proof_url"] or None,
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


def build_leads() -> dict:
    rows = read_csv(LEADS_CSV)
    upcoming_rows = read_csv(UPCOMING_CSV)

    leads = []
    for r in rows:
        software = r["software"]
        if software in ("not chosen yet", "unknown", ""):
            software = None
        sources = []
        for tag in (source_tag(u.strip()) for u in r["sources"].split(";") if u.strip()):
            if tag not in sources:
                sources.append(tag)
        leads.append({
            "id": f"l{r['rank']}",
            "score": int(r["score"]),
            "property": r["name"],
            "city": r["city"],
            "units": int(r["units"]) if r["units"] else None,
            "signalType": "Upcoming" if r["signal"] == "upcoming" else "Sold",
            "signal": short_signal(r["signal"], r["why"]),
            "software": software,
            "why": r["why"],
            "sources": sources,
            "isNew": False,
        })

    units_in_play = sum(l["units"] or 0 for l in leads)

    today = date.today()
    horizon = today + timedelta(days=365)
    opening_next_12mo = 0
    for r in upcoming_rows:
        if not r["expected_open"]:
            continue
        try:
            opens = date.fromisoformat(r["expected_open"])
        except ValueError:
            continue
        if today <= opens <= horizon:
            opening_next_12mo += 1

    return {
        "stats": {
            "leads": len(leads),
            "newThisWeek": 0,
            "unitsInPlay": units_in_play,
            "openingNext12mo": opening_next_12mo,
        },
        "leads": leads,
    }


def build_pipeline(properties_stats: dict) -> dict:
    run_files = sorted(glob.glob(str(RUNS_DIR / "*.json")))
    runs_by_skill: dict[str, list[dict]] = {}
    for path in run_files:
        with open(path) as f:
            run = json.load(f)
        run["_runId"] = Path(path).stem
        runs_by_skill.setdefault(run["skill"], []).append(run)

    def latest(skill: str) -> dict | None:
        return runs_by_skill[skill][-1] if runs_by_skill.get(skill) else None

    n_apartments = properties_stats["apartments"]
    n_identified = properties_stats["softwareIdentified"]
    website_checked = None
    bt = latest("build-table")
    if bt:
        website_checked = bt["counts"].get("checked")

    steps = [
        {"name": "find-apartments", "count": n_apartments},
        {"name": "find-website", "count": website_checked},
        {"name": "detect-software", "count": n_identified},
        {"name": "build-table", "count": n_apartments},
        {"name": "leads", "count": latest("score-leads")["counts"]["total_leads"] if latest("score-leads") else None},
    ]

    final_run = bt or latest("find-apartments")
    runs = []
    if final_run:
        pct = round(100 * n_identified / n_apartments, 1) if n_apartments else 0
        runs.append({
            "runId": final_run["_runId"],
            "area": final_run["area"],
            "propertiesProcessed": n_apartments,
            "pctIdentified": pct,
            "costUsd": None,
            "durationSec": final_run["duration_s"] or None,
            "models": "not logged per run yet -- see propertystack/runs/*.json",
        })

    return {
        "steps": steps,
        "runs": runs,
        "accuracy": {
            "correct": 0,
            "total": 0,
            "note": "PLACEHOLDER -- no hand-check log exists yet.",
        },
        "costPerArea": {"note": "PLACEHOLDER -- no real run-cost tracking yet."},
        "reviewQueue": {
            "status": "PLACEHOLDER",
            "rows": [],
        },
    }


def main() -> None:
    properties, properties_json, share_json = build_properties_and_share()
    (OUT_DIR / "properties.json").write_text(json.dumps(properties_json, indent=2))
    (OUT_DIR / "software-share.json").write_text(json.dumps(share_json, indent=2))

    leads_json = build_leads()
    (OUT_DIR / "leads.json").write_text(json.dumps(leads_json, indent=2))

    pipeline_json = build_pipeline(properties_json["stats"])
    (OUT_DIR / "pipeline.json").write_text(json.dumps(pipeline_json, indent=2))

    print(f"wrote properties.json ({len(properties)} rows)")
    print(f"wrote software-share.json ({len(share_json['share'])} vendors)")
    print(f"wrote leads.json ({len(leads_json['leads'])} leads)")
    print(f"wrote pipeline.json")


if __name__ == "__main__":
    main()
