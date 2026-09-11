"""Skill 4 — build-table: left-join apartments + websites + software into one master table.

Usage: python3 skills/build-table/run.py --area plano-richardson
"""
import argparse, collections, csv, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from lib.paths import area_dir
from lib.runlog import RunLog

APT_COLS = ["apt_id", "name", "address", "city", "zip", "units", "year_built", "owner",
            "parcels", "cad_prop_ids", "cad_use_code"]
OUT_COLS = APT_COLS + ["county", "website", "website_confidence", "software", "signal",
                        "proof_url", "checked_at", "unknown_reason"]


def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8-sig")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", required=True)
    a = ap.parse_args()
    with RunLog("build-table", a.area) as log:
        d = area_dir(a.area)
        # Collin County source files (default county label: Collin)
        sources = [("1-apartments.csv", "2-websites.csv", "3-software.csv", "Collin")]
        # Optional second-county source files, added rather than duplicating this script.
        if (d / "1-buildings-dallas.csv").exists():
            sources.append(("1-buildings-dallas.csv", "2-websites-dallas.csv",
                             "3-software-dallas.csv", None))

        inputs_used = []
        out = []
        for apt_f, site_f, sw_f, default_county in sources:
            f1, f2, f3 = d / apt_f, d / site_f, d / sw_f
            if not f1.exists():
                continue
            apts, sites, sw = read_csv(f1), read_csv(f2), read_csv(f3)
            inputs_used += [f1, f2, f3]

            sites_by_id = {r["apt_id"]: r for r in sites}
            sw_by_id = {r["apt_id"]: r for r in sw}

            for apt in apts:
                aid = apt["apt_id"]
                site = sites_by_id.get(aid, {})
                s = sw_by_id.get(aid, {})
                row = {c: apt.get(c, "") for c in APT_COLS}
                row["county"] = apt.get("county") or default_county or ""
                row["website"] = site.get("website", "")
                row["website_confidence"] = site.get("confidence", "")
                row["software"] = s.get("software", "unknown")
                row["signal"] = s.get("signal", "none")
                row["proof_url"] = s.get("proof_url", "")
                row["checked_at"] = s.get("checked_at", "")
                row["unknown_reason"] = s.get("unknown_reason", "no-website" if not site else "")
                out.append(row)
        log.rec["inputs"] = [str(p.relative_to(p.parents[2])) for p in inputs_used]

        out_f = d / "master.csv"
        with open(out_f, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=OUT_COLS)
            w.writeheader()
            w.writerows(out)
        log.rec["outputs"] = [str(out_f.relative_to(out_f.parents[2]))]

        in_area = len(out)
        website_found = sum(1 for r in out if r["website_confidence"] in ("high", "medium"))
        checked = sum(1 for r in out if r["checked_at"])
        identified = sum(1 for r in out if r["software"] not in ("unknown", ""))
        unknown_rows = [r for r in out if r["software"] in ("unknown", "")]
        unknown_reasons = collections.Counter(r["unknown_reason"] or "(blank)" for r in unknown_rows)
        software_counts = collections.Counter(r["software"] for r in out if r["software"] not in ("unknown", ""))

        log.rec["counts"] = {
            "in_area": in_area,
            "website_found": website_found,
            "checked": checked,
            "identified": identified,
            "unknown": len(unknown_rows),
            "unknown_by_reason": dict(unknown_reasons.most_common()),
            "software": dict(software_counts.most_common()),
        }
        print(log.rec["counts"])


if __name__ == "__main__":
    main()
