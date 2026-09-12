"""Public chat endpoint for the PropertyStack site.

Hermes' API server needs a bearer key, which a static site can't hide, so this
small front sits on Railway's $PORT and forwards to Hermes on localhost:

  POST /chat   {"message": "..."}  ->  {"answer": "...", "citations": [...]}
  GET  /health

Chats live on the server: the page sends a random session_id and Hermes keeps
the transcript in its state.db (X-Hermes-Session-Id). Without a session_id the
old stateless mode is used (page sends its own history). Guardrails on cost: message length cap, per-IP rate limit, a small
concurrency cap and a timeout.
"""
import asyncio
import json
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
HISTORY_MAX = 10          # prior user/assistant turns forwarded per request
HISTORY_ITEM_CHARS = 6000
RATE_PER_HOUR = int(os.environ.get("CHAT_RATE_PER_HOUR", "30"))
TIMEOUT_S = 120

_hits: dict[str, deque] = defaultdict(deque)
_slots = asyncio.Semaphore(int(os.environ.get("CHAT_MAX_CONCURRENT", "3")))
BRACKET_RE = re.compile(r"\[([^\[\]]+)\]")
FILE_RE = re.compile(r"^[\w./-]+\.(?:csv|md|jsonl)$")
SESSION_RE = re.compile(r"^[A-Za-z0-9-]{16,64}$")
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


class _BadRequest(Exception):
    def __init__(self, error: str, status: int = 400):
        self.error, self.status = error, status


async def _parse(request: web.Request) -> tuple[str, str, list]:
    """Validate a chat request -> (message, session_id, history). Raises _BadRequest."""
    try:
        body = await request.json()
    except Exception:
        raise _BadRequest("Send JSON: {\"message\": \"...\"}")
    message = str(body.get("message") or "").strip()
    if not message:
        raise _BadRequest("message is required")
    if len(message) > MAX_CHARS:
        raise _BadRequest(f"message is over {MAX_CHARS} characters")
    session_id = str(body.get("session_id") or "").strip()
    if session_id and not SESSION_RE.match(session_id):
        raise _BadRequest("bad session_id")
    # With a session_id Hermes loads the chat from its own store; the page's
    # history is only used by old pages that don't send one.
    raw = [] if session_id else (body.get("history") or [])
    if not isinstance(raw, list):
        raise _BadRequest("history must be a list")
    history = []
    for h in raw[-HISTORY_MAX:]:
        if not isinstance(h, dict) or h.get("role") not in ("user", "assistant"):
            continue
        content = str(h.get("content") or "").strip()[:HISTORY_ITEM_CHARS]
        if content:
            history.append({"role": h["role"], "content": content})
    ip = request.headers.get("X-Forwarded-For", request.remote or "").split(",")[0].strip()
    if not _rate_ok(ip):
        raise _BadRequest("rate limit reached, try again later", 429)
    return message, session_id, history


def _hermes_headers(session_id: str) -> dict:
    return {"Authorization": f"Bearer {HERMES_KEY}",
            **({"X-Hermes-Session-Id": f"web-{session_id}"} if session_id else {})}


async def chat(request: web.Request) -> web.StreamResponse:
    try:
        message, session_id, history = await _parse(request)
    except _BadRequest as e:
        return _cors(request, web.json_response({"error": e.error}, status=e.status))

    started = time.monotonic()
    async with _slots:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT_S)) as s:
                async with s.post(
                    HERMES_URL,
                    headers=_hermes_headers(session_id),
                    json={"model": "hermes-agent", "stream": False,
                          "messages": history + [{"role": "user", "content": message}]},
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


# Plain-English labels for the "what it's doing" line.
TOOL_LABELS = {
    "ps_schema": "Checking what data there is…",
    "ps_sql": "Looking through the building data…",
    "ps_research_search": "Searching the research notes…",
    "ps_research_read": "Reading a research note…",
}


async def chat_stream(request: web.Request) -> web.StreamResponse:
    """Same as /chat, but Server-Sent Events: progress, delta (text), done or error.

    If the page disconnects (Stop / closed tab), the Hermes request is closed
    too and Hermes interrupts the agent.
    """
    try:
        message, session_id, history = await _parse(request)
    except _BadRequest as e:
        return _cors(request, web.json_response({"error": e.error}, status=e.status))
    resp = _cors(request, web.StreamResponse(headers={
        "Content-Type": "text/event-stream", "Cache-Control": "no-cache", "X-Accel-Buffering": "no"}))
    await resp.prepare(request)

    async def send(event: str, data: dict) -> None:
        await resp.write(f"event: {event}\ndata: {json.dumps(data)}\n\n".encode())

    started = time.monotonic()
    answer = ""
    async with _slots:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT_S)) as s:
                async with s.post(
                    HERMES_URL,
                    headers=_hermes_headers(session_id),
                    json={"model": "hermes-agent", "stream": True,
                          "messages": history + [{"role": "user", "content": message}]},
                ) as r:
                    if r.status != 200:
                        await send("error", {"error": "agent error", "status": r.status})
                        return resp
                    event = ""
                    async for raw in r.content:
                        line = raw.decode("utf-8", "replace").rstrip("\r\n")
                        if line.startswith("event:"):
                            event = line[6:].strip()
                            continue
                        if not line.startswith("data:"):
                            if not line:
                                event = ""
                            continue
                        payload = line[5:].strip()
                        if payload == "[DONE]":
                            break
                        try:
                            data = json.loads(payload)
                        except ValueError:
                            continue
                        if event == "hermes.tool.progress":
                            if data.get("status") == "running":
                                # Text before a tool call is the bot thinking aloud; the page
                                # drops it when a progress line arrives, so drop it here too.
                                answer = ""
                                await send("progress", {"label": TOOL_LABELS.get(data.get("tool"), "Working…")})
                            continue
                        if data.get("error"):
                            await send("error", {"error": "agent error"})
                            return resp
                        choice = (data.get("choices") or [{}])[0]
                        text = (choice.get("delta") or {}).get("content") or ""
                        if text:
                            answer += text
                            await send("delta", {"text": text})
        except asyncio.TimeoutError:
            await send("error", {"error": "agent timed out"})
            return resp
    await send("done", {"citations": _citations(answer), "seconds": round(time.monotonic() - started, 1)})
    return resp


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


app = web.Application(client_max_size=128 * 1024)
app.add_routes([web.post("/chat", chat), web.options("/chat", options),
                web.post("/chat/stream", chat_stream), web.options("/chat/stream", options), web.get("/health", health)])

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=PORT, print=None)
