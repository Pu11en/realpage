"""G1-T3: contact buttons send now or wait for a signed-in chat."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PANEL = (ROOT / "site/js/chat-panel.js").read_text(encoding="utf-8")
INDEX = (ROOT / "site/index.html").read_text(encoding="utf-8")
PROPERTY = (ROOT / "site/property.html").read_text(encoding="utf-8")


def test_every_building_surface_uses_get_contact_label():
    assert INDEX.count("Get contact &rarr;") == 1
    assert PROPERTY.count("Get contact &rarr;") == 2
    assert "✦ Deep dive" not in INDEX
    assert "✦ Deep dive in chat" not in PROPERTY


def test_contact_button_stays_with_the_building_name():
    row = INDEX.split('<td class="lead-prop">', 1)[1].split("</td>", 1)[0]
    assert row.index("<strong>${l.property}</strong>") < row.index("data-deep-dive")
    assert row.index("data-deep-dive") < row.index("${contactHtml(l.contact)}")

    for heading in ('<h1>${esc(p.community)}</h1>', '<h1>${esc(name)}</h1>'):
        detail = PROPERTY.split(heading, 1)[1]
        assert detail.index("data-deep-dive") < detail.index('<div class="meta">')


def test_contact_question_is_submitted_automatically():
    assert 'type: "input:prompt:submit"' in PANEL
    assert "submit=true" in PANEL
    assert "submit=false" not in PANEL


def test_signed_out_question_waits_and_sends_after_auth():
    assert "function queueQuestion(panel, text, id)" in PANEL
    assert "panel.dataset.pendingQuestion = text" in PANEL
    assert 'panel.dataset.canAsk = res.ok ? "1" : "0"' in PANEL
    assert "if (res.ok) sendPendingQuestion(panel)" in PANEL
    assert "setFrameSource(panel, CHAT_APP_URL)" in PANEL


def test_generic_send_path_is_ready_for_lead_search():
    assert "function ask(text)" in PANEL
    assert "isOpen, ask, deepDive, deepDivePrompt" in PANEL
