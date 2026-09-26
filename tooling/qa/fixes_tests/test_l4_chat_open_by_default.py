"""Chat panel: opens only when asked (2026-09-19) and asks for a free account."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JS = (ROOT / "site/js/chat-panel.js").read_text(encoding="utf-8")
PAGES = ["index.html", "property.html"]


def test_docked_on_every_wide_page():
    # Drew 2026-09-19: the agent is part of the page. Every page opens with it docked
    # on screens >= 900px; closing it only lasts for that page view.
    assert 'function docksByDefault()' in JS
    assert 'window.matchMedia("(min-width: 900px)")' in JS
    assert "return docksByDefault() || sessionStorage.getItem(STORAGE_OPEN) === \"1\";" in JS
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
