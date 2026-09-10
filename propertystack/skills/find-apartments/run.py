"""Skill 1 — find-apartments: every apartment community in an area, from county appraisal records.

Source: Collin CAD 2026 on data.texas.gov (Socrata). Filter catches category-B multifamily
AND multifamily coded as commercial (use code MFU/MFUSE), 20+ units. Parcels of the same
community are merged by normalized name + city.
Usage: python3 skills/find-apartments/run.py --area plano-richardson --cities PLANO,RICHARDSON
"""
import argparse, collections, csv, re, sys, pathlib, httpx
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from lib.paths import area_dir
from lib.runlog import RunLog

API = "https://data.texas.gov/resource/5tkr-3759.json"   # Collin CAD Appraisal Data - 2026
FIELDS = "propid,dbaname,situsconcatshort,situscity,situszip,ownername,imprvunits,imprvyearbuilt,propcategorycode,propusecode"
COLS = ["apt_id", "name", "address", "city", "zip", "units", "year_built", "owner", "parcels", "cad_prop_ids", "cad_use_code"]
STOP = r"\b(apartments?|apts?|apartment homes|phase|ph|i{1,3}|iv|v|building|bldg|[a-f])\b"

def norm(s):
    s = re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())
    return re.sub(r"\s+", " ", re.sub(STOP, " ", s)).strip()

def norm_addr(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())

def fetch(cities, min_units):
    where = (f"upper(situscity) in ({','.join(repr(c) for c in cities)}) and imprvunits >= {min_units} "
             "and (propcategorycode = 'B' or propusecode in ('MFU','MFUSE'))")
    r = httpx.get(API, params={"$select": FIELDS, "$where": where, "$limit": 5000}, timeout=120)
    r.raise_for_status()
    return r.json(), where

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", required=True)
    ap.add_argument("--cities", default="PLANO,RICHARDSON")
    ap.add_argument("--min-units", type=int, default=20)
    a = ap.parse_args()
    with RunLog("find-apartments", a.area) as log:
        rows, where = fetch(a.cities.upper().split(","), a.min_units)
        log.rec["inputs"] = [f"{API} where {where}"]
        groups = collections.OrderedDict()
        for r in sorted(rows, key=lambda r: int(r["propid"])):
            key = (norm(r.get("dbaname")) or r["situsconcatshort"].lower(), r["situscity"].upper())
            g = groups.setdefault(key, [])
            g.append(r)
        # Fallback merge: different normalized names (e.g. "...Creek" vs "...Creekside",
        # "...Prairie Creek" vs "...Prairie Creek Villas Ii") sometimes name the same
        # physical site. If two name-groups share the exact same normalized street
        # address + city, treat them as one community rather than double-counting the
        # denominator. Found via review 2026-09-10 (evals/review-weak-spots.md-style
        # check) — confirmed live for the two merges below; NOT applied on name/owner
        # similarity alone, since a shared owner + deed date can also mean two distinct
        # sites sold together in one portfolio transaction (seen with a same-owner,
        # different-address, similarly-named pair that was deliberately left unmerged).
        by_addr = collections.OrderedDict()
        for key, g in groups.items():
            addr_key = (norm_addr(g[0]["situsconcatshort"]), key[1])
            by_addr.setdefault(addr_key, []).append(key)
        merged = collections.OrderedDict()
        seen_keys = set()
        for addr_key, keys in by_addr.items():
            if len(keys) == 1:
                k = keys[0]
                merged[k] = groups[k]
                continue
            combined_key = min(keys, key=lambda k: min(int(x["propid"]) for x in groups[k]))
            combined = []
            for k in keys:
                combined.extend(groups[k])
            combined.sort(key=lambda x: int(x["propid"]))
            merged[combined_key] = combined
        groups = merged
        out = []
        for (_, _), g in groups.items():
            first = g[0]
            out.append({
                "apt_id": first["propid"],
                "name": (first.get("dbaname") or first["situsconcatshort"]).strip().title(),
                "address": first["situsconcatshort"].strip().title(),
                "city": first["situscity"].strip().title(),
                "zip": (first.get("situszip") or "")[:5],
                "units": sum(int(x["imprvunits"]) for x in g),
                "year_built": min((x.get("imprvyearbuilt") or "9999") for x in g).replace("9999", ""),
                "owner": first["ownername"].strip(),
                "parcels": len(g),
                "cad_prop_ids": ";".join(x["propid"] for x in g),
                "cad_use_code": first.get("propusecode", ""),
            })
        out.sort(key=lambda r: (r["city"], -r["units"]))
        f = area_dir(a.area) / "1-apartments.csv"
        with open(f, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerows(out)
        log.rec["outputs"] = [str(f.relative_to(f.parents[2]))]
        log.rec["counts"] = {"parcels": len(rows), "communities": len(out),
                             "units": sum(r["units"] for r in out),
                             "by_city": dict(collections.Counter(r["city"] for r in out))}
        log.rec["api_calls"] = {"socrata": 1}
        print(log.rec["counts"])

if __name__ == "__main__":
    main()
