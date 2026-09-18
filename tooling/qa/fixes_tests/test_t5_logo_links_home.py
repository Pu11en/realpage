"""T5: the CraneSignal wordmark in the header links back to the CraneSignal home page
(LANDING_URL) on every app page. It pointed at index.html until the app moved to open on the Map."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP_JS = (ROOT / "site/js/app.js").read_text(encoding="utf-8")

APP_PAGES = ["index.html", "map.html", "under-the-hood.html", "property.html"]


def test_wordmark_is_a_link_to_the_home_page():
    fn = APP_JS.split("function renderShell", 1)[1].split("\nfunction ", 1)[0]
    assert '<a class="wordmark" href="${LANDING_URL}"' in fn
    assert 'const LANDING_URL = ' in APP_JS and '"https://cranesignal.com"' in APP_JS


def test_every_app_page_calls_render_shell():
    for page in APP_PAGES:
        html = (ROOT / "site" / page).read_text(encoding="utf-8")
        assert "renderShell(" in html, f"{page} doesn't call renderShell()"
