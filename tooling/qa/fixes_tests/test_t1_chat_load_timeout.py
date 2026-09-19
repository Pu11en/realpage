"""T1: the chat panel waits well past 8s for a sleepy chat app, shows a "waking up" message, and
retries the frame once automatically before showing the manual error/retry button."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JS = (ROOT / "site/js/chat-panel.js").read_text(encoding="utf-8")


def test_default_timeout_is_well_past_8s():
    m = re.search(r"loadTimeoutMs = window\.PS_CHAT_LOAD_TIMEOUT_MS \|\| (\d+)", JS)
    assert m, "could not find loadTimeoutMs default"
    assert int(m.group(1)) >= 20000


def test_waking_up_message_shown_while_loading():
    assert "Waking up the chat" in JS


def test_one_automatic_retry_before_showing_error():
    fn = JS.split("const startLoadTimer = () => {", 1)[1].split("panel.querySelector(\"#chat-panel-retry\")", 1)[0]
    assert "autoRetried" in fn
    assert "setFrameSource(panel, CHAT_APP_URL)" in fn
    assert 'errorEl.style.display = "flex"' in fn
