"""Scout: score ~25 Sun Belt metros (no DFW) for untapped apartment-software demand.

S1 skeleton (scoring, cap, cards) + S2 Census numbers (census.py) + S3 vendor sample (sample.py)
+ S4 churn news and portal complaints (churn_pain.py).
Data gathering (Census S2, vendor sample S3, churn + pain S4) plugs in as `gather()`.

Usage: python3 propertystack/skills/scout-areas/run.py --metros tucson-az,boise-id --limit-searches 120
"""
import argparse, csv, datetime, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REACH = ROOT / "site" / "data" / "reach.json"
MAX_SEARCHES = 1500  # hard cap per run (Jina search only)


def load_metros(path=HERE / "metros.csv"):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


class CapReached(Exception):
    pass


class SearchBudget:
    """Counts searches; raises CapReached instead of going over the cap."""
    def __init__(self, cap=MAX_SEARCHES):
        self.cap, self.used = min(cap, MAX_SEARCHES), 0

    def use(self, n=1):
        if self.used + n > self.cap:
            raise CapReached(f"search cap {self.cap} reached")
        self.used += n


def _frac(x, full):
    return min(max(x / full, 0.0), 1.0) if full else 0.0


def score_metro(d):
    """Three 0-100 part-scores + total from one metro's gathered numbers."""
    renters = d.get("renter_households") or 0
    permits = d.get("permits_5plus_12mo") or 0
    sample = d.get("sample") or {}
    n = sample.get("total") or 0
    rp_share = _frac(sample.get("RealPage", 0), n)
    rival_share = _frac(sample.get("Yardi", 0) + sample.get("Entrata", 0), n)
    growth = 0.0
    if renters or permits or n:
        per_1k = permits / (renters / 1000) if renters else 0
        growth = 40 * _frac(per_1k, 20) + 20 * _frac(renters, 300_000) + (40 * (1 - rp_share) if n else 0)
    churn = 100 * _frac(d.get("churn_items") or 0, 20)
    pain = 60 * rival_share + 40 * _frac(d.get("complaints") or 0, 10)
    parts = {"growth": round(growth), "churn": round(churn), "pain": round(pain)}
    parts["total"] = round(sum(parts.values()) / 3)
    return parts


def run_metros(metros, budget, gather):
    """gather(metro, budget) -> numbers dict. Stops cleanly when the search cap is hit."""
    areas, unfinished, stopped = [], [], False
    for i, m in enumerate(metros):
        try:
            d = gather(m, budget)
        except CapReached:
            stopped, unfinished = True, [x["slug"] for x in metros[i:]]
            break
        areas.append({**m, **score_metro(d), "inputs": d, "evidence": d.get("evidence", [])})
    areas.sort(key=lambda a: -a["total"])
    return {"areas": areas, "unfinished": unfinished, "stopped_by_cap": stopped, "searches": budget.used}


def render_cards(areas, top=5, why=None):
    why = why or {}
    out = ["# Scout: untapped Sun Belt areas", ""]
    for a in areas[:top]:
        out += [f"## {a['name']}, {a['state']} — total {a['total']}",
                f"- Growth + weakness: {a['growth']}",
                f"- Churn: {a['churn']}",
                f"- Competitor pain: {a['pain']}",
                f"- Why this city: {why.get(a['slug']) or a.get('why') or '(written in S5 from the evidence)'}"]
        ev = a.get("evidence") or []
        out += [f"- Source: {u}" for u in ev] or ["- No evidence links yet"]
        out.append("")
    return "\n".join(out)


def write_areas(res, dest):
    """areas.json: numbers + evidence links only (the "why" prose lives in why.json, written by Claude)."""
    dest = pathlib.Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    keep = ("slug", "name", "state", "cbsa", "lat", "lon", "growth", "churn", "pain", "total")
    doc = {"date": dest.name, "searches": res["searches"], "stopped_by_cap": res["stopped_by_cap"],
           "unfinished": res["unfinished"],
           "areas": [{**{k: a[k] for k in keep if k in a},
                      "inputs": {k: v for k, v in a["inputs"].items() if k != "evidence"},
                      "evidence": [u for u in dict.fromkeys(a.get("evidence") or []) if str(u).startswith("http")]}
                     for a in res["areas"]]}
    path = dest / "areas.json"
    path.write_text(json.dumps(doc, indent=1))
    return path


def write_cards(areas, dest, top=5):
    """cards.md from the areas + dest/why.json ({slug: 3-line argument}) if Claude has written it."""
    dest = pathlib.Path(dest)
    wf = dest / "why.json"
    why = json.loads(wf.read_text()) if wf.exists() else {}
    why = {k: v.replace("\n", "\n  ") for k, v in why.items()}
    path = dest / "cards.md"
    path.write_text(render_cards(areas, top, why))
    return path


