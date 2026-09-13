"""Scout: score ~25 Sun Belt metros (no DFW) for untapped apartment-software demand.

S1 skeleton (scoring, cap, cards) + S2 Census numbers (census.py) + S3 vendor sample (sample.py).
Data gathering (Census S2, vendor sample S3, churn + pain S4) plugs in as `gather()`.

Usage: python3 propertystack/skills/scout-areas/run.py --metros tucson-az,boise-id --limit-searches 120
"""
import argparse, csv, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
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


def render_cards(areas, top=5):
    out = ["# Scout: untapped Sun Belt areas", ""]
    for a in areas[:top]:
        out += [f"## {a['name']}, {a['state']} — total {a['total']}",
                f"- Growth + weakness: {a['growth']}",
                f"- Churn: {a['churn']}",
                f"- Competitor pain: {a['pain']}",
                f"- Why this city: {a.get('why') or '(written in S5 from the evidence)'}"]
        ev = a.get("evidence") or []
        out += [f"- Source: {u}" for u in ev] or ["- No evidence links yet"]
        out.append("")
    return "\n".join(out)


_CENSUS = {}
_TOOLS = {}


def gather(metro, budget):
    """Census numbers (S2, no searches) + vendor sample (S3, searches counted). Churn + pain in S4."""
    if not _CENSUS:
        import census
        _CENSUS.update(census.census_numbers(load_metros()))
    d = dict(_CENSUS[metro["slug"]])
    import sample
    if not _TOOLS:
        _TOOLS.update(search=sample.jina_search(), reader=sample.Crawl4aiReader())
    d["sample"], proof, path = sample.sample_metro(metro, budget, _TOOLS["search"], _TOOLS["reader"])
    d["sample_csv"] = str(path)
    d["evidence"] = d.get("evidence", []) + proof[:5]
    return d


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--metros", help="comma-separated slugs (default: all)")
    ap.add_argument("--limit-searches", type=int, default=MAX_SEARCHES)
    a = ap.parse_args(argv)
    metros = load_metros()
    if a.metros:
        want = a.metros.split(",")
        unknown = set(want) - {m["slug"] for m in metros}
        if unknown:
            sys.exit(f"unknown metros: {', '.join(sorted(unknown))}")
        metros = [m for m in metros if m["slug"] in want]
    print(f"scout: {len(metros)} metros, cap {min(a.limit_searches, MAX_SEARCHES)} searches")
    res = run_metros(metros, SearchBudget(a.limit_searches), gather)
    for x in res["areas"]:
        d = x["inputs"]
        print(f"  {x['slug']}: permits5+ {d.get('permits_5plus_12mo')}, renters {d.get('renter_households')}"
              f", sample {d.get('sample')} -> growth {x['growth']} churn {x['churn']} pain {x['pain']} total {x['total']}")
    print(f"searches used: {res['searches']}" + (" (stopped at cap)" if res["stopped_by_cap"] else ""))


if __name__ == "__main__":
    main()
