"""T3: every app page gets a "Sign out" link in the shared shell, hidden by default (no sign-in
locally), which calls the chat app's sign-out endpoint, clears the local session, then lands on the
chat app's sign-in page."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP_JS = (ROOT / "site/js/app.js").read_text(encoding="utf-8")
CHAT_JS = (ROOT / "site/js/chat-panel.js").read_text(encoding="utf-8")

APP_PAGES = ["index.html", "under-the-hood.html", "property.html"]


def test_every_app_page_calls_render_shell():
    for page in APP_PAGES:
        html = (ROOT / "site" / page).read_text(encoding="utf-8")
        assert "renderShell(" in html, f"{page} doesn't call renderShell()"


def test_shell_includes_a_hidden_sign_out_link():
    assert 'id="sign-out-link"' in APP_JS
    fn = APP_JS.split("function renderShell", 1)[1].split("\nfunction ", 1)[0]
    assert 'id="sign-out-link"' in fn
    assert "display: none" in fn.split('id="sign-out-link"', 1)[1].split("</a>", 1)[0]


def test_sign_out_calls_chat_app_and_lands_on_its_sign_in_page():
    fn = CHAT_JS.split("function signOut", 1)[1].split("\n  function ", 1)[0]
    assert "/api/v1/auths/signout" in fn
    assert "sessionStorage.removeItem(STORAGE_OPEN)" in fn
    assert 'location.href = `${base}/auth`' in fn


def test_sign_out_link_only_shown_once_a_real_session_is_confirmed():
    fn = CHAT_JS.split("function checkAuth", 1)[1].split("\n  function ", 1)[0]
    assert "setSignOutVisible(false)" in fn
    assert "setSignOutVisible(res.ok)" in fn


def test_wire_sign_out_does_not_double_bind():
    fn = CHAT_JS.split("function wireSignOut", 1)[1].split("\n  function ", 1)[0]
    assert "link.dataset.signOutWired" in fn
    assert "window.wireSignOut = wireSignOut" in CHAT_JS
