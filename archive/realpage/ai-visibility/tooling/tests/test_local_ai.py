"""Offline tests for the Gemini models in local_ai.py: never touch the network or a real key."""

import io
import json
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
FIXTURES = HERE / "fixtures"
sys.path.insert(0, str(HERE))
import local_ai  # noqa: E402


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setattr(local_ai, "GEMINI_GAP", 0.0)
    monkeypatch.setattr(local_ai, "_gemini_stopped", "")
    monkeypatch.setattr(local_ai, "_gemini_key", lambda: pytest.fail("tests must not read the key"))
    monkeypatch.setenv("AI_VIS_SOURCES", str(tmp_path / "gemini-sources.jsonl"))
    sent = []

    def fake_post(body):
        sent.append(body)
        return offline.reply(body)
    offline.reply = lambda body: fixture("gemini-memory.json")
    monkeypatch.setattr(local_ai, "_gemini_post", fake_post)
    offline.sent = sent
    offline.sources = tmp_path / "gemini-sources.jsonl"
    return offline


def test_memory_answer_has_no_tools_and_public_prompt(offline):
    text = local_ai.ask("gemini", "Best apartment software?")
    assert "Yardi" in text
    body = offline.sent[0]
    assert "tools" not in body
    assert "member of the public" in body["systemInstruction"]["parts"][0]["text"]
    assert not offline.sources.exists()


def test_web_answer_turns_on_search_and_saves_sources(offline):
    offline.reply = lambda body: fixture("gemini-web.json")
    text = local_ai.ask("gemini-web", "Best revenue management software?")
    assert "antitrust" in text
    assert offline.sent[0]["tools"] == [{"google_search": {}}]
    line = json.loads(offline.sources.read_text().splitlines()[0])
    assert line["prompt"] == "Best revenue management software?"
    assert [s["title"] for s in line["sources"]] == ["justice.gov", "realpage.com"]
    assert line["sources"][0]["url"].startswith("https://")


def test_throttle_spaces_calls(offline, monkeypatch):
    monkeypatch.setattr(local_ai, "GEMINI_GAP", 0.3)
    monkeypatch.setattr(local_ai, "_gemini_last", 0.0)
    import time
    start = time.monotonic()
    local_ai.ask("gemini", "a")
    local_ai.ask("gemini", "b")
    assert time.monotonic() - start >= 0.3


def test_429_stops_all_later_gemini_calls(offline):
    def limited(body):
        raise urllib.error.HTTPError(local_ai.GEMINI_URL, 429, "Too Many Requests", {}, io.BytesIO(b""))
    offline.reply = limited
    with pytest.raises(local_ai.RateLimited):
        local_ai.ask("gemini", "a")
    offline.reply = lambda body: fixture("gemini-memory.json")
    with pytest.raises(local_ai.RateLimited):
        local_ai.ask("gemini-web", "b")
    assert len(offline.sent) == 1  # the second call never went out


def test_empty_answer_is_an_error(offline):
    offline.reply = lambda body: {"candidates": [{"content": {"parts": []}}]}
    with pytest.raises(RuntimeError):
        local_ai.ask("gemini", "a")


@pytest.fixture
def server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), local_ai.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def post(url, body):
    req = urllib.request.Request(url + "/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"content-type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def test_model_list_includes_gemini(server):
    with urllib.request.urlopen(server + "/v1/models") as resp:
        ids = [m["id"] for m in json.loads(resp.read())["data"]]
    assert "gemini" in ids and "gemini-web" in ids


def test_structured_tool_call_through_gemini(offline, server):
    offline.reply = lambda body: fixture("gemini-json.json")
    tool = {"type": "function", "function": {"name": "emit", "parameters": {"type": "object"}}}
    code, data = post(server, {"model": "gemini", "messages": [{"role": "user", "content": "Make prompts"}],
                               "tools": [tool]})
    assert code == 200
    call = data["choices"][0]["message"]["tool_calls"][0]["function"]
    assert call["name"] == "emit"
    assert json.loads(call["arguments"])["prompts"]
    assert offline.sent[0]["generationConfig"]["responseMimeType"] == "application/json"


def test_rate_limit_reaches_niubigeo_as_429(offline, server):
    def limited(body):
        raise urllib.error.HTTPError(local_ai.GEMINI_URL, 429, "Too Many Requests", {}, io.BytesIO(b""))
    offline.reply = limited
    code, data = post(server, {"model": "gemini", "messages": [{"role": "user", "content": "hi"}]})
    assert code == 429 and "rate limit" in data["error"]["message"]
