"""E1: the whole app needs sign-in (Drew 2026-09-15). Runs the real
site/Caddyfile with the fake chat upstream (tooling/qa/fake-webui) and checks
the gate. Offline: no network and no paid calls. The first run unpacks the
Caddy binary out of the cache/caddy:2-alpine image into .caddy-bin/."""
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CADDY = ROOT / ".caddy-bin" / "caddy"
FAKE = ROOT / "tooling" / "qa" / "fake-webui" / "server.py"
COOKIE = "fake_signed_in=1"


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _ensure_caddy() -> None:
    if CADDY.exists():
        return
    on_path = shutil.which("caddy")
    if on_path:
        CADDY.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(on_path, CADDY)
        CADDY.chmod(0o755)
        return
    CADDY.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("docker") is None:
        pytest.fail("E1 needs Caddy: install Docker (caddy:2-alpine) or put a caddy binary at .caddy-bin/caddy")
    created = subprocess.run(["docker", "create", "caddy:2-alpine"], capture_output=True, text=True)
    cid = created.stdout.strip()
    if created.returncode or not cid:
        pytest.fail(f"could not create caddy:2-alpine (is the image pulled?): {created.stderr.strip()}")
    try:
        subprocess.run(["docker", "cp", f"{cid}:/usr/bin/caddy", str(CADDY)], check=True, capture_output=True)
    finally:
        subprocess.run(["docker", "rm", cid], capture_output=True)
    if not CADDY.exists():
        pytest.fail("docker cp did not produce .caddy-bin/caddy")
    CADDY.chmod(0o755)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _get(url: str, cookie: str | None = None, headers: dict | None = None):
    req = urllib.request.Request(url)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    if cookie:
        req.add_header("Cookie", cookie)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)
    try:
        with opener.open(req, timeout=10) as r:
            return r.status, r.headers.get("Location"), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location"), e.read()


def _post_json(url: str, payload: dict, cookie: str | None = None):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    if cookie:
        req.add_header("Cookie", cookie)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)
    try:
        with opener.open(req, timeout=20) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


@pytest.fixture(scope="module")
def gate():
    _ensure_caddy()
    chat_port, web_port = _free_port(), _free_port()
    xdg = {"XDG_CONFIG_HOME": str(ROOT / ".caddy-bin" / "xdg-config"),
           "XDG_DATA_HOME": str(ROOT / ".caddy-bin" / "xdg-data")}
    fake = subprocess.Popen([sys.executable, str(FAKE), str(chat_port)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    env = dict(os.environ, **xdg, PORT=str(web_port),
               CHAT_UPSTREAM=f"http://127.0.0.1:{chat_port}",
               SITE_ROOT=str(ROOT / "site"))
    caddy = subprocess.Popen([str(CADDY), "run", "--config", str(ROOT / "site" / "Caddyfile"),
                              "--adapter", "caddyfile"],
                             env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{web_port}"
    for _ in range(60):
        try:
            if _get(base + "/privacy.html")[0] == 200:
                break
        except OSError:
            pass
        time.sleep(0.2)
    else:
        caddy.terminate()
        fake.terminate()
        pytest.fail("Caddy did not start with site/Caddyfile")
    yield base
    caddy.terminate()
    fake.terminate()
    for p in (caddy, fake):
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()


def test_signed_out_pages_and_data_are_sent_to_sign_in(gate):
    # "/" redirects to the Map first (the app opens there); the Map is in the gated list below,
    # so a signed-out visitor still ends at sign-in.
    status, loc, _ = _get(gate + "/")
    assert (status, loc) == (302, "/map.html")
    for path in ("/index.html", "/map.html", "/property.html?id=tx-1", "/master-table.html",
                 "/under-the-hood.html", "/data/leads.json",
                 "/data/areas/tx.json", "/js/app.js", "/vendor/x.js"):
        status, loc, _ = _get(gate + path)
        assert status == 302, (path, status)
        assert loc and "/auth?redirect=" in loc, (path, loc)


def test_public_page_and_shell_stay_open(gate):
    for path in ("/privacy.html", "/css/styles.css", "/auth"):
        status, _, _ = _get(gate + path)
        assert status == 200, (path, status)


def test_signed_in_request_gets_the_page_and_the_data(gate):
    status, _, body = _get(gate + "/index.html", cookie=COOKIE)
    assert status == 200 and b"Early Leads" in body
    status, _, body = _get(gate + "/data/areas/tx.json", cookie=COOKIE)
    assert status == 200 and b'"leads"' in body


def test_chat_panel_frame_home_and_its_api_stay_public(gate):
    # The panel frames "/" (Sec-Fetch-Dest: iframe) and calls the chat app's
    # current-user endpoint: both must reach the chat app, never the gate.
    status, _, _ = _get(gate + "/", headers={"Sec-Fetch-Dest": "iframe"})
    assert status == 200
    status, _, _ = _get(gate + "/api/v1/auths/")
    assert status == 401  # the fake chat app's "not signed in", proxied through


def test_caddyfile_gates_the_app_paths():
    conf = (ROOT / "site" / "Caddyfile").read_text()
    assert "forward_auth" in conf and "uri /api/v1/auths/" in conf
    assert "/privacy.html" in conf
    assert "/case-study" not in conf and "CASESTUDY_UPSTREAM" not in conf
