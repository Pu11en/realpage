#!/usr/bin/env python3
"""Free local web search via SearXNG (tooling/searxng). Local research sessions only.

    python3 tooling/searx_search.py "query" [--n 10] [--json]

Results are cached in tooling/searxng/cache.sqlite and calls are spaced >= 2 s apart so
upstream engines don't CAPTCHA us. If SearXNG is down, start it with:
    docker compose -f tooling/searxng/docker-compose.yml up -d
Fall back to Jina only when this returns nothing.
"""
import argparse, json, os, sqlite3, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get("SEARXNG_URL", "http://127.0.0.1:8888")
CACHE = os.path.join(HERE, "searxng", "cache.sqlite")
GAP_S = 2.0


def search(query: str, n: int = 10) -> list[dict]:
    con = sqlite3.connect(CACHE)
    con.execute("CREATE TABLE IF NOT EXISTS c (q TEXT PRIMARY KEY, at REAL, body TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS last (id INTEGER PRIMARY KEY, at REAL)")
    row = con.execute("SELECT body FROM c WHERE q=?", (query,)).fetchone()
    if row:
        return json.loads(row[0])[:n]
    last = con.execute("SELECT at FROM last WHERE id=1").fetchone()
    if last and time.time() - last[0] < GAP_S:
        time.sleep(GAP_S - (time.time() - last[0]))
    url = f"{BASE}/search?" + urllib.parse.urlencode({"q": query, "format": "json"})
    with urllib.request.urlopen(url, timeout=20) as r:
        data = json.load(r)
    con.execute("INSERT OR REPLACE INTO last VALUES (1, ?)", (time.time(),))
    results = [{"title": x.get("title", ""), "url": x.get("url", ""), "snippet": (x.get("content") or "")[:300]}
               for x in data.get("results", [])]
    if results:
        con.execute("INSERT OR REPLACE INTO c VALUES (?, ?, ?)", (query, time.time(), json.dumps(results)))
    con.commit()
    return results[:n]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        res = search(a.query, a.n)
    except OSError as e:
        sys.exit(f"SearXNG not reachable at {BASE} ({e}). Start it: docker compose -f tooling/searxng/docker-compose.yml up -d")
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for r in res:
            print(f"- {r['title']}\n  {r['url']}\n  {r['snippet'][:160]}")
