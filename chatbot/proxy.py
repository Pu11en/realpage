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

HERMES_BASE = f"http://127.0.0.1:{os.environ.get('API_SERVER_PORT', '8642')}/v1"
HERMES_URL = f"{HERMES_BASE}/chat/completions"
HERMES_KEY = os.environ["API_SERVER_KEY"]
PORT = int(os.environ.get("PORT", "8080"))
ALLOWED_ORIGINS = {o.strip() for o in os.environ.get(
    "CHAT_ALLOWED_ORIGINS", "https://propertystack-production.up.railway.app"
).split(",") if o.strip()}
MAX_CHARS = 1000
HISTORY_MAX = 10          # prior user/assistant turns forwarded per request
HISTORY_ITEM_CHARS = 6000
RATE_PER_HOUR = int(os.environ.get("CHAT_RATE_PER_HOUR", "30"))
TIMEOUT_S = 180  # call prep with web lookups can take ~1-2 min

# Open WebUI gateway (/v1/*): per-signed-in-user rate limit + daily $ cap.
GATEWAY_ADMIN_EMAIL = os.environ.get("CHAT_ADMIN_EMAIL", "kidquick360@gmail.com").strip().lower()
GATEWAY_DAILY_CAP_USD = float(os.environ.get("CHAT_DAILY_CAP_USD", "3.0"))
GATEWAY_RATE_PER_MINUTE = int(os.environ.get("CHAT_RATE_PER_MINUTE", "40"))
GATEWAY_USAGE_FILE = os.path.join(os.environ.get("HERMES_HOME", "/opt/data"), "usage.json")
# DeepSeek cache-miss pricing (USD per token); ~4 chars/token estimate since we
# don't run Hermes' tokenizer here.
GATEWAY_PRICE_IN_PER_TOKEN = 0.14 / 1_000_000
GATEWAY_PRICE_OUT_PER_TOKEN = 0.28 / 1_000_000
GATEWAY_CHARS_PER_TOKEN = 4

_hits: dict[str, deque] = defaultdict(deque)
_gateway_hits: dict[str, deque] = defaultdict(deque)
_gateway_usage_lock = asyncio.Lock()
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


def _rate_ok(ip: str) -> int:
    """0 if allowed, else minutes until the next request is allowed."""
    now = time.time()
    q = _hits[ip]
    while q and now - q[0] > 3600:
        q.popleft()
    if len(q) >= RATE_PER_HOUR:
        return max(1, int((q[0] + 3600 - now) // 60) + 1)
    q.append(now)
    return 0


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
    wait = _rate_ok(ip)
    if wait:
        raise _BadRequest(f"rate limit reached, try again in {wait} minutes", 429)
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


def _gateway_load_usage() -> dict:
    try:
        with open(GATEWAY_USAGE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _gateway_save_usage(usage: dict) -> None:
    try:
        os.makedirs(os.path.dirname(GATEWAY_USAGE_FILE), exist_ok=True)
        with open(GATEWAY_USAGE_FILE, "w") as f:
            json.dump(usage, f)
    except OSError:
        pass


def _gateway_usage_key(email: str) -> str:
    return f"{email}|{time.strftime('%Y-%m-%d', time.gmtime())}"


def _gateway_est_cost(chars: int, *, is_output: bool) -> float:
    tokens = chars / GATEWAY_CHARS_PER_TOKEN
    return tokens * (GATEWAY_PRICE_OUT_PER_TOKEN if is_output else GATEWAY_PRICE_IN_PER_TOKEN)


def _gateway_rate_ok(email: str) -> bool:
    now = time.time()
    q = _gateway_hits[email]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= GATEWAY_RATE_PER_MINUTE:
        return False
    q.append(now)
    return True


async def _gateway_check(email: str) -> str:
    """Empty string if allowed, else the reason it's blocked."""
    if not _gateway_rate_ok(email):
        return f"too many messages, wait a minute (limit {GATEWAY_RATE_PER_MINUTE}/min)"
    if email == GATEWAY_ADMIN_EMAIL or not email:
        return ""
    async with _gateway_usage_lock:
        spent = _gateway_load_usage().get(_gateway_usage_key(email), 0.0)
    if spent >= GATEWAY_DAILY_CAP_USD:
        return f"daily chat limit reached (${GATEWAY_DAILY_CAP_USD:.2f}), resets tomorrow"
    return ""


async def _gateway_add_cost(email: str, cost: float) -> None:
    if not email or email == GATEWAY_ADMIN_EMAIL:
        return
    async with _gateway_usage_lock:
        usage = _gateway_load_usage()
        key = _gateway_usage_key(email)
        usage[key] = usage.get(key, 0.0) + cost
        _gateway_save_usage(usage)


def _gateway_auth_ok(request: web.Request) -> bool:
    return request.headers.get("Authorization", "") == f"Bearer {HERMES_KEY}"


async def gateway_models(request: web.Request) -> web.StreamResponse:
    """Open WebUI's /v1/models probe. Not user-scoped, no cap needed."""
    if not _gateway_auth_ok(request):
        return web.json_response({"error": "unauthorized"}, status=401)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as s:
        async with s.get(f"{HERMES_BASE}/models", headers=dict(request.headers)) as r:
            data = await r.json(content_type=None)
            return web.json_response(data, status=r.status)


async def gateway_chat(request: web.Request) -> web.StreamResponse:
    """Open WebUI's OpenAI-compatible endpoint, gated per signed-in user.

    Open WebUI is told to forward X-OpenWebUI-User-Email (see
    ENABLE_FORWARD_USER_INFO_HEADERS in docker-compose); Hermes itself has no
    concept of separate users, so the cap lives here in front of it.
    """
    if not _gateway_auth_ok(request):
        return web.json_response({"error": "unauthorized"}, status=401)
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad json"}, status=400)
    email = request.headers.get("X-Openwebui-User-Email", "").strip().lower()
    blocked = await _gateway_check(email)
    if blocked:
        return web.json_response({"error": {"message": blocked, "type": "rate_limit_exceeded"}}, status=429)
    req_chars = sum(len(str(m.get("content", ""))) for m in body.get("messages", []) if isinstance(m, dict))

    async with _slots:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT_S)) as s:
                async with s.post(HERMES_URL, headers={"Authorization": f"Bearer {HERMES_KEY}"}, json=body) as r:
                    if not body.get("stream"):
                        data = await r.json(content_type=None)
                        await _gateway_add_cost(email, _gateway_est_cost(req_chars, is_output=False)
                                                 + _gateway_est_cost(len(json.dumps(data)), is_output=True))
                        return web.json_response(data, status=r.status)
                    resp = web.StreamResponse(headers={
                        "Content-Type": "text/event-stream", "Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
                    await resp.prepare(request)
                    out_chars = 0
                    async for chunk in r.content.iter_any():
                        out_chars += len(chunk)
                        await resp.write(chunk)
                    await _gateway_add_cost(email, _gateway_est_cost(req_chars, is_output=False)
                                             + _gateway_est_cost(out_chars, is_output=True))
                    return resp
        except asyncio.TimeoutError:
            return web.json_response({"error": "agent timed out"}, status=504)


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
                web.post("/chat/stream", chat_stream), web.options("/chat/stream", options), web.get("/health", health),
                web.post("/v1/chat/completions", gateway_chat), web.options("/v1/chat/completions", options),
                web.get("/v1/models", gateway_models)])

if __name__ == "__main__":
    # Both: IPv4 for Railway's health check, IPv6 for its private network (asyncio makes "::" v6-only).
    web.run_app(app, host=["0.0.0.0", "::"], port=PORT, print=None)
