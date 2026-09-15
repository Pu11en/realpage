"""T7: an answer never ends with a broken "Sources: )" (or "Sources: ()")
line once its bad/unseen citations are stripped out."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "chatbot"))

from linkfix import _norm, fix_links  # noqa: E402


def test_dangling_parens_on_sources_line_are_dropped():
    # Reproduces the live bug: "Which buildings sold recently?" ended with
    # a bare "Sources: )" once its one citation got stripped as unseen.
    text = "Which buildings sold recently?\nSources: [Bad record](http://not-a-real-source.example)"
    out = fix_links(text, seen=set())
    assert "Sources:" not in out
    assert ")" not in out


def test_empty_parens_sources_line_dropped():
    text = "Which buildings sold recently?\nSources: ()"
    out = fix_links(text, seen=set())
    assert "Sources:" not in out


def test_sources_line_with_real_citation_survives():
    url = "https://www.tdlr.texas.gov/TABS/Search/Print/TABS2025020938"
    text = f"Which buildings sold recently?\nSources: [Texas building record]({url})"
    out = fix_links(text, seen={_norm(url)})
    assert "Sources:" in out
    assert url in out
