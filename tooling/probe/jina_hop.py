"""Second pass: for 'unknown' rows, follow resident/login/pay links one hop and re-classify."""
import csv, re, httpx, pathlib, concurrent.futures as cf, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from jina_classify import KEY, classify, URL, ROOT  # noqa (import runs nothing heavy? guarded below)
H = {"Authorization": f"Bearer {KEY}", "X-With-Links-Summary": "true", "X-Retain-Images": "none"}
HOP = re.compile(r"resident|login|pay-?rent|portal|my\w+\.com", re.I)
def hop(row):
    if row["vendor"] != "unknown": return row
    t = httpx.get("https://r.jina.ai/" + row["url"], timeout=60, headers=H).text
    cands = [u for u in dict.fromkeys(URL.findall(t)) if HOP.search(u) and not re.search(r"facebook|onetrust|cookie|google|\.(png|jpg|svg|css|js)", u, re.I)][:3]
    for u in cands:
        try:
            r = httpx.get("https://r.jina.ai/" + u, timeout=60, headers=H)
            hits, kind = classify(r.text + " " + str(r.headers.get("x-final-url", "")))
            if hits:
                return {**row, "vendor": "+".join(hits), "signal": "hop-" + kind, "evidence": next(iter(hits.values()))}
        except Exception: pass
    return {**row, "notes_hop": " | ".join(cands)}
def main():
    rows = list(csv.DictReader(open(ROOT / "raw/research-01/R2-jina-results.csv")))
    with cf.ThreadPoolExecutor(5) as ex: out = list(ex.map(hop, rows))
    keys = list(dict.fromkeys(k for o in out for k in o))
    w = csv.DictWriter(open(ROOT / "raw/research-01/R2-hop-results.csv", "w", newline=""), fieldnames=keys); w.writeheader(); w.writerows(out)
    for o in out:
        if o["vendor"] == "unknown" or o["signal"].startswith("hop"): print(o["vendor"], o["signal"], o["url"], o.get("notes_hop", o["evidence"])[:150])
if __name__ == "__main__": main()
