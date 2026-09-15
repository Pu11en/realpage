"""A9: map state labels sit in a white pill and scale up on narrow (phone) maps."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_label_has_pill():
    js = (ROOT / "site/js/map.js").read_text()
    assert 'class="label-pill"' in js
    assert "layoutLabels" in js and "resize" in js
    css = (ROOT / "site/map.html").read_text()
    assert ".label-pill" in css


def test_label_font_scales_for_phone():
    js = (ROOT / "site/js/map.js").read_text()
    assert "svg.clientWidth" in js
