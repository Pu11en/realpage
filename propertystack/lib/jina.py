"""Tiny Jina client (Reader + Search). Key from env JINA_API_KEY or the nearest .env; never printed."""
import os, pathlib, time, httpx

def _key():
    if os.environ.get("JINA_API_KEY"):
        return os.environ["JINA_API_KEY"]
    for d in [pathlib.Path.cwd(), *pathlib.Path(__file__).resolve().parents]:
        env = d / ".env"
        if env.exists():
            for line in open(env):
                if line.startswith("JINA_API_KEY="):
                    return line.split("=", 1)[1].strip()
    raise SystemExit("JINA_API_KEY not found (env var or .env)")

class Jina:
    def __init__(self):
        self.h = {"Authorization": f"Bearer {_key()}"}
        self.calls = {"read": 0, "search": 0}

    def read(self, url: str, timeout=60) -> str:
        """Page as markdown with a links summary at the end."""
        self.calls["read"] += 1
        r = httpx.get("https://r.jina.ai/" + url, timeout=timeout,
                      headers={**self.h, "X-With-Links-Summary": "true", "X-Retain-Images": "none"})
        return r.text

    def search(self, query: str, timeout=60) -> list[dict]:
        """Top web results: [{title, url, description}]."""
        self.calls["search"] += 1
        for attempt in range(3):
            r = httpx.get("https://s.jina.ai/", params={"q": query}, timeout=timeout,
                          headers={**self.h, "Accept": "application/json", "X-Respond-With": "no-content"})
            if r.status_code == 200:
                return [{"title": x.get("title", ""), "url": x.get("url", ""), "description": x.get("description", "")}
                        for x in r.json().get("data", [])]
            time.sleep(2 * (attempt + 1))
        return []
