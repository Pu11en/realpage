"""Classify apartment communities' PMS vendor from their website via Jina Reader.
Key is read from ./.env at runtime (never printed). Usage: python3 tooling/probe/jina_classify.py"""
import csv, re, json, time, concurrent.futures as cf, httpx, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
KEY = [l.split("=",1)[1].strip() for l in open(ROOT/".env") if l.startswith("JINA_API_KEY=")][0]
VENDORS = [("RealPage", r"loftliving|realpage\.com|activebuilding|onesite|g5\w*\.com/residents|rpweb"),
           ("Yardi", r"securecafe|rentcafe|yardi"),
           ("Entrata", r"entrata|residentportal\.com|prospectportal"),
           ("AppFolio", r"appfolio"), ("Buildium", r"managebuilding"),
           ("ResMan", r"myresman|resman"), ("MRI/RentManager", r"mrisoftware|rentmanager|rentegi|residentcheckout")]
PORTAL = re.compile(r"resident|login|portal|pay|userlogin|onlineleasing|apply", re.I)
URL = re.compile(r"https?://[^\s)\"'<>]+")
def classify(text):
    urls = URL.findall(text)
    for strong in (True, False):  # portal/login links first, then any vendor host (e.g. image CDN)
        hits = {}
        for u in urls:
            if strong and not PORTAL.search(u): continue
            for v, pat in VENDORS:
                if re.search(pat, u, re.I): hits.setdefault(v, u)
        if hits: return hits, ("portal" if strong else "asset")
    return {}, ""
def fetch(row):
    t = time.time()
    try:
        r = httpx.get("https://r.jina.ai/" + row["url"], timeout=60,
                      headers={"Authorization": f"Bearer {KEY}", "X-With-Links-Summary": "true", "X-Retain-Images": "none"})
        hits, kind = classify(r.text)
        return {**row, "status": r.status_code, "vendor": "+".join(hits) or "unknown", "signal": kind,
                "evidence": next(iter(hits.values()), ""), "secs": round(time.time()-t,1)}
    except Exception as e:
        return {**row, "status": "err", "vendor": "unknown", "signal": "", "evidence": str(e)[:80], "secs": round(time.time()-t,1)}
rows = list(csv.DictReader(open(ROOT/"raw/research-01/R2-communities.csv")))
with cf.ThreadPoolExecutor(5) as ex: out = list(ex.map(fetch, rows))
f = ROOT/"raw/research-01/R2-jina-results.csv"
w = csv.DictWriter(open(f,"w",newline=""), fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
from collections import Counter
print(Counter(o["vendor"] for o in out)); print(Counter(o["signal"] for o in out)); print("status", Counter(str(o["status"]) for o in out))
print("identified", sum(o["vendor"]!="unknown" for o in out), "/", len(out))
