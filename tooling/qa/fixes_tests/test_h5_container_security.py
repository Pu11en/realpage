"""Offline guard for H5's least-privilege container policy.

This deliberately reads Dockerfiles rather than invoking Docker, so the normal
release check stays offline and catches a later accidental return to root.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _last_user(dockerfile: Path) -> str:
    users = [
        line.split(maxsplit=1)[1].strip()
        for line in dockerfile.read_text(encoding="utf-8").splitlines()
        if line.strip().lower().startswith("user ")
    ]
    assert users, f"{dockerfile} must select a runtime user"
    return users[-1]


def test_chatbot_runs_as_its_dedicated_unprivileged_user():
    dockerfile = ROOT / "chatbot" / "Dockerfile"
    text = dockerfile.read_text(encoding="utf-8")

    assert _last_user(dockerfile) == "hermes"
    assert "chown -R hermes:hermes /app /opt/hermes-profile /opt/hermes-start /opt/chatbot" in text
    assert "chmod -R a-w /opt/propertystack" in text


def test_site_runs_as_caddy_with_only_its_runtime_state_writable():
    dockerfile = ROOT / "site" / "Dockerfile"
    text = dockerfile.read_text(encoding="utf-8")

    assert _last_user(dockerfile) == "caddy"
    assert "chown -R caddy:caddy /config /data" in text
    assert "COPY . /srv" in text
    assert ":{$PORT:8080}" in (ROOT / "site" / "Caddyfile").read_text(encoding="utf-8")
