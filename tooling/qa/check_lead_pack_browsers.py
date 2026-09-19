#!/usr/bin/env python3
"""Build C T4: verify Lead Pack downloads across desktop and phone browsers.

Serves ``site/`` locally, treats the visitor as signed in through the same
auth-off response used by local development, and checks Dallas–Fort Worth in:

- desktop Chromium, Firefox, and WebKit
- iPhone 13 (WebKit) and Pixel 7 (Chromium) device emulation

Every downloaded PDF must contain one source link per Dallas lead and report
the same row count in its PDF metadata. The first PDF and one screenshot per
profile are saved under ``docs/plans`` for human review.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.async_api import BrowserType, Page, async_playwright
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
DEFAULT_ARTIFACT_DIR = ROOT / "docs" / "plans"
PORT = int(os.environ.get("CHECK_LEAD_PACK_PORT", "8794"))
BASE = f"http://localhost:{PORT}"
REGION = "Dallas–Fort Worth"


@dataclass(frozen=True)
class Profile:
    name: str
    browser_name: str
    context_options: dict[str, Any]


def wait_until_serving() -> bool:
    for _ in range(60):
        try:
            with urllib.request.urlopen(f"{BASE}/index.html", timeout=2) as response:
                if response.status == 200 and b"Early Leads" in response.read():
                    return True
        except Exception:
            pass
        time.sleep(0.25)
    return False


def dallas_lead_count() -> int:
    data = json.loads((SITE / "data" / "areas" / "tx.json").read_text(encoding="utf-8"))
    return sum(lead.get("metro") == REGION for lead in data["leads"])


def source_link_count(reader: PdfReader) -> int:
    count = 0
    for page in reader.pages:
        for annotation_ref in page.get("/Annots", []):
            annotation = annotation_ref.get_object()
            uri = annotation.get("/A", {}).get("/URI", "")
            if uri and uri != "https://app.cranesignal.com":
                count += 1
    return count


def validate_pdf(path: Path, expected_rows: int) -> tuple[int, int]:
    if path.read_bytes()[:5] != b"%PDF-":
        raise AssertionError(f"{path.name} is not a PDF")

    reader = PdfReader(path)
    expected_subject = f"{expected_rows} apartment leads for {REGION}"
    if reader.metadata.subject != expected_subject:
        raise AssertionError(
            f"{path.name} reports {reader.metadata.subject!r}; expected {expected_subject!r}"
        )

    links = source_link_count(reader)
    if links != expected_rows:
        raise AssertionError(f"{path.name} has {links} lead source links; expected {expected_rows}")

    first_page_text = reader.pages[0].extract_text() or ""
    if "CraneSignal Lead Pack: Dallas" not in first_page_text:
        raise AssertionError(f"{path.name} does not have the Dallas Lead Pack title")
    return len(reader.pages), links


async def allow_local_auth(page: Page) -> None:
    async def fulfill_auth(route) -> None:
        await route.fulfill(
            status=200,
            content_type="application/json",
            headers={
                "Access-Control-Allow-Origin": BASE,
                "Access-Control-Allow-Credentials": "true",
            },
            body=json.dumps({"features": {"auth": False}}),
        )

    await page.route("http://localhost:3000/api/config", fulfill_auth)


async def check_profile(
    browser_type: BrowserType,
    profile: Profile,
    expected_rows: int,
    artifact_dir: Path,
    download_dir: Path,
    save_sample: bool,
) -> tuple[int, int]:
    browser = await browser_type.launch()
    try:
        context = await browser.new_context(accept_downloads=True, **profile.context_options)
        page = await context.new_page()
        errors: list[str] = []

        def record_console_error(message) -> None:
            # WebKit reports this harmless, engine-level viewport warning as a
            # console error even though it ignores the key and renders normally.
            if message.type != "error" or "interactive-widget" in message.text:
                return
            errors.append(f"console error: {message.text}")

        page.on("pageerror", lambda error: errors.append(f"page error: {error}"))
        page.on("console", record_console_error)
        await allow_local_auth(page)

        response = await page.goto(f"{BASE}/index.html?area=tx", wait_until="networkidle")
        if response is None or response.status >= 400:
            raise AssertionError(f"Early Leads failed to load ({response.status if response else 'no response'})")

        metro = page.locator(f'.metro-btn[data-metro="{REGION}"]')
        await metro.wait_for(state="visible")
        await metro.click()
        chat_close = page.locator("#chat-panel-close")
        if await chat_close.is_visible():
            await chat_close.click()
        await page.locator("#download-lead-pack").scroll_into_view_if_needed()

        async with page.expect_download(timeout=120_000) as download_info:
            await page.locator("#download-lead-pack").click()
        download = await download_info.value
        pdf_path = download_dir / f"{profile.name}.pdf"
        await download.save_as(pdf_path)

        await page.locator("#lead-pack-status").get_by_text(
            f"{expected_rows} leads downloaded."
        ).wait_for(timeout=120_000)
        pages, links = validate_pdf(pdf_path, expected_rows)

        screenshot_dir = artifact_dir / "lead-pack-screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=screenshot_dir / f"{profile.name}.png")
        if save_sample:
            (artifact_dir / "sample-lead-pack.pdf").write_bytes(pdf_path.read_bytes())

        if errors:
            raise AssertionError("; ".join(errors))
        await context.close()
        return pages, links
    finally:
        await browser.close()


async def run_checks(artifact_dir: Path) -> list[str]:
    expected_rows = dallas_lead_count()
    if expected_rows <= 0:
        raise AssertionError("Dallas–Fort Worth has no leads to test")

    results: list[str] = []
    async with async_playwright() as playwright:
        iphone = dict(playwright.devices["iPhone 13"])
        iphone.pop("default_browser_type", None)
        pixel = dict(playwright.devices["Pixel 7"])
        pixel.pop("default_browser_type", None)
        profiles = [
            Profile("desktop-chromium", "chromium", {"viewport": {"width": 1440, "height": 900}}),
            Profile("desktop-firefox", "firefox", {"viewport": {"width": 1440, "height": 900}}),
            Profile("desktop-webkit", "webkit", {"viewport": {"width": 1440, "height": 900}}),
            Profile("iphone-13", "webkit", iphone),
            Profile("pixel-7", "chromium", pixel),
        ]

        with tempfile.TemporaryDirectory(prefix="cranesignal-lead-pack-") as temp_dir:
            for index, profile in enumerate(profiles):
                browser_type = getattr(playwright, profile.browser_name)
                pages, links = await check_profile(
                    browser_type,
                    profile,
                    expected_rows,
                    artifact_dir,
                    Path(temp_dir),
                    save_sample=index == 0,
                )
                result = f"{profile.name}: valid PDF, {expected_rows} rows/links, {pages} pages"
                print(f"PASS {result}", flush=True)
                results.append(result)
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=DEFAULT_ARTIFACT_DIR,
        help="directory for the sample PDF and screenshots (default: docs/plans)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifact_dir = args.artifact_dir.resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "-d", str(SITE)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        if not wait_until_serving():
            print(f"FAIL site server did not start on port {PORT}", file=sys.stderr)
            return 1
        results = asyncio.run(run_checks(artifact_dir))
    except Exception as error:
        print(f"FAIL {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)

    print(f"Lead Pack browser check: {len(results)} profiles passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
