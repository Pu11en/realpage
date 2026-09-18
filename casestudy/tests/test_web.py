"""C10: browser workbench and byte-identical export actions."""
from __future__ import annotations

import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

from casestudy.pipeline import run_batch, submission_jsonl
from casestudy.web import WEB_ROOT, run_payload
from casestudy.writer import WriterConfig

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "casestudy" / "data"
SAMPLES = (DATA / "sample.jsonl").read_text(encoding="utf-8").splitlines()
PRACTICE = (DATA / "practice.jsonl").read_text(encoding="utf-8").splitlines()
NO_CONSENT = PRACTICE[1]
VOICE_ONLY = PRACTICE[-1]
OFFLINE = WriterConfig(enabled=False)


def _twelve() -> str:
    rows = []
    for index in range(12):
        row = json.loads(SAMPLES[index % 2])
        row["task_id"] += f"_browser_{index}"
        rows.append(json.dumps(row))
    return "\n".join(rows) + "\n"


def test_web_payload_uses_the_cli_serializer_exactly():
    text = "\n".join(SAMPLES) + "\n"
    payload = run_payload(text, offline=True)
    expected = submission_jsonl(run_batch(text.splitlines(), config=OFFLINE))
    assert payload["submission_jsonl"] == expected
    assert payload["submission_jsonl"] == "".join(row["submission_line"] + "\n" for row in payload["records"])
    assert payload["mode"] == "offline" and payload["record_count"] == 2
    for row in payload["records"]:
        assert set(json.loads(row["submission_line"])) == {"next_message", "next_action"}


def test_web_payload_preserves_malformed_middle_record():
    payload = run_payload(SAMPLES[0] + "\n{not json\n" + SAMPLES[1], offline=True)
    assert payload["record_count"] == 3
    assert payload["records"][1]["diagnostics"]["malformed"] is True
    assert payload["records"][1]["diagnostics"]["errors"][0].startswith("malformed_json")
    assert json.loads(payload["records"][1]["submission_line"])["next_action"]["type"] == "escalate"


def test_page_has_complete_interaction_and_accessibility_states():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    css = (WEB_ROOT / "styles.css").read_text(encoding="utf-8")
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
    for marker in (
        "jsonl-input", "file-input", "copy-one", "copy-all", "download-all", "check-list",
        "record-errors", "human-decision-badge", "human-channel", "human-send-at",
        "human-next-action", "human-body", "no-message",
    ):
        assert f'id="{marker}"' in html
    assert "Skip to workbench" in html and "noindex,nofollow" in html
    assert "Human review" in html and "View exact submission and checks" in html
    assert 'id="offline" type="checkbox"> Force template fallback' in html
    assert "AI writer ready" in html
    assert ":focus-visible" in css and ":hover" in css and ":active" in css and ".loading" in css and ".empty-state" in css
    assert "submission_line + \"\\n\"" in script
    assert "payload.submission_jsonl" in script
    assert "No live AI model was used for this result" in script
    assert "window.alert" not in script


def test_under_the_hood_distinguishes_evidence_assumptions_and_limits():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    assert 'id="under-the-hood"' in html
    for claim in (
        "2 of 2", "24 synthetic replies", "live AI reply time", "How the AI answered",
        "Project assumptions", "conservative project defaults, not claims about Texas law",
        "Code decides. The model may only write.", "Still unhandled or unproven",
        "Only a few live AI runs so far; broader latency, quality, and availability are not measured",
    ):
        assert claim in html
    assert "hidden test or production evidence" in html


def test_under_the_hood_links_primary_sources_and_existing_tools():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    links = (
        "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-64/subpart-L/section-64.1200",
        "https://www.anthropic.com/engineering/building-effective-agents",
        "https://arxiv.org/abs/2507.11538",
        "https://github.com/Pu11en/shipcheck",
        "https://github.com/Pu11en/ebi-agent-chat-relay",
    )
    assert "https://uscode.house.gov/view.xhtml?edition=prelim&amp;" in html
    for link in links:
        assert f'href="{link}"' in html
    assert html.count('target="_blank" rel="noopener"') >= len(links) + 1


