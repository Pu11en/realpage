"""Skill 7 — score-leads, GATHER+SCORE phase: read master.csv, 5-sales.csv, 6-upcoming.csv,
produce one lead per sold community and per upcoming project, score each 0-100, and write
data/<area>/leads.csv (why left empty) + data/<area>/leads-facts.jsonl (facts the agent's WHY
step is allowed to use -- no other facts).

This script makes NO prose judgment calls -- it only computes the score and lays out the
sourced facts. The one-sentence `why` per lead is written by the agent in the EXTRACT-style
WHY step documented in SKILL.md, using only facts from leads-facts.jsonl.

Usage: python3 skills/score-leads/run.py --area plano-richardson
"""
import argparse, csv, datetime as dt, json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from lib.paths import area_dir
from lib.runlog import RunLog

TODAY = dt.date.fromisoformat("2026-09-10")

UPCOMING_STAGE_SCORE = {
    "zoning-filed": 30, "zoning-approved": 28, "site-plan-approved": 26,
    "permit": 22, "under-construction": 18, "leasing": 10,
}
COLS = ["rank", "score", "score_size", "score_timing", "score_signal", "score_open",
        "signal", "ref_id", "name", "city", "units", "software", "why", "sources"]


def score_size(units):
    if not units:
        return 15
    try:
        u = int(units)
    except ValueError:
        return 15
    return round(min(u, 400) / 400 * 40)


def score_timing_sold(sale_date):
    try:
        d = dt.date.fromisoformat(sale_date)
    except (ValueError, TypeError):
        return 0
    days = (TODAY - d).days
    if days <= 90:
        return 30
    if days <= 180:
        return 20
    if days <= 365:
        return 12
    if days <= 730:
        return 5
    return 0


def score_open(software):
    sw = (software or "").strip().lower()
    if sw in ("", "unknown", "not checked", "not chosen yet"):
        return 15
    return 5


def read_csv(path):
    if not path.exists():
        return []
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def build_sold_leads(sales_rows, master_by_id, log):
    leads, facts = [], []
    for s in sales_rows:
        apt_id = s["apt_id"]
        m = master_by_id.get(apt_id, {})
        units = s.get("units") or m.get("units") or ""
        software = m.get("software") or "unknown"
        sz, tm, sg, op = score_size(units), score_timing_sold(s.get("sale_date")), 15, score_open(software)
        total = sz + tm + sg + op
        sources = [u for u in (s.get("source_url"), m.get("proof_url")) if u]
        lead = {
            "score": total, "score_size": sz, "score_timing": tm, "score_signal": sg,
            "score_open": op, "signal": "sold", "ref_id": apt_id,
            "name": s.get("name") or m.get("name") or "", "city": m.get("city", ""),
            "units": units, "software": software, "why": "", "sources": ";".join(sources),
        }
        leads.append(lead)
        facts.append({
            "ref_id": apt_id, "signal": "sold", "name": lead["name"], "city": lead["city"],
            "units": units, "software": software, "sale_date": s.get("sale_date", ""),
            "new_owner": s.get("new_owner", ""), "previous_owner": s.get("previous_owner", ""),
            "deed_type": s.get("deed_type", ""), "source": s.get("source", ""),
            "sources": sources,
        })
    return leads, facts


def build_upcoming_leads(upcoming_rows, log):
    leads, facts = [], []
    for p in upcoming_rows:
        stage = p.get("stage", "")
        sz = score_size(p.get("units"))
        tm = UPCOMING_STAGE_SCORE.get(stage, 0)
        sg, op = 15, score_open("not chosen yet")
        total = sz + tm + sg + op
        sources = [u for u in (p.get("source_url"),) if u]
        lead = {
            "score": total, "score_size": sz, "score_timing": tm, "score_signal": sg,
            "score_open": op, "signal": "upcoming", "ref_id": p.get("project_id", ""),
            "name": p.get("project", ""), "city": p.get("city", ""), "units": p.get("units", ""),
            "software": "not chosen yet", "why": "", "sources": ";".join(sources),
        }
        leads.append(lead)
        facts.append({
            "ref_id": p.get("project_id", ""), "signal": "upcoming", "name": lead["name"],
            "city": lead["city"], "units": p.get("units", ""), "software": "not chosen yet",
            "stage": stage, "stage_date": p.get("stage_date", ""),
            "expected_open": p.get("expected_open", ""), "developer": p.get("developer", ""),
            "source_type": p.get("source_type", ""), "sources": sources,
        })
    return leads, facts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", required=True)
    a = ap.parse_args()
    with RunLog("score-leads", a.area) as log:
        d = area_dir(a.area)
        master_rows = read_csv(d / "master.csv")
        # Combine Collin sales with the optional second-county (Dallas) sales file,
        # rather than duplicating this script per county.
        sale_files = ["5-sales.csv"]
        if (d / "5-sales-dallas.csv").exists():
            sale_files.append("5-sales-dallas.csv")
        sales_rows = [r for f in sale_files for r in read_csv(d / f)]
        upcoming_rows = read_csv(d / "6-upcoming.csv")
        log.rec["inputs"] = [str((d / f).relative_to(d.parents[1]))
                              for f in (["master.csv"] + sale_files + ["6-upcoming.csv"])]
        master_by_id = {r["apt_id"]: r for r in master_rows}

        sold_leads, sold_facts = build_sold_leads(sales_rows, master_by_id, log)
        upcoming_leads, upcoming_facts = build_upcoming_leads(upcoming_rows, log)

        all_leads = sold_leads + upcoming_leads
        all_leads.sort(key=lambda r: r["score"], reverse=True)
        for i, lead in enumerate(all_leads, start=1):
            lead["rank"] = i

        f = d / "leads.csv"
        with open(f, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            w.writeheader()
            for lead in all_leads:
                w.writerow({c: lead.get(c, "") for c in COLS})

        facts_f = d / "leads-facts.jsonl"
        with open(facts_f, "w") as fh:
            for fact in sold_facts + upcoming_facts:
                fh.write(json.dumps(fact) + "\n")

        log.rec["outputs"] = [str(f.relative_to(f.parents[2])), str(facts_f.relative_to(facts_f.parents[2]))]
        log.rec["counts"] = {
            "sold_leads": len(sold_leads), "upcoming_leads": len(upcoming_leads),
            "total_leads": len(all_leads),
        }
        print(log.rec["counts"])


if __name__ == "__main__":
    main()
