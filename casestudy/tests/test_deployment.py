"""C11: production container, health, limits, and local wiring."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = (ROOT / "casestudy" / "data" / "sample.jsonl").read_text(encoding="utf-8").splitlines()[0]


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _request(url: str, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


@pytest.fixture(scope="module")
def limited_server():
    port = _free_port()
    env = dict(
        os.environ,
        CASESTUDY_OFFLINE="true",
        CASESTUDY_MAX_REQUEST_BYTES="65536",
        CASESTUDY_MAX_BATCH_SIZE="12",
    )
    process = subprocess.Popen(
        [sys.executable, "-m", "casestudy.web", "--port", str(port)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            if _request(base + "/health")[0] == 200:
                break
        except OSError:
            pass
        time.sleep(0.05)
    else:
        process.terminate()
        pytest.fail("limited case-study server did not start")
    yield base
    process.terminate()
    process.wait(timeout=5)


def test_health_and_batch_limit(limited_server):
    status, body = _request(limited_server + "/health")
    assert status == 200 and body == {"status": "ok"}
    twelve = "\n".join([SAMPLE] * 12)
    status, body = _request(limited_server + "/case-study/api/run", {"jsonl": twelve, "offline": True})
    assert status == 200 and body["record_count"] == 12
    thirteen = twelve + "\n" + SAMPLE
    status, body = _request(limited_server + "/case-study/api/run", {"jsonl": thirteen, "offline": True})
    assert status == 413 and "limit is 12" in body["error"]


def test_request_size_limit_is_413(limited_server):
    oversized = {"jsonl": "x" * 70000, "offline": True}
    status, body = _request(limited_server + "/case-study/api/run", oversized)
    assert status == 413
    assert "Maximum request body size" in body["error"]


def test_container_is_isolated_non_root_and_railway_documented():
    dockerfile = (ROOT / "casestudy" / "Dockerfile").read_text(encoding="utf-8")
    readme = (ROOT / "casestudy" / "README.md").read_text(encoding="utf-8")
    copy_lines = [line.strip() for line in dockerfile.splitlines() if line.strip().startswith("COPY ")]
    assert copy_lines and all(line.startswith("COPY casestudy") for line in copy_lines)
    assert "USER casestudy" in dockerfile and "tzdata" in dockerfile and "/health" in dockerfile
    assert "casestudy/Dockerfile" in readme
    assert "python -m casestudy.web --host 0.0.0.0" in readme
    assert "DEEPSEEK_API_KEY" in readme and "propertystack-case-study" in readme


def test_front_door_compose_and_navigation_are_wired():
    caddy = (ROOT / "site" / "Caddyfile").read_text(encoding="utf-8")
    nav = (ROOT / "site" / "js" / "app.js").read_text(encoding="utf-8")
    local = (ROOT / "chatbot" / "docker-compose.local.yml").read_text(encoding="utf-8")
    preview = (ROOT / "chatbot" / "docker-compose.human-test.yml").read_text(encoding="utf-8")
    case_block = caddy.split("@case_study path /case-study*", 1)[1].split("# The app's pages", 1)[0]
    assert "forward_auth" in case_block and "reverse_proxy {$CASESTUDY_UPSTREAM" in case_block
    assert 'label: "Case Study"' in nav and '"/case-study"' in nav
    assert "dockerfile: casestudy/Dockerfile" in local and '"18091:8080"' in local
    assert "CASESTUDY_UPSTREAM: http://casestudy:8080" in preview
