"""T5: the CraneSignal wordmark in the header links to index.html on every app page."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP_JS = (ROOT / "site/js/app.js").read_text(encoding="utf-8")

APP_PAGES = ["index.html", "map.html", "ai-visibility.html", "under-the-hood.html", "property.html"]


def test_wordmark_is_a_link_to_index():
    fn = APP_JS.split("function renderShell", 1)[1].split("\nfunction ", 1)[0]
    assert '<a class="wordmark" href="index.html">CraneSignal</a>' in fn


def test_every_app_page_calls_render_shell():
    for page in APP_PAGES:
        html = (ROOT / "site" / page).read_text(encoding="utf-8")
        assert "renderShell(" in html, f"{page} doesn't call renderShell()"
