"""The outreach sample packs.

A pack is sent to a named person at a company we want as a customer, so a wrong row costs
more than a wrong row on a web page: it is the first and possibly only thing that reader
sees. These tests pin the claims the pack makes about itself.

Offline: reads files on disk and runs the generator, no network, no paid calls.
"""
import importlib.util
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
GEN = ROOT / "tooling" / "outreach" / "build_pack.py"
PACKS = ROOT / "docs" / "outreach" / "packs"


def load():
    spec = importlib.util.spec_from_file_location("outreach_pack", GEN)
    module = importlib.util.module_from_spec(spec)
    sys.modules["outreach_pack"] = module
    spec.loader.exec_module(module)
    return module


pack = load()


def built_packs() -> list[Path]:
    return sorted(PACKS.glob("*.html")) if PACKS.exists() else []


def text_of(path: Path) -> str:
    html = re.sub(r"<(script|style)\b.*?</\1>", " ", path.read_text(encoding="utf-8"), flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


# ---------------------------------------------------------------- the selection rules


def test_every_profile_states_who_it_is_for_and_why():
    """A pack whose rule cannot be explained is a list the reader cannot argue with, which
    is worse than one they can push back on."""
    for key, profile in pack.PROFILES.items():
        for field in ("audience", "headline", "why", "rule", "date_label"):
            assert profile.get(field), f"{key} has no {field}"
        assert callable(profile["pick"]), key


def test_opening_soon_picks_only_buildings_that_have_not_opened():
    """The whole pitch is that these buildings have not chosen their vendors yet. A building
    that already opened breaks it."""
    today = date(2026, 9, 25)
    profile = pack.PROFILES["opening-soon"]
    assert profile["pick"]({"openingDate": "2027-06-01", "units": 200}, today)
    assert not profile["pick"]({"openingDate": "2026-01-01", "units": 200}, today), "already open"
    assert not profile["pick"]({"openingDate": "2029-06-01", "units": 200}, today), "too far out"
    assert not profile["pick"]({"openingDate": "2027-06-01", "units": 40}, today), "too small"
    assert not profile["pick"]({"openingDate": None, "units": 200}, today), "no date"


def test_just_sold_picks_only_recent_sales():
    today = date(2026, 9, 25)
    profile = pack.PROFILES["just-sold"]
    assert profile["pick"]({"saleDate": "2026-06-01", "units": 200}, today)
    assert not profile["pick"]({"saleDate": "2024-01-01", "units": 200}, today), "too old"
    assert not profile["pick"]({"saleDate": "2027-01-01", "units": 200}, today), "in the future"


def test_months_ahead_handles_a_missing_or_broken_date():
    today = date(2026, 9, 25)
    assert pack.months_ahead(None, today) is None
    assert pack.months_ahead("", today) is None
    assert pack.months_ahead("not-a-date", today) is None
    assert pack.months_ahead("2027-09-01", today) == 12


# ---------------------------------------------------------------- the generated pack


def test_the_generator_runs_and_writes_a_pack(tmp_path):
    done = subprocess.run(
        [sys.executable, str(GEN), "--profile", "opening-soon", "--limit", "5"],
        capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stderr
    assert "wrote" in done.stdout


@pytest.mark.parametrize("path", built_packs(), ids=lambda p: p.name)
def test_every_row_links_its_public_record(path):
    """The pack's central claim is that any line can be checked in thirty seconds. A row
    with no source link is a claim the reader cannot verify."""
    html = path.read_text(encoding="utf-8")
    body = html.split("<tbody>", 1)[1].split("</tbody>", 1)[0]
    rows = re.findall(r"<tr>.*?</tr>", body, re.S)
    assert rows, f"{path.name} has no rows"
    unlinked = [row for row in rows if '<a href="http' not in row]
    assert not unlinked, f"{path.name}: {len(unlinked)} of {len(rows)} rows have no source"


@pytest.mark.parametrize("path", built_packs(), ids=lambda p: p.name)
def test_pack_states_its_rule_its_dates_and_the_pool_it_came_from(path):
    text = text_of(path)
    assert "buildings that match" in text, "does not say what the rule was"
    assert "Prepared on" in text and "Data as of" in text, "undated"
    assert "Why these." in text, "does not explain the selection"
    # Saying "15 of 17" rather than just "15" is the difference between a sample and a claim
    # that this is everything.
    assert re.search(r"\d+ of \d+ buildings", text), "does not say it is a sample"


@pytest.mark.parametrize("path", built_packs(), ids=lambda p: p.name)
def test_pack_is_honest_about_blanks_and_estimates(path):
    text = text_of(path)
    assert "not that the value is zero" in text
    assert "Nothing here is estimated" in text


@pytest.mark.parametrize("path", built_packs(), ids=lambda p: p.name)
def test_pack_is_noindex_and_needs_no_javascript(path):
    """A pack is for one reader, not for Google, and it has to survive being printed to PDF
    and forwarded."""
    html = path.read_text(encoding="utf-8")
    assert 'name="robots" content="noindex"' in html
    assert "<script" not in html


@pytest.mark.parametrize("path", built_packs(), ids=lambda p: p.name)
def test_pack_sends_the_reader_somewhere_real(path):
    html = path.read_text(encoding="utf-8")
    assert "https://app.cranesignal.com/index.html" in html
    assert "free and with no account" in text_of(path)


@pytest.mark.parametrize("path", built_packs(), ids=lambda p: p.name)
def test_no_realpage_text(path):
    assert "RealPage" not in path.read_text(encoding="utf-8"), path.name
