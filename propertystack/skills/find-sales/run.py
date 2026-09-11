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

STOP_OWNER_WORDS = r"\b(LLC|LP|LLP|LTD|INC|CORP|CO|L P|L L C|SPE)\b"


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


# --- Dallas County (DCAD) mode ---
# DCAD's bulk data has no deed-date field anywhere (confirmed by inspecting every CSV/DAT
# in both the current-year ZIP and the historical "certified roll" ZIP — see
# DALLAS-SOURCES.md). So unlike Collin, Dallas sales can only be inferred from an
# owner-name change between the current DCAD roll (used by find-apartments/run_dallas.py,
# data/raw/dcad/DCAD2026_CURRENT.ZIP -> ACCOUNT_INFO.CSV OWNER_NAME1) and a prior-year
# certified roll (fixed-width .DAT, ~24 months back). No sale_date/deed_type evidence is
# possible this way, so those columns are always blank/"owner-change" and every row is
# weaker evidence than a Collin deed-backed row.
DALLAS_PRIOR_ROLL = "data/raw/dcad/extracted2024/REAL_APRL_ROLL_DALLAS_COUNTY_2024.DAT"
# Fixed-width columns per Add_Change_File_Format.xls (1-indexed, inclusive):
# DCAD ACCOUNT NUMBER 0010-0026 (17), OWNER NAME 0027-0056 (30).
DALLAS_ACCT_SLICE = slice(9, 26)
DALLAS_OWNER_SLICE = slice(26, 56)


def prefix_same(a, b, min_len=8):
    """True if two normalized owner names are equal, or agree over their common length
    (handles the 30-char field truncating long owner names identically in both rolls)."""
    if a == b:
        return True
    m = min(len(a), len(b))
    return m >= min_len and a[:m] == b[:m]


def load_dallas_prior_owners(propids, path=DALLAS_PRIOR_ROLL):
    """Scan the prior-year DCAD fixed-width roll once and return {account_num: [owner, ...]}
    restricted to the propids we care about."""
    ids = set(propids)
    found = collections.defaultdict(list)
    with open(path, encoding="latin-1") as fh:
        for line in fh:
            acc = line[DALLAS_ACCT_SLICE].strip()
            if acc in ids:
                found[acc].append(line[DALLAS_OWNER_SLICE].strip())
    return found


def run_dallas(a):
    """Owner-name-change-only sales inference for the Dallas County part of an area.
    Writes data/<area>/5-sales-dallas.csv with the same COLS as the Collin output."""
    with RunLog("find-sales-dallas", a.area) as log:
        in_f = area_dir(a.area) / "1-buildings-dallas.csv"
        communities = list(csv.DictReader(open(in_f)))
        log.rec["inputs"] = [str(in_f.relative_to(in_f.parents[2])), DALLAS_PRIOR_ROLL]

        all_propids = sorted({pid for c in communities for pid in c["cad_prop_ids"].split(";")})
        prior = load_dallas_prior_owners(all_propids)
        missing_from_prior_roll = [pid for pid in all_propids if pid not in prior]

        out_rows = []
        for c in communities:
            propids = c["cad_prop_ids"].split(";")
            prior_owners = {o for pid in propids for o in prior.get(pid, [])}
            if not prior_owners:
                continue  # no prior-roll evidence at all for this community -> can't compare
            cur_owner = (c.get("owner") or "").strip()
            cur_n = norm_owner(cur_owner)
            if any(prefix_same(cur_n, norm_owner(po)) for po in prior_owners):
                continue  # same owner (allowing for 30-char truncation) -> not a sale
            prev_owner = sorted(prior_owners)[0]
            out_rows.append({
                "apt_id": c["apt_id"],
                "name": c["name"],
                "sale_date": "",
                "deed_type": "owner-change (DCAD bulk data has no deed date field; "
                              "see DALLAS-SOURCES.md)",
                "new_owner": cur_owner,
                "previous_owner": prev_owner,
                "units": c["units"],
                "source": "DCAD 2026 current roll vs 2024 certified roll (owner-name diff only)",
                "source_url": "https://www.dallascad.org/dataproducts.aspx",
            })

        out_rows.sort(key=lambda r: r["name"])
        f = area_dir(a.area) / "5-sales-dallas.csv"
        with open(f, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            w.writeheader()
            w.writerows(out_rows)

        log.rec["outputs"] = [str(f.relative_to(f.parents[2]))]
        log.rec["counts"] = {
            "communities_checked": len(communities),
            "parcels_checked": len(all_propids),
            "parcels_missing_from_prior_roll": len(missing_from_prior_roll),
            "owner_changed": len(out_rows),
        }
        print(log.rec["counts"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", required=True)
    ap.add_argument("--dallas", action="store_true",
                     help="Dallas County (DCAD) mode: owner-name-change diff against a "
                          "prior-year DCAD roll, no deed-date evidence available. "
                          "Reads 1-buildings-dallas.csv, writes 5-sales-dallas.csv.")
    a = ap.parse_args()
    if a.dallas:
        run_dallas(a)
        return
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

            # Prefer a trigger backed by a real, in-window sale deed (deed_sale=True) —
            # concrete dated evidence. Only fall back to an owner-name-change-only
            # trigger if no such deed exists on any parcel. Previously this picked
            # whichever trigger had the LATEST deedeffdate across BOTH kinds, which
            # could surface an old, unrelated non-sale deed (e.g. a 2024 PLAT filing)
            # as if its date/type were sale evidence for a same-owner-name-change
            # community — misleading even though the underlying signal (owner changed
            # between the 2025 and 2026 rolls) was real and recent. See
            # evals/review-weak-spots.md.
            def sort_key(t):
                return t["deedeffdate"] or "0000-00-00"
            deed_triggers = [t for t in triggers if t["deed_sale"]]
            if deed_triggers:
                best = sorted(deed_triggers, key=sort_key, reverse=True)[0]
                sale_date, deed_type = best["deedeffdate"], best["deed_type"]
                sold_by_deed += 1
            else:
                best = sorted(triggers, key=sort_key, reverse=True)[0]
                sale_date, deed_type = "", "owner-change (no qualifying sale deed on file)"
                owner_changed_without_deed += 1

            def clean_owner(s):
                return re.sub(r"[\s&]+$", "", s or "").strip()

            out_rows.append({
                "apt_id": c["apt_id"],
                "name": c["name"],
                "sale_date": sale_date,
                "deed_type": deed_type,
                "new_owner": clean_owner(best["new_owner"]),
                "previous_owner": clean_owner(best["previous_owner"]),
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
