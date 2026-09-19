"""Chat panel: opens only when asked (2026-09-19) and asks for a free account."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JS = (ROOT / "site/js/chat-panel.js").read_text(encoding="utf-8")
PAGES = ["index.html", "map.html", "property.html", "under-the-hood.html"]


def test_docked_on_wide_leads_page_only():
    # Wide Leads page: docked from the first look (it shrinks the page, never covers it).
    # Narrow screens and every other page: waits to be asked.
    assert 'function docksByDefault()' in JS
    assert 'window.matchMedia("(min-width: 1200px)")' in JS
    assert "if (v === null) return docksByDefault();" in JS
    assert 'sessionStorage.setItem(STORAGE_OPEN, v ? "1" : "0")' in JS
    assert 'addEventListener("click", closePanel)' in JS


def test_signed_out_prompt_wording():
    assert '<button class="chat-panel-signin" id="chat-panel-signin">Make a free account</button>' in JS
    assert 'id="chat-panel-signin-link">Already have one? Sign in</a>' in JS
    assert "Sign in free" not in JS


def test_both_prompts_use_the_existing_sign_in():
    assert 'signinBtn.addEventListener("click", startSignIn)' in JS
    assert '"#chat-panel-signin-link").addEventListener("click", startSignIn)' in JS


def test_every_site_page_loads_the_panel():
    for page in PAGES:
        assert 'src="js/chat-panel.js"' in (ROOT / "site" / page).read_text(encoding="utf-8"), page
