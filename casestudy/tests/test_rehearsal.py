"""C13 recovery rehearsal coverage."""
from __future__ import annotations

import socket
import subprocess
import sys
import time
import urllib.request

import pytest

from casestudy.rehearsal import run_rehearsal


@pytest.fixture()
def rehearsal_server():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    proc = subprocess.Popen(
        [sys.executable, "-m", "casestudy.web", "--port", str(port)],
        env={"PATH": "/usr/bin:/bin", "PYTHONPATH": "."},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url + "/health", timeout=0.5):
                break
        except Exception:
            time.sleep(0.05)
    else:
        proc.terminate()
        raise RuntimeError("rehearsal server did not start")
    yield url
    proc.terminate()
    proc.wait(timeout=5)


def test_full_http_rehearsal_exports_parse_and_contains_bad_middle_row(rehearsal_server, tmp_path):
    results = run_rehearsal(rehearsal_server, tmp_path)
    assert [(item["name"], item["records"]) for item in results] == [
        ("goldens-configured", 2),
        ("practice12-configured", 12),
        ("goldens-offline", 2),
        ("practice12-offline", 12),
        ("malformed-middle-offline", 3),
    ]
    assert len(list(tmp_path.glob("*.jsonl"))) == 5
    assert len(list(tmp_path.glob("*.diagnostics.json"))) == 5
