"""Public chat endpoint for the PropertyStack site.

Hermes' API server needs a bearer key, which a static site can't hide, so this
small front sits on Railway's $PORT and forwards to Hermes on localhost:

  POST /chat   {"message": "..."}  ->  {"answer": "...", "citations": [...]}
  GET  /health

One-shot: every request is a fresh, stateless Hermes call (no session id, no
memory). Guardrails on cost: message length cap, per-IP rate limit, a small
concurrency cap and a timeout.
"""
import asyncio
import os
import re
import time
from collections import defaultdict, deque

import aiohttp
from aiohttp import web

HERMES_URL = f"http://127.0.0.1:{os.environ.get('API_SERVER_PORT', '8642')}/v1/chat/completions"
HERMES_KEY = os.environ["API_SERVER_KEY"]
PORT = int(os.environ.get("PORT", "8080"))
ALLOWED_ORIGINS = {o.strip() for o in os.environ.get(
    "CHAT_ALLOWED_ORIGINS", "https://propertystack-production.up.railway.app"
).split(",") if o.strip()}
MAX_CHARS = 1000
RATE_PER_HOUR = int(os.environ.get("CHAT_RATE_PER_HOUR", "30"))
TIMEOUT_S = 120

_hits: dict[str, deque] = defaultdict(deque)
_slots = asyncio.Semaphore(int(os.environ.get("CHAT_MAX_CONCURRENT", "3")))
BRACKET_RE = re.compile(r"\[([^\[\]]+)\]")
FILE_RE = re.compile(r"^[\w./-]+\.(?:csv|md|jsonl)$")
URL_RE = re.compile(r"https?://[^\s)\]>`]+")


def _cors(request: web.Request, resp: web.StreamResponse) -> web.StreamResponse:
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS or origin.startswith("http://localhost"):
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Vary"] = "Origin"
    return resp


def _rate_ok(ip: str) -> bool:
    now = time.time()
    q = _hits[ip]
    while q and now - q[0] > 3600:
        q.popleft()
    if len(q) >= RATE_PER_HOUR:
        return False
    q.append(now)
    return True


def _citations(text: str) -> list[str]:
    found = []
    for m in BRACKET_RE.finditer(text):
        found += [p.strip() for p in re.split(r"[,;]", m.group(1)) if FILE_RE.match(p.strip())]
    found += URL_RE.findall(text)
    return list(dict.fromkeys(found))


async def chat(request: web.Request) -> web.StreamResponse:
    try:
        body = await request.json()
    except Exception:
        return _cors(request, web.json_response({"error": "Send JSON: {\"message\": \"...\"}"}, status=400))
    message = str(body.get("message") or "").strip()
    if not message:
        return _cors(request, web.json_response({"error": "message is required"}, status=400))
    if len(message) > MAX_CHARS:
        return _cors(request, web.json_response({"error": f"message is over {MAX_CHARS} characters"}, status=400))
    ip = request.headers.get("X-Forwarded-For", request.remote or "").split(",")[0].strip()
    if not _rate_ok(ip):
        return _cors(request, web.json_response({"error": "rate limit reached, try again later"}, status=429))

    started = time.monotonic()
    async with _slots:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT_S)) as s:
                async with s.post(
                    HERMES_URL,
                    headers={"Authorization": f"Bearer {HERMES_KEY}"},
                    json={"model": "hermes-agent", "stream": False,
                          "messages": [{"role": "user", "content": message}]},
                ) as r:
                    data = await r.json(content_type=None)
                    if r.status != 200:
                        return _cors(request, web.json_response({"error": "agent error", "status": r.status}, status=502))
        except asyncio.TimeoutError:
            return _cors(request, web.json_response({"error": "agent timed out"}, status=504))
    answer = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    return _cors(request, web.json_response({
        "answer": answer,
        "citations": _citations(answer),
        "seconds": round(time.monotonic() - started, 1),
    }))


async def options(request: web.Request) -> web.StreamResponse:
    return _cors(request, web.Response(status=204))


async def health(request: web.Request) -> web.StreamResponse:
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as s:
            async with s.get(HERMES_URL.replace("/v1/chat/completions", "/health")) as r:
                ok = r.status == 200
    except Exception:
        ok = False
    return _cors(request, web.json_response({"ok": ok}, status=200 if ok else 503))


app = web.Application(client_max_size=64 * 1024)
app.add_routes([web.post("/chat", chat), web.options("/chat", options), web.get("/health", health)])

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=PORT, print=None)
