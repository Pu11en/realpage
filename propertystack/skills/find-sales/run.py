"""Skill 5 — find-sales: apartment communities that changed hands in the last 24 months,
from Collin CAD deed records + owner-name changes across appraisal rolls.

Source: Collin CAD on data.texas.gov (Socrata), free, no key.
  2026 roll: 5tkr-3759 (current owner + deed info)
  2025 roll: vffy-snc6 (prior owner, for the owner-change check)
Field names (propid, dbaname, ownername, deedtypecd, deedeffdate) are identical across
2024/2025/2026 rolls (confirmed via GET https://data.texas.gov/api/views/<id>.json).

A community counts as SOLD if any of its parcels has, in the last 24 months:
  - a real-sale ("warranty deed family": WD, SWD, WDNL, SWDNL) deed effective date, and/or
  - an owner name that differs (normalized) between the 2025 and 2026 rolls.
Excludes non-sale deed types (QCD, CORRD, AFF, TODD, PRB, WILL, DIV, PLAT, ROW, etc.) —
those alone do not trigger a sale.

Usage: python3 skills/find-sales/run.py --area plano-richardson
"""
import argparse, collections, csv, datetime as dt, re, sys, pathlib, httpx
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from lib.paths import area_dir
from lib.runlog import RunLog

API_2026 = "https://data.texas.gov/resource/5tkr-3759.json"
API_2025 = "https://data.texas.gov/resource/vffy-snc6.json"
FIELDS = "propid,dbaname,ownername,deedtypecd,deedeffdate"
COLS = ["apt_id", "name", "sale_date", "deed_type", "new_owner", "previous_owner",
        "units", "source", "source_url"]

WD_FAMILY = {"WD", "SWD", "WDNL", "SWDNL"}
TODAY = dt.date(2026, 9, 10)
WINDOW_START = TODAY - dt.timedelta(days=730)  # 24 months

STOP_OWNER_WORDS = r"\b(LLC|LP|LLP|LTD|INC|CORP|CO|L P|L L C)\b"


def norm_owner(s):
    s = re.sub(r"[^A-Z0-9 ]", " ", (s or "").upper())
    s = re.sub(STOP_OWNER_WORDS, " ", s)
    return re.sub(r"\s+", " ", s).strip()


def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def fetch_by_propid(api, propids):
    """Batch-fetch rows for a list of propids ($where=propid in (...)), chunks of 100."""
    out = {}
    calls = 0
    for group in chunk(propids, 100):
        where = f"propid in ({','.join(group)})"
        r = httpx.get(api, params={"$select": FIELDS, "$where": where, "$limit": 1000}, timeout=120)
        r.raise_for_status()
        calls += 1
        for row in r.json():
            out[row["propid"]] = row
    return out, calls


def parcel_source_url(propid):
    return (f"{API_2026}?$select={FIELDS}&$where=propid%20in%20({propid})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", required=True)
    a = ap.parse_args()
    with RunLog("find-sales", a.area) as log:
        in_f = area_dir(a.area) / "1-apartments.csv"
        communities = list(csv.DictReader(open(in_f)))
        log.rec["inputs"] = [str(in_f.relative_to(in_f.parents[2]))]

        all_propids = []
        for c in communities:
            all_propids.extend(c["cad_prop_ids"].split(";"))
        all_propids = sorted(set(all_propids))

        data_2026, calls_2026 = fetch_by_propid(API_2026, all_propids)
        data_2025, calls_2025 = fetch_by_propid(API_2025, all_propids)

        deed_types_seen = collections.Counter()
        excluded_deed_types = collections.Counter()
        sold_by_deed = 0
        owner_changed_without_deed = 0

        out_rows = []
        for c in communities:
            propids = c["cad_prop_ids"].split(";")
            triggers = []  # list of dicts: propid, deedeffdate, deedtypecd, new_owner, prev_owner, kind
            for pid in propids:
                r26 = data_2026.get(pid)
                if not r26:
                    continue
                deed_type = r26.get("deedtypecd") or ""
                owner26 = (r26.get("ownername") or "").strip()
                deedeffdate_raw = r26.get("deedeffdate") or ""
                deedeffdate = deedeffdate_raw[:10] if deedeffdate_raw else ""
                if deed_type:
                    deed_types_seen[deed_type] += 1

                r25 = data_2025.get(pid)
                owner25 = (r25.get("ownername") or "").strip() if r25 else ""

                deed_sale = False
                if deed_type in WD_FAMILY and deedeffdate:
                    try:
                        eff = dt.date.fromisoformat(deedeffdate)
                        deed_sale = eff >= WINDOW_START
                    except ValueError:
                        deed_sale = False
                elif deed_type and deed_type not in WD_FAMILY:
                    excluded_deed_types[deed_type] += 1

                owner_changed = bool(owner25) and norm_owner(owner25) != norm_owner(owner26)

                if deed_sale or owner_changed:
                    prev_owner = owner25 if (owner25 and norm_owner(owner25) != norm_owner(owner26)) \
                        else "unknown (same owner name in 2025 roll)"
                    triggers.append({
                        "propid": pid, "deedeffdate": deedeffdate, "deed_type": deed_type,
                        "new_owner": owner26, "previous_owner": prev_owner,
                        "deed_sale": deed_sale, "owner_changed": owner_changed,
                    })

            if not triggers:
                continue

            # most recent sale: prefer the trigger with the latest deedeffdate; fall back to
            # first trigger if none have parseable dates.
            def sort_key(t):
                return t["deedeffdate"] or "0000-00-00"
            best = sorted(triggers, key=sort_key, reverse=True)[0]

            if best["deed_sale"]:
                sold_by_deed += 1
            if any(t["owner_changed"] and not t["deed_sale"] for t in triggers):
                owner_changed_without_deed += 1

            out_rows.append({
                "apt_id": c["apt_id"],
                "name": c["name"],
                "sale_date": best["deedeffdate"],
                "deed_type": best["deed_type"],
                "new_owner": best["new_owner"],
                "previous_owner": best["previous_owner"],
                "units": c["units"],
                "source": "Collin CAD 2026 vs 2025",
                "source_url": parcel_source_url(best["propid"]),
            })

        out_rows.sort(key=lambda r: r["sale_date"], reverse=True)
        f = area_dir(a.area) / "5-sales.csv"
        with open(f, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            w.writeheader()
            w.writerows(out_rows)

        log.rec["outputs"] = [str(f.relative_to(f.parents[2]))]
        log.rec["counts"] = {
            "communities_checked": len(communities),
            "parcels_checked": len(all_propids),
            "sold": len(out_rows),
            "sold_by_deed": sold_by_deed,
            "owner_changed_without_deed": owner_changed_without_deed,
            "deed_types_seen": dict(deed_types_seen),
            "excluded_deed_types_seen": dict(excluded_deed_types),
        }
        log.rec["api_calls"] = {"socrata_2026": calls_2026, "socrata_2025": calls_2025}
        print(log.rec["counts"])


if __name__ == "__main__":
    main()
