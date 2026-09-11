"""Skill 1 (Dallas County mode) — find-apartments for the Dallas County part of Richardson.

Source: DCAD ("Dallas CAD") free bulk data download (no API — DCAD has no Socrata
resource, unlike Collin CAD). Data Products page: https://www.dallascad.org/dataproducts.aspx
ZIP used: DCAD2026_CURRENT.ZIP ("2026 Certified Data Files with Supplemental Changes").

DCAD's PTAD state property class B splits into two DCAD SPTD codes (see
data/raw/dcad/extracted/SPTD_CD_XREF.pdf, extracted from the ZIP):
  B11 = MFR - APARTMENTS   <- what we want
  B12 = MFR - DUPLEXES     <- excluded (not apartment communities)
Confirmed live from DCAD2026_CURRENT.ZIP, fetched 2026-09-10.

Unlike Collin CAD's single Socrata resource (one row per parcel with situscity/
imprvunits/propcategorycode fields inline), DCAD splits data across CSVs joined by
ACCOUNT_NUM:
  ACCOUNT_APPRL_YEAR.CSV  -> SPTD_CODE (property class), CITY_JURIS_DESC
  ACCOUNT_INFO.CSV        -> PROPERTY_CITY, street address, zip, owner name
  COM_DETAIL.CSV          -> NUM_UNITS, YEAR_BUILT, PROPERTY_NAME (one row per
                              building/component on the account; parking garages
                              and retail components have NUM_UNITS=0)

Usage:
  python3 skills/find-apartments/run_dallas.py --area plano-richardson \
      --city RICHARDSON --zip-path data/raw/dcad/DCAD2026_CURRENT.ZIP

The ZIP (~186MB) and its extracted CSVs are NOT committed to git — see
data/raw/.gitignore. Re-download from the URL above if the raw folder is missing:
  curl -sL -o data/raw/dcad/DCAD2026_CURRENT.ZIP \
    "https://www.dallascad.org/ViewPDFs.aspx?type=3&id=%5C%5CDCAD.ORG%5CWEB%5CWEBDATA%5CWEBFORMS%5CDATA%20PRODUCTS%5CDCAD2026_CURRENT.ZIP"
"""
import argparse, collections, csv, re, sys, pathlib, zipfile, io
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from lib.paths import area_dir
from lib.runlog import RunLog

COLS = ["apt_id", "name", "address", "city", "county", "zip", "units", "year_built",
        "owner", "parcels", "cad_prop_ids", "cad_use_code"]
STOP = r"\b(apartments?|apts?|apartment homes|phase|ph|i{1,3}|iv|v|building|bldg|[a-f])\b"


def norm(s):
    s = re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())
    return re.sub(r"\s+", " ", re.sub(STOP, " ", s)).strip()


