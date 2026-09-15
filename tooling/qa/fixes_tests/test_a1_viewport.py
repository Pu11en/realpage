"""A1: every site page has the phone viewport tag, and the phone QA runs act like a real phone."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TAG = re.compile(r'<meta\s+name="viewport"\s+content="width=device-width,\s*initial-scale=1"', re.I)


def test_every_page_has_viewport_tag():
    pages = sorted((ROOT / "site").glob("*.html"))
    assert pages
    missing = [p.name for p in pages if not TAG.search(p.read_text(encoding="utf-8"))]
    assert not missing, f"no viewport tag: {missing}"


def test_phone_runs_use_mobile_emulation():
    for name in ("sweep.py", "quick-check.py"):
        src = (ROOT / "tooling/qa" / name).read_text(encoding="utf-8")
        assert "is_mobile=" in src and "has_touch=" in src, name
