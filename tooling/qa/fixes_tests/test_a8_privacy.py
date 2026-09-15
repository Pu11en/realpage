"""A8: privacy page covers email sign-up, what we store and a contact line; menu links to it."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_privacy_page_content():
    s = (ROOT / "site/privacy.html").read_text()
    for needle in ("Google", "sign up with your", "chats", "early access", "Contact", "mailto:"):
        assert needle in s, needle
    assert "support email shown on the Google sign-in screen" not in s


def test_menu_links_privacy():
    assert 'href="privacy.html"' in (ROOT / "site/js/app.js").read_text()