def update_reach(path, areas, top=5):
    """Replace every kind:"scout" marker in the map data with the current top areas; keep all others."""
    path = pathlib.Path(path)
    old = json.loads(path.read_text()) if path.exists() else []
    marks = [{"city": a["name"], "state": a["state"], "lat": float(a["lat"]), "lon": float(a["lon"]),
              "signs": 0, "kind": "scout", "source": "scout",
              "note": f"Scout score: total {a['total']} (growth {a['growth']}, churn {a['churn']}, pain {a['pain']})",
              "links": [{"title": u.split("/")[2], "url": u} for u in [u for u in dict.fromkeys(a.get("evidence") or []) if "census.gov" not in u][:5]]}
             for a in areas[:top]]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([x for x in old if x.get("kind") != "scout"] + marks, indent=1) + "\n")
    return path


def gather_saved(metro, budget, day_dir):
    """Rebuild one metro from saved sample.csv + evidence.json (zero searches; Census is free)."""
    if not _CENSUS:
        import census
        _CENSUS.update(census.census_numbers(load_metros()))
    import sample
    d = dict(_CENSUS[metro["slug"]])
    base = pathlib.Path(day_dir) / metro["slug"]
    rows = list(csv.DictReader(open(base / "sample.csv", newline=""))) if (base / "sample.csv").exists() else []
    ev = json.loads((base / "evidence.json").read_text()) if (base / "evidence.json").exists() else {}
    churn, pain = ev.get("churn", []), ev.get("complaints", [])
    d["sample"] = sample.summarize(rows)
    d["churn_items"], d["complaints"] = len(churn), len(pain)
    proof = [r["evidence"] for r in rows if r.get("vendor") in ("RealPage", "Yardi", "Entrata") and r.get("evidence")]
    d["evidence"] = d.get("evidence", []) + proof[:5] + [x["url"] for x in churn[:3] + pain[:3]]
    return d


_CENSUS = {}
_TOOLS = {}


def gather(metro, budget):
    """Census numbers (S2, no searches) + vendor sample (S3) + churn/complaints (S4); searches counted."""
    if not _CENSUS:
        import census
        _CENSUS.update(census.census_numbers(load_metros()))
    d = dict(_CENSUS[metro["slug"]])
    import sample, churn_pain
    if not _TOOLS:
        _TOOLS.update(search=sample.jina_search(), reader=sample.Crawl4aiReader(),
                      reddit=churn_pain.reddit_search())
    d["sample"], proof, path = sample.sample_metro(metro, budget, _TOOLS["search"], _TOOLS["reader"])
    d["sample_csv"] = str(path)
    d["churn_items"], d["complaints"], links, ev_path = churn_pain.churn_pain_metro(
        metro, budget, _TOOLS["search"], _TOOLS["reddit"], sample.out_dir(), _TOOLS["reader"])
    d["evidence_json"] = str(ev_path)
    d["evidence"] = d.get("evidence", []) + proof[:5] + links
    return d


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--metros", help="comma-separated slugs (default: all)")
    ap.add_argument("--limit-searches", type=int, default=MAX_SEARCHES)
    ap.add_argument("--from-saved", metavar="DATE", help="rescore saved sample/evidence of that day, no searches")
    ap.add_argument("--reach", default=str(REACH), help="map data file to refresh scout markers in")
    a = ap.parse_args(argv)
    metros = load_metros()
    if a.metros:
        want = a.metros.split(",")
        unknown = set(want) - {m["slug"] for m in metros}
        if unknown:
            sys.exit(f"unknown metros: {', '.join(sorted(unknown))}")
        metros = [m for m in metros if m["slug"] in want]
    print(f"scout: {len(metros)} metros, cap {min(a.limit_searches, MAX_SEARCHES)} searches")
    import sample
    day = sample.out_dir(a.from_saved)
    g = (lambda m, b: gather_saved(m, b, day)) if a.from_saved else gather
    sys.path.insert(0, str(ROOT / "propertystack"))
    from lib.runlog import RunLog
    with RunLog("scout-areas", ",".join(m["slug"] for m in metros)) as log:
        res = run_metros(metros, SearchBudget(a.limit_searches), g)
        outs = [write_areas(res, day), write_cards(res["areas"], day), update_reach(a.reach, res["areas"])]
        log.rec["inputs"] = [str(p) for p in sorted(day.glob("*/*.*"))]
        log.rec["outputs"] = [str(p) for p in outs]
        log.rec["counts"] = {"metros": len(res["areas"]), "unfinished": len(res["unfinished"])}
        log.rec["api_calls"] = {"jina_search": res["searches"]}
        if res["stopped_by_cap"]:
            log.rec["notes"].append(f"stopped at search cap; unfinished: {', '.join(res['unfinished'])}")
    for x in res["areas"]:
        d = x["inputs"]
        print(f"  {x['slug']}: permits5+ {d.get('permits_5plus_12mo')}, renters {d.get('renter_households')}"
              f", sample {d.get('sample')}, churn {d.get('churn_items')}, complaints {d.get('complaints')} -> growth {x['growth']} churn {x['churn']} pain {x['pain']} total {x['total']}")
    print(f"searches used: {res['searches']}" + (" (stopped at cap)" if res["stopped_by_cap"] else ""))
    print("wrote: " + ", ".join(str(p) for p in outs))


if __name__ == "__main__":
    main()
