"""H6: the human preview must be a separate, fresh, sign-in-enabled lane.

These checks inspect only tracked files.  They never start Docker, call a
model, consume a key, or modify a local account.
"""
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "tooling" / "human-test.sh"
OVERLAY = ROOT / "chatbot" / "docker-compose.human-test.yml"


def test_human_preview_offline_safeguards_pass():
    result = subprocess.run(
        ["bash", str(SCRIPT), "check"], cwd=ROOT, text=True, capture_output=True
    )
    assert result.returncode == 0, result.stderr
    assert "isolated" in result.stdout


def test_human_preview_does_not_share_everyday_local_state():
    script = SCRIPT.read_text()
    overlay = OVERLAY.read_text()

    assert 'PROJECT="cranesignal-human-test"' in script
    assert 'down --volumes --remove-orphans' in script
    assert 'for port in 8765 8876' in script
    assert 'APP_URL=http://localhost:8876' in script
    assert 'LANDING_DIR="$MAIN_ROOT/business/marketing/landing"' in script
    assert "cranesignal-human-test-open-webui" in overlay
    assert "cranesignal-human-test-hermes-home" in overlay
    assert "-p ps-chat" not in script


def test_human_preview_has_a_real_sign_in_front_door():
    overlay = OVERLAY.read_text()

    assert 'WEBUI_AUTH: "True"' in overlay
    assert 'ENABLE_SIGNUP: "true"' in overlay
    assert 'ENABLE_LOGIN_FORM: "true"' in overlay
    assert 'CHAT_UPSTREAM: http://open-webui:8080' in overlay
    assert '"8876:8080"' in overlay
    assert overlay.count("ports: !reset []") == 2
