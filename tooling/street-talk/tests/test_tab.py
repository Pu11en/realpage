"""Street Talk tab: page exists, is in the tab bar, and reads the saved data file."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_tab_in_nav_bar():
    app = (ROOT / "site/js/app.js").read_text()
    assert 'href: "street-talk.html"' in app and '"Street Talk"' in app


def test_page_reads_saved_data_and_handles_empty():
    page = (ROOT / "site/street-talk.html").read_text()
    assert 'renderShell("street")' in page
    assert "data/street-talk.json" in page
    assert "No posts yet" in page
    assert "property.html?id=" in page
    assert "warm lead" in page
    assert "PropertyStack" not in page and "Hermes" not in page
