"""Skill 3 — detect-software: which property-management software each community runs.

Ports the vendor-detection logic from tooling/pms_detect.py: Jina Reader fetches the
homepage -> look for vendor hosts in resident/login/pay/apply links (a "portal" match)
-> if none, follow up to 3 such links one hop and check again ("hop-portal") -> else
fall back to vendor hosts anywhere on the page ("asset") -> else check known in-house
portals (UDR, Camden) as a last resort -> else unknown.
Only fetches rows from 2-websites.csv with confidence high/medium; low/none are left
unknown with reason "no-website" and never fetched.
Usage: python3 skills/detect-software/run.py --area plano-richardson
"""
import argparse, collections, csv, datetime as dt, re, sys, pathlib
import concurrent.futures as cf
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from lib.paths import area_dir
from lib.runlog import RunLog
from lib.jina import Jina

COLS = ["apt_id", "software", "signal", "proof_url", "checked_at", "unknown_reason"]

# Vendor fingerprints: host/path patterns seen in resident-portal, pay-rent and apply links.
VENDORS = [
    ("RealPage", r"loftliving|activebuilding|realpage\.com|onesite"),
    ("Yardi", r"securecafe|rentcafe|yardi"),
    ("Entrata", r"entrata|residentportal\.com|prospectportal"),
    ("AppFolio", r"appfolio"),
    ("Buildium", r"managebuilding"),
    ("ResMan", r"myresman|resman"),
    ("Yotta", r"yottareal"),
    ("MRI/RentManager", r"mrisoftware|rentmanager"),
]
PORTAL = re.compile(r"resident|login|portal|pay|userlogin|onlineleasing|apply", re.I)
HOP = re.compile(r"resident|login|pay-?rent|portal", re.I)
SKIP = re.compile(r"facebook|onetrust|cookie|google|\.(png|jpe?g|svg|css|js|pdf)(\?|$)", re.I)
URL = re.compile(r"https?://[^\s)\"'<>]+")

# Known in-house portals, checked only after no known vendor is found on the page.
UDR = re.compile(r"residents\.udr\.com", re.I)
CAMDEN = re.compile(r"mycamden\.com", re.I)
FUNNEL = re.compile(r"funnelleasing\.com", re.I)


def classify(text):
    urls = URL.findall(text)
    for strong in (True, False):  # portal-type links first, then any vendor host
        hits = {}
        for u in urls:
            if strong and not PORTAL.search(u):
                continue
            for vendor, pat in VENDORS:
                if re.search(pat, u, re.I):
                    hits.setdefault(vendor, u)
        if hits:
            return hits, "portal" if strong else "asset"
    return {}, ""


def in_house(text):
    urls = URL.findall(text)
    for u in urls:
        if UDR.search(u):
            return "in-house:UDR", u
    for u in urls:
        if CAMDEN.search(u):
            return "in-house:Camden", u
    return None, None


def is_funnel(text):
    for u in URL.findall(text):
        if FUNNEL.search(u):
            return u
    return None


def detect(row, jina, today):
    if row["confidence"] not in ("high", "medium"):
        return {"apt_id": row["apt_id"], "software": "unknown", "signal": "none",
                "proof_url": "", "checked_at": "", "unknown_reason": "no-website"}
    url = row["website"]
    try:
        page = jina.read(url)
    except Exception as e:
        return {"apt_id": row["apt_id"], "software": "unknown", "signal": "none",
                "proof_url": "", "checked_at": today, "unknown_reason": f"error: {e}"[:100]}

    hits, kind = classify(page)
    if kind == "portal":
        return {"apt_id": row["apt_id"], "software": next(iter(hits)), "signal": "portal",
                "proof_url": next(iter(hits.values())), "checked_at": today, "unknown_reason": ""}

    hop_links = [u for u in dict.fromkeys(URL.findall(page)) if HOP.search(u) and not SKIP.search(u)][:3]
    for link in hop_links:
        try:
            page2 = jina.read(link)
        except Exception:
            continue
        h2, _ = classify(page2)
        if h2:
            return {"apt_id": row["apt_id"], "software": next(iter(h2)), "signal": "hop-portal",
                    "proof_url": next(iter(h2.values())), "checked_at": today, "unknown_reason": ""}

    if kind == "asset" and hits:
        return {"apt_id": row["apt_id"], "software": next(iter(hits)), "signal": "asset",
                "proof_url": next(iter(hits.values())), "checked_at": today, "unknown_reason": ""}

    name, link = in_house(page)
    if name:
        return {"apt_id": row["apt_id"], "software": name, "signal": "portal",
                "proof_url": link, "checked_at": today, "unknown_reason": ""}

    funnel_url = is_funnel(page)
    if funnel_url:
        return {"apt_id": row["apt_id"], "software": "unknown", "signal": "none",
                "proof_url": funnel_url, "checked_at": today, "unknown_reason": "in-house-portal"}

    return {"apt_id": row["apt_id"], "software": "unknown", "signal": "none",
            "proof_url": "", "checked_at": today, "unknown_reason": "no-portal-link"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", required=True)
    ap.add_argument("--workers", type=int, default=5)
    a = ap.parse_args()
    with RunLog("detect-software", a.area) as log:
        in_f = area_dir(a.area) / "2-websites.csv"
        rows = list(csv.DictReader(open(in_f, encoding="utf-8-sig")))
        log.rec["inputs"] = [str(in_f.relative_to(in_f.parents[2]))]
        jina = Jina()
        today = dt.date.today().isoformat()
        with cf.ThreadPoolExecutor(a.workers) as ex:
            out = list(ex.map(lambda r: detect(r, jina, today), rows))
        out_f = area_dir(a.area) / "3-software.csv"
        with open(out_f, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            w.writeheader()
            w.writerows(out)
        log.rec["outputs"] = [str(out_f.relative_to(out_f.parents[2]))]
        sw_counts = collections.Counter(r["software"] for r in out)
        reason_counts = collections.Counter(r["unknown_reason"] for r in out if r["software"] == "unknown")
        log.rec["counts"] = {"total": len(out), "software": dict(sw_counts.most_common()),
                             "unknown_reasons": dict(reason_counts.most_common())}
        log.rec["api_calls"] = dict(jina.calls)
        print(log.rec["counts"], log.rec["api_calls"])


if __name__ == "__main__":
    main()
