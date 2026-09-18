"""T4: unknown addresses (like /nope.html) get a real CraneSignal 404 page with
status 404, not the chat app's leads page. Runs the real site/Caddyfile with the
fake chat upstream, like the E1 sign-in test. Offline: no network, no paid calls."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_e1_signin import COOKIE, _get, gate  # noqa: F401  (reuses the E1 fixture)

ROOT = Path(__file__).resolve().parents[3]


def test_unknown_page_is_a_real_404(gate):
    status, _, body = _get(gate + "/nope.html")
    assert status == 404, status
    assert b"Page not found" in body
    assert b"CraneSignal" in body


def test_pages_load_signed_out_and_signed_in(gate):
    status, _, body = _get(gate + "/index.html")
    assert status == 200 and b"Early Leads" in body
    status, _, body = _get(gate + "/index.html", cookie=COOKIE)
    assert status == 200 and b"Early Leads" in body


def test_chat_app_routes_still_reach_the_chat_app(gate):
    status, _, _ = _get(gate + "/auth")
    assert status == 200
    status, _, _ = _get(gate + "/api/v1/auths/")
    assert status == 401


def test_404_page_exists_on_disk():
    assert (ROOT / "site" / "404.html").exists()
