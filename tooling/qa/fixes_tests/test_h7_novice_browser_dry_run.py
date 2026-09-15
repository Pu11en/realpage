"""H7: the fresh signed-in preview must build the site from its own context.

The human-test overlay is the only Compose file that builds the Caddy front
door.  Building it from the repository root makes site/Dockerfile fail before
the sign-in screen can load because Caddyfile lives inside site/.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OVERLAY = ROOT / "chatbot" / "docker-compose.human-test.yml"
LOCAL_COMPOSE = ROOT / "chatbot" / "docker-compose.local.yml"
APP_JS = ROOT / "site" / "js" / "app.js"
CHAT_PANEL_JS = ROOT / "site" / "js" / "chat-panel.js"


def test_human_preview_site_uses_the_dockerfile_expected_context():
    overlay = OVERLAY.read_text(encoding="utf-8")
    dockerfile = (ROOT / "site" / "Dockerfile").read_text(encoding="utf-8")

    assert "context: ../site" in overlay
    assert "dockerfile: Dockerfile" in overlay
    assert "COPY Caddyfile /etc/caddy/Caddyfile" in dockerfile
    assert "COPY . /srv" in dockerfile


def test_human_preview_loads_the_post_signin_cranesignal_redirect():
    compose = LOCAL_COMPOSE.read_text(encoding="utf-8")
    loader = (ROOT / "chatbot" / "branding" / "loader.js").read_text(encoding="utf-8")

    assert "./branding/loader.js:/app/build/static/loader.js:ro" in compose
    assert 'var toDashboard = function () { location.replace("/"); };' in loader
    assert 'if (p !== last) { last = p; if (!allowed(p)) toDashboard(); }' in loader


def test_human_preview_routes_the_chat_panel_through_its_front_door():
    app_js = APP_JS.read_text(encoding="utf-8")

    assert 'location.port === "8765"' in app_js
    assert "? location.origin // isolated human preview" in app_js
    assert '"http://localhost:3000"' in app_js


def test_sign_out_clears_the_same_origin_chat_token_before_redirecting():
    chat_panel = CHAT_PANEL_JS.read_text(encoding="utf-8")
    sign_out = chat_panel.split("function signOut()", 1)[1].split("\n  function ", 1)[0]

    assert "/api/v1/auths/signout" in sign_out
    assert 'localStorage.removeItem("token")' in sign_out
    assert 'location.href = `${base}/auth`' in sign_out
