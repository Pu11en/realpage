"""F1: lead lines with no phone/link end with a one-tap 🔍 Find contact link.

Offline: checks the SOUL rule and that linkfix keeps #ask: links while still
stripping fake web links.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "chatbot"))

from linkfix import LineFixer, _norm, finalize_answer, fix_links  # noqa: E402

SOUL = open(os.path.join(ROOT, "chatbot", "hermes-profile", "SOUL.md"), encoding="utf-8").read()

NEWS = "https://communityimpact.com/richardson/housing-real-estate/sherman-street/"
FAKE = "https://example.com/made-up"
SEEN = {_norm(NEWS)}
ASK = "[🔍 Find contact](#ask:Deep dive on The Sherman, Richardson)"


def test_soul_uses_find_contact_link():
    assert "[🔍 Find contact](#ask:Deep dive on <name>, <city>)" in SOUL
    assert "ask me for a deep dive" not in SOUL


def test_soul_one_web_search_for_top_lead_only():
    i = SOUL.index("Find contact")
    rule = SOUL[i:i + 600]
    assert "#1" in rule and "office_phone" in rule and "ps_web_search" in rule
    assert "only for #1" in rule
    assert "names that building" in rule


def test_linkfix_keeps_ask_link():
    line = f"1. **The Sherman**, Richardson -- **300 units**, opening 2027 · {ASK}"
    assert fix_links(line, SEEN) == line
    assert finalize_answer(line, SEEN) == line


def test_linkfix_still_strips_fake_link_next_to_ask():
    line = f"2. **Oak Row**, Plano -- **200 units**, sold 2026 · [Website]({FAKE}) · {ASK}"
    out = fix_links(line, SEEN)
    assert FAKE not in out
    assert ASK in out


def test_linefixer_stream_keeps_ask_link():
    lf = LineFixer(seen=SEEN)
    line = f"3. **Elm Park**, Frisco -- **150 units** · [News]({NEWS}) · {ASK}"
    out = lf.feed(line[:40]) + lf.feed(line[40:] + "\n") + lf.flush()
    assert ASK in out and NEWS in out


def test_loader_makes_ask_links_clickable():
    """F2: loader.js (runs inside Open WebUI) turns #ask: links into a one-tap send."""
    js = open(os.path.join(ROOT, "chatbot", "branding", "loader.js"), encoding="utf-8").read()
    assert 'a[href^="#ask:"]' in js
    assert "input:prompt:submit" in js
    assert "preventDefault" in js
    assert "decodeURIComponent" in js
