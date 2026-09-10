"""PMS detector: which property-management software does each apartment community run?

Input  CSV: needs a `url` column (community website); other columns are kept.
Output CSV: adds vendor, signal, evidence, status.
Method: Jina Reader fetches the homepage (handles JavaScript and bot walls) -> look for
vendor hosts in resident/login/pay/apply links -> if none, follow up to 3 such links one
hop and check again -> otherwise fall back to vendor hosts anywhere (e.g. asset CDNs).

Usage: python3 tooling/pms_detect.py IN.csv OUT.csv [--workers 5]
Key: JINA_API_KEY from ./.env (gitignored) or the environment. Never print it.
"""
import argparse, collections, concurrent.futures as cf, csv, os, pathlib, re, sys, httpx

ROOT = pathlib.Path(__file__).resolve().parents[1]

def load_key():
    env = ROOT / ".env"
    if env.exists():
        for line in open(env):
            if line.startswith("JINA_API_KEY="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("JINA_API_KEY") or sys.exit("JINA_API_KEY missing (.env or env var)")

# Vendor fingerprints: host/path patterns seen in resident-portal, pay-rent and apply links.
# Add new ones here with an example URL in the comment.
VENDORS = [
    ("RealPage", r"loftliving|activebuilding|realpage\.com|onesite"),   # dorianandencore.loftliving.com/login
    ("Yardi",    r"securecafe|rentcafe|yardi"),                         # axis110.securecafe.com/residentservices/...
    ("Entrata",  r"entrata|residentportal\.com|prospectportal"),        # legacynorthapts.residentportal.com/auth
    ("AppFolio", r"appfolio"),
    ("Buildium", r"managebuilding"),
    ("ResMan",   r"myresman|resman"),
    ("Yotta",    r"yottareal"),                                         # adaraportal.yottareal.com
    ("MRI/RentManager", r"mrisoftware|rentmanager"),
]
PORTAL = re.compile(r"resident|login|portal|pay|userlogin|onlineleasing|apply", re.I)
HOP = re.compile(r"resident|login|pay-?rent|portal", re.I)
SKIP = re.compile(r"facebook|onetrust|cookie|google|\.(png|jpe?g|svg|css|js|pdf)(\?|$)", re.I)
URL = re.compile(r"https?://[^\s)\"'<>]+")

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

class Reader:
    def __init__(self, key):
        self.h = {"Authorization": f"Bearer {key}", "X-With-Links-Summary": "true", "X-Retain-Images": "none"}
    def get(self, url):
        return httpx.get("https://r.jina.ai/" + url, headers=self.h, timeout=60).text

def detect(row, reader):
    try:
        page = reader.get(row["url"])
    except Exception as e:
        return {**row, "vendor": "unknown", "signal": "error", "evidence": str(e)[:100]}
    hits, kind = classify(page)
    if kind == "portal":
        return {**row, "vendor": "+".join(hits), "signal": "portal", "evidence": next(iter(hits.values()))}
    for link in [u for u in dict.fromkeys(URL.findall(page)) if HOP.search(u) and not SKIP.search(u)][:3]:
        try:
            h2, k2 = classify(reader.get(link))
        except Exception:
            continue
        if h2:
            return {**row, "vendor": "+".join(h2), "signal": "hop-" + k2, "evidence": next(iter(h2.values()))}
    if hits:
        return {**row, "vendor": "+".join(hits), "signal": "asset", "evidence": next(iter(hits.values()))}
    return {**row, "vendor": "unknown", "signal": "", "evidence": ""}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("--workers", type=int, default=5)
    a = ap.parse_args()
    rows = [r for r in csv.DictReader(open(a.inp, encoding="utf-8-sig")) if r.get("url", "").startswith("http")]
    reader = Reader(load_key())
    with cf.ThreadPoolExecutor(a.workers) as ex:
        out = list(ex.map(lambda r: detect(r, reader), rows))
    keys = list(dict.fromkeys(k for o in out for k in o))
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(out)
    c = collections.Counter(o["vendor"] for o in out)
    known = len(out) - c["unknown"]
    print(f"{known}/{len(out)} identified ({known * 100 // max(len(out), 1)}%)", dict(c.most_common()))

if __name__ == "__main__":
    main()