@pytest.fixture(scope="module")
def web_server():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    proc = subprocess.Popen(
        [sys.executable, "-m", "casestudy.web", "--port", str(port)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url + "/case-study", timeout=0.5) as response:
                if response.status == 200:
                    break
        except Exception:
            time.sleep(0.05)
    else:
        proc.terminate()
        raise RuntimeError("case-study web server did not start")
    yield url
    proc.terminate()
    proc.wait(timeout=5)


def test_browser_runs_1_2_12_malformed_upload_and_exact_exports(web_server, tmp_path):
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch()
        context = browser.new_context(accept_downloads=True)
        context.grant_permissions(["clipboard-read", "clipboard-write"], origin=web_server)
        page = context.new_page()
        page.goto(web_server + "/case-study")
        assert page.title() == "CraneSignal | Case study workbench"
        assert not page.locator("#offline").is_checked()
        assert page.locator("#mode-label").inner_text() == "AI writer ready"

        def run(text: str, count: int):
            page.locator("#jsonl-input").fill(text)
            page.locator("#run-button").click()
            page.locator(f"#record-count:text-is('{count}')").wait_for()
            page.locator("#run-button:not([disabled])").wait_for()
            assert page.locator(".record-tab").count() == count

        with page.expect_request("**/case-study/api/run") as request_info:
            run(SAMPLES[0], 1)
        assert request_info.value.post_data_json["offline"] is False
        assert page.locator("#mode-label").inner_text() == "AI writer result"

        page.locator("#offline").check()
        assert page.locator("#mode-label").inner_text() == "Template fallback ready"
        run(SAMPLES[0], 1)
        public = json.loads(page.locator("#submission-output").text_content())
        assert set(public) == {"next_message", "next_action"}
        assert page.locator("#human-decision-badge").inner_text() == "Send text"
        assert page.locator("#human-channel").inner_text() == "Text message"
        assert "Dec 9, 2025 at 9:00 AM" in page.locator("#human-send-at").inner_text()
        assert "Hi Taylor" in page.locator("#human-body").inner_text()
        assert "Start prospect welcome short horizon" in page.locator("#human-next-action").inner_text()
        assert page.locator("#human-subject-row").is_hidden()
        assert "No live AI model" in page.locator("#human-engine-note").inner_text()
        page.locator(".submission-details > summary").click()
        assert page.locator("#diagnostic-summary").get_by_text("template", exact=True).is_visible()
        assert page.locator(".check-row").count() == 11

        run(SAMPLES[1], 1)
        assert page.locator("#human-decision-badge").inner_text() == "Send email"
        assert page.locator("#human-channel").inner_text() == "Email"
        assert page.locator("#human-subject-row").is_visible()
        assert "Tour Oak Ridge" in page.locator("#human-subject").inner_text()
        assert "oakridge.example/tour" in page.locator("#human-cta").inner_text()

        run(NO_CONSENT, 1)
        assert page.locator("#human-decision-badge").inner_text() == "Do not send"
        assert page.locator("#message-preview").is_hidden()
        assert page.locator("#no-message").is_visible()
        assert "Do not contact" in page.locator("#human-next-action").inner_text()

        run(VOICE_ONLY, 1)
        assert page.locator("#human-decision-badge").inner_text() == "Human call"
        assert page.locator("#human-channel").inner_text() == "Human phone call"
        assert "Create a human call task" in page.locator("#human-next-action").inner_text()

        run("{not json", 1)
        assert page.locator("#human-decision-badge").inner_text() == "Human review"
        assert "A human needs to review" in page.locator("#no-message-title").inner_text()

        upload = tmp_path / "two.jsonl"
        upload.write_text("\n".join(SAMPLES) + "\n", encoding="utf-8")
        page.locator("#file-input").set_input_files(upload)
        playwright.expect(page.locator("#jsonl-input")).to_have_value(upload.read_text(encoding="utf-8"))
        assert page.locator("#jsonl-input").input_value().splitlines() == SAMPLES
        page.locator("#run-button").click()
        page.locator("#record-count:text-is('2')").wait_for()
        assert page.locator(".record-tab").count() == 2

        run(_twelve(), 12)
        expected = page.evaluate("window.caseStudyDemo.allBytes()")
        assert len(expected.splitlines()) == 12
        page.locator("#copy-all").click()
        assert page.evaluate("navigator.clipboard.readText()") == expected
        with page.expect_download() as download_info:
            page.locator("#download-all").click()
        assert Path(download_info.value.path()).read_text(encoding="utf-8") == expected
        page.locator(".record-tab").nth(7).click()
        expected_one = page.evaluate("window.caseStudyDemo.oneBytes()")
        page.locator("#copy-one").click()
        assert page.evaluate("navigator.clipboard.readText()") == expected_one
        assert len(expected_one.splitlines()) == 1

        run(SAMPLES[0] + "\n{not json\n" + SAMPLES[1], 3)
        page.locator(".record-tab").nth(1).click()
        assert page.locator("#record-errors").is_visible()
        assert "malformed_json" in page.locator("#record-errors").inner_text()
        assert json.loads(page.locator("#submission-output").text_content())["next_action"]["type"] == "escalate"
        browser.close()


def test_payload_carries_answer_key_for_display_only():
    from casestudy.web import run_payload
    text = (Path(__file__).resolve().parents[1] / "data" / "sample.jsonl").read_text(encoding="utf-8")
    payload = run_payload(text.rstrip("\n") + "\nnot json\n", offline=True)
    keys = [r["answer_key"] for r in payload["records"]]
    assert keys[0]["next_action"]["name"] == "prospect_welcome_short_horizon"
    assert keys[1]["next_message"]["channel"] == "email"
    assert keys[2] is None
    for r in payload["records"]:
        assert "expected" not in r["submission_line"]


def test_recent_runs_need_the_review_token(monkeypatch):
    import asyncio
    from aiohttp.test_utils import TestClient, TestServer
    from casestudy import web as w
    monkeypatch.setenv("CASESTUDY_REVIEW_TOKEN", "secret-token")
    w.RECENT_RUNS.clear()

    async def go():
        async with TestClient(TestServer(w.create_app())) as client:
            text = (Path(__file__).resolve().parents[1] / "data" / "sample.jsonl").read_text(encoding="utf-8")
            assert (await client.post("/case-study/api/run", json={"jsonl": text, "offline": True})).status == 200
            assert (await client.get("/case-study/api/recent")).status == 404
            assert (await client.get("/case-study/api/recent", headers={"X-Review-Token": "wrong"})).status == 404
            ok = await client.get("/case-study/api/recent", headers={"X-Review-Token": "secret-token"})
            body = await ok.json()
            assert body["runs"][0]["input_jsonl"] == text and body["runs"][0]["result"]["record_count"] == 2
    asyncio.run(go())
