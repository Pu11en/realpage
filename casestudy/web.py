"""Small web surface for the case-study demo.

The browser receives the exact JSONL bytes produced by ``submission_jsonl`` and a
separate diagnostics object.  It never reconstructs the public export from the
diagnostics.  Production proxy, authentication, limits, and container wiring are C11.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from aiohttp import web

from casestudy.pipeline import run_batch, submission_jsonl
from casestudy.writer import WriterConfig

WEB_ROOT = Path(__file__).with_name("web_assets")
DEFAULT_MAX_REQUEST_BYTES = 2 * 1024 * 1024
DEFAULT_MAX_BATCH_SIZE = 100
MAX_BATCH_SIZE_KEY: web.AppKey[int] = web.AppKey("max_batch_size", int)


def _positive_env_int(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


def _lines(text: str) -> list[str]:
    """Match the CLI's ``str.splitlines()`` behavior byte for byte."""
    return text.splitlines()


def run_payload(text: str, *, offline: bool) -> dict[str, Any]:
    config = WriterConfig(enabled=False) if offline else WriterConfig.from_env()
    results = run_batch(_lines(text), config=config)
    exported = submission_jsonl(results)
    records = []
    for index, result in enumerate(results):
        records.append({
            "index": index,
            "submission_line": result.submission_line(),
            "diagnostics": result.diagnostics(),
        })
    return {
        "record_count": len(records),
        "submission_jsonl": exported,
        "records": records,
        "mode": "offline" if offline else "configured",
    }


async def run_handler(request: web.Request) -> web.Response:
    try:
        payload = await request.json()
    except web.HTTPRequestEntityTooLarge:
        raise
    except Exception:
        return web.json_response({"error": "Request body must be JSON."}, status=400)
    if not isinstance(payload, dict) or not isinstance(payload.get("jsonl"), str):
        return web.json_response({"error": "jsonl must be a string."}, status=400)
    offline = payload.get("offline", False)
    if not isinstance(offline, bool):
        return web.json_response({"error": "offline must be true or false."}, status=400)
    line_count = len(_lines(payload["jsonl"]))
    max_batch_size = request.app[MAX_BATCH_SIZE_KEY]
    if line_count > max_batch_size:
        return web.json_response(
            {"error": f"Batch has {line_count} records; the limit is {max_batch_size}."},
            status=413,
        )
    try:
        return web.json_response(run_payload(payload["jsonl"], offline=offline))
    except Exception as exc:  # the batch protects records; this protects the request shell
        return web.json_response({"error": f"The batch could not run: {type(exc).__name__}."}, status=500)


async def asset_handler(request: web.Request) -> web.FileResponse:
    name = request.match_info["name"]
    if name not in {"app.js", "styles.css"}:
        raise web.HTTPNotFound()
    return web.FileResponse(WEB_ROOT / name)


async def page_handler(_request: web.Request) -> web.FileResponse:
    return web.FileResponse(WEB_ROOT / "index.html")


async def health_handler(_request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


@web.middleware
async def request_limit_errors(request: web.Request, handler):
    try:
        return await handler(request)
    except web.HTTPRequestEntityTooLarge:
        return web.json_response({"error": "Maximum request body size exceeded."}, status=413)


def create_app(*, max_request_bytes: int | None = None, max_batch_size: int | None = None) -> web.Application:
    request_limit = max_request_bytes or _positive_env_int(
        "CASESTUDY_MAX_REQUEST_BYTES", DEFAULT_MAX_REQUEST_BYTES
    )
    batch_limit = max_batch_size or _positive_env_int(
        "CASESTUDY_MAX_BATCH_SIZE", DEFAULT_MAX_BATCH_SIZE
    )
    app = web.Application(client_max_size=request_limit, middlewares=[request_limit_errors])
    app[MAX_BATCH_SIZE_KEY] = batch_limit
    app.router.add_get("/health", health_handler)
    app.router.add_post("/case-study/api/run", run_handler)
    app.router.add_get("/case-study/assets/{name}", asset_handler)
    app.router.add_get("/case-study", page_handler)
    app.router.add_get("/case-study/", page_handler)
    return app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Case-study demo web service")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", default=int(os.environ.get("PORT", "8091")), type=int)
    args = parser.parse_args(argv)
    web.run_app(create_app(), host=args.host, port=args.port, print=None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