def norm_addr(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def read_csv_from_zip(zf, name):
    with zf.open(name) as fh:
        text = io.TextIOWrapper(fh, encoding="utf-8", errors="replace")
        yield from csv.DictReader(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", required=True)
    ap.add_argument("--city", default="RICHARDSON", help="PROPERTY_CITY value to filter on (DCAD situs city)")
    ap.add_argument("--min-units", type=int, default=20)
    ap.add_argument("--zip-path", required=True, help="path to the downloaded DCAD*_CURRENT.ZIP")
    a = ap.parse_args()
    zip_path = pathlib.Path(a.zip_path)
    if not zip_path.exists():
        print(f"ERROR: {zip_path} not found. Download the DCAD bulk ZIP first "
              f"(see run_dallas.py docstring for the URL).", file=sys.stderr)
        sys.exit(1)

    with RunLog("find-apartments-dallas", a.area) as log:
        log.rec["inputs"] = [str(zip_path)]
        with zipfile.ZipFile(zip_path) as zf:
            b11_accounts = set()
            for row in read_csv_from_zip(zf, "ACCOUNT_APPRL_YEAR.CSV"):
                if row["SPTD_CODE"] == "B11":
                    b11_accounts.add(row["ACCOUNT_NUM"])

            info = {}
            for row in read_csv_from_zip(zf, "ACCOUNT_INFO.CSV"):
                acc = row["ACCOUNT_NUM"]
                if acc in b11_accounts and row["PROPERTY_CITY"].strip().upper() == a.city.upper():
                    info[acc] = row

            com = collections.defaultdict(list)
            for row in read_csv_from_zip(zf, "COM_DETAIL.CSV"):
                if row["ACCOUNT_NUM"] in info:
                    com[row["ACCOUNT_NUM"]].append(row)

        # Build one row per account: sum NUM_UNITS across components with units > 0,
        # take earliest YEAR_BUILT among those, name = the component with the most units.
        accounts_out = []
        for acc, acct_info in info.items():
            rows = [r for r in com.get(acc, []) if int(r["NUM_UNITS"] or 0) > 0]
            if not rows:
                continue
            units = sum(int(r["NUM_UNITS"]) for r in rows)
            if units < a.min_units:
                continue
            name_row = max(rows, key=lambda r: int(r["NUM_UNITS"]))
            year_built = min((r["YEAR_BUILT"] for r in rows if r["YEAR_BUILT"] not in ("0", "")), default="")
            street = " ".join(p for p in [
                acct_info.get("STREET_NUM", "").strip(),
                acct_info.get("STREET_HALF_NUM", "").strip(),
                acct_info.get("FULL_STREET_NAME", "").strip(),
            ] if p)
            accounts_out.append({
                "acc": acc,
                "name": name_row["PROPERTY_NAME"].strip().title(),
                "address": street.title(),
                "city": acct_info["PROPERTY_CITY"].strip().title(),
                "zip": (acct_info.get("PROPERTY_ZIPCODE") or "").strip()[:5],
                "units": units,
                "year_built": year_built,
                "owner": (acct_info.get("OWNER_NAME1") or "").strip(),
            })

        # Merge accounts of the same community by normalized name + exact street address
        # (same rule as the Collin-County fallback merge in run.py), since DCAD sometimes
        # splits one community across multiple ACCOUNT_NUMs (e.g. garage/retail parcels
        # already excluded by units>0, but phased apartment builds can still share a name).
        groups = collections.OrderedDict()
        for r in sorted(accounts_out, key=lambda r: r["acc"]):
            key = (norm(r["name"]) or r["address"].lower(), r["city"].upper())
            groups.setdefault(key, []).append(r)
        by_addr = collections.OrderedDict()
        for key, g in groups.items():
            addr_key = (norm_addr(g[0]["address"]), key[1])
            by_addr.setdefault(addr_key, []).append(key)
        merged = collections.OrderedDict()
        for addr_key, keys in by_addr.items():
            if len(keys) == 1:
                merged[keys[0]] = groups[keys[0]]
                continue
            combined_key = min(keys, key=lambda k: min(x["acc"] for x in groups[k]))
            combined = []
            for k in keys:
                combined.extend(groups[k])
            merged[combined_key] = combined

        out = []
        for _, g in merged.items():
            first = min(g, key=lambda r: r["acc"])
            out.append({
                "apt_id": first["acc"],
                "name": first["name"],
                "address": first["address"],
                "city": first["city"],
                "county": "Dallas",
                "zip": first["zip"],
                "units": sum(x["units"] for x in g),
                "year_built": min((x["year_built"] for x in g if x["year_built"]), default=""),
                "owner": first["owner"],
                "parcels": len(g),
                "cad_prop_ids": ";".join(x["acc"] for x in g),
                "cad_use_code": "B11",
            })
        out.sort(key=lambda r: (r["city"], -r["units"]))

        f = area_dir(a.area) / "1-buildings-dallas.csv"
        with open(f, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            w.writeheader()
            w.writerows(out)
        log.rec["outputs"] = [str(f.relative_to(f.parents[2]))]
        log.rec["counts"] = {"b11_accounts_total_county": len(b11_accounts),
                              "accounts_in_city": len(info),
                              "communities": len(out),
                              "units": sum(r["units"] for r in out)}
        print(log.rec["counts"])


if __name__ == "__main__":
    main()
