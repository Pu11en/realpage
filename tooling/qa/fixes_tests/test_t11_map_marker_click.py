"""T11: map markers actually open their state's table when clicked, not just a popup.

A click landing in the gap between the amber dot and its white label pill used to
fall through to the state shape underneath (which only shows a hover tooltip, no
navigation) because the marker's <g> had no geometry of its own there. Guard against
that regressing by requiring an invisible hit-area rect sized to cover both the dot
and the label, and prove clicking it navigates using a real browser."""
import asyncio
import os
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
MAP_JS = (ROOT / "site/js/map.js").read_text(encoding="utf-8")


def test_hit_area_element_present():
    assert '"hit-area"' in MAP_JS


def test_hit_area_sized_to_cover_dot_and_label():
    assert "hit.setAttribute" in MAP_JS
    assert "Math.min(pillX, -dot)" in MAP_JS
    assert "Math.max(pillX + pillW, dot)" in MAP_JS


def test_click_between_dot_and_label_navigates():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("playwright not installed")

    port = int(os.environ.get("T11_PORT", "8797"))
    proc = subprocess.Popen(
        ["python3", "-m", "http.server", str(port), "-d", str(ROOT / "site")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        base = f"http://localhost:{port}"
        for _ in range(40):
            try:
                urllib.request.urlopen(f"{base}/map.html", timeout=1)
                break
            except Exception:
                time.sleep(0.25)
        else:
            pytest.fail("dev server for map.html never came up")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"{base}/map.html")
            page.wait_for_selector(".lead-marker")
            marker = page.query_selector(".lead-marker")
            marker.click()
            page.wait_for_timeout(300)
            assert "index.html?area=" in page.url
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=5)
