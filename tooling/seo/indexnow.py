#!/usr/bin/env python3
"""Tell Bing, Yandex, Seznam and DuckDuckGo about new or changed pages, immediately.

Why bother, when a sitemap exists: a sitemap is a hint that gets read whenever the
crawler feels like it, which for a small site can be weeks. IndexNow is a push -- you
post a list of URLs and the engines fetch them. It is free, needs no account and no
approval, and Bing's index is what ChatGPT search and Copilot read. For the AI half of
this work that makes it the shortest path from "page published" to "an engine can cite
it". Google does not participate; Google gets the sitemap and Search Console.

How it authenticates: a file at the site root whose name is the key and whose contents
are the key. Serving it proves whoever posts the URLs controls the site. The key is not
a secret -- it is published on purpose -- so it is committed like any other site file.

    python3 tooling/seo/indexnow.py --init        # create the key file (once)
    python3 tooling/seo/indexnow.py --dry-run     # show what would be submitted
    python3 tooling/seo/indexnow.py               # submit every URL in the sitemap
    python3 tooling/seo/indexnow.py --changed-since HEAD~1   # only what a commit touched

Submitting pages that are not live yet is worse than useless -- an engine that fetches a
404 learns the page does not exist -- so the script refuses unless the host serves the
key file and the URLs it is about to send.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
HOST = "app.cranesignal.com"
ENDPOINT = "https://api.indexnow.org/IndexNow"
KEY_GLOB = "indexnow-*.txt"
# The protocol accepts up to 10,000 URLs per call; this site will never approach that.
MAX_URLS = 10_000


def key_file() -> Path | None:
    found = sorted(SITE.glob(KEY_GLOB))
    return found[0] if found else None


def read_key() -> tuple[str, str] | None:
    """Returns (key, filename), or None if the key file has not been created."""
    path = key_file()
    if not path:
        return None
    return path.read_text(encoding="utf-8").strip(), path.name


def init_key() -> int:
    existing = read_key()
    if existing:
        print(f"key file already exists: site/{existing[1]}")
        return 0
    key = uuid.uuid4().hex
    path = SITE / f"indexnow-{key}.txt"
    path.write_text(key, encoding="utf-8", newline="\n")
    print(f"created site/{path.name}")
    print("Commit it and deploy before submitting anything: the engines fetch it to")
    print(f"check that https://{HOST}/{path.name} really serves the key.")
    return 0


def sitemap_urls() -> list[str]:
    path = SITE / "sitemap.xml"
    if not path.exists():
        print("site/sitemap.xml is missing -- run tooling/seo/build_seo_files.py", file=sys.stderr)
        return []
    root = ElementTree.fromstring(path.read_text(encoding="utf-8"))
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [el.text for el in root.findall("s:url/s:loc", ns) if el.text]


def changed_urls(since: str) -> list[str]:
    """URLs for the site pages a commit range touched.

    A weekly data refresh rewrites every generated page, so submitting the whole sitemap
    every week would be noise. This narrows it to what actually changed.
    """
    done = subprocess.run(
        ["git", "diff", "--name-only", since, "--", "site"],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    if done.returncode != 0:
        print(done.stderr.strip(), file=sys.stderr)
        return []
    urls = []
    for line in done.stdout.splitlines():
        if not line.endswith(".html"):
            continue
        rel = line[len("site/"):] if line.startswith("site/") else line
        urls.append(f"https://{HOST}/{rel}")
    return urls


def is_live(url: str, timeout: int = 10) -> bool:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "CraneSignal/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 300
    except Exception:  # noqa: BLE001 - any failure means "do not submit this"
        return False


def submit(urls: list[str], key: str, key_name: str, timeout: int = 30) -> int:
    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": f"https://{HOST}/{key_name}",
        "urlList": urls[:MAX_URLS],
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            # 200 and 202 both mean accepted; 202 means the key is still being verified.
            print(f"submitted {len(payload['urlList'])} URLs -- HTTP {response.status}")
            return 0
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")[:300]
        print(f"IndexNow refused: HTTP {err.code} {body}", file=sys.stderr)
        if err.code == 403:
            print(f"  403 usually means https://{HOST}/{key_name} is not serving the key yet.",
                  file=sys.stderr)
        return 1
    except Exception as err:  # noqa: BLE001
        print(f"IndexNow request failed: {err}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", help="create the key file")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--changed-since", metavar="REF",
                        help="only URLs whose files changed since this git ref")
    parser.add_argument("--skip-live-check", action="store_true",
                        help="submit without checking the pages are live (not advised)")
    args = parser.parse_args()

    if args.init:
        return init_key()

    found = read_key()
    if not found:
        print("no key file -- run: python3 tooling/seo/indexnow.py --init", file=sys.stderr)
        return 2
    key, key_name = found

    urls = changed_urls(args.changed_since) if args.changed_since else sitemap_urls()
    urls = sorted(set(urls))
    if not urls:
        print("nothing to submit")
        return 0

    if args.dry_run:
        print(f"would submit {len(urls)} URLs using https://{HOST}/{key_name}:")
        for url in urls:
            print("  " + url)
        return 0

    if not args.skip_live_check:
        if not is_live(f"https://{HOST}/{key_name}"):
            print(f"https://{HOST}/{key_name} is not live -- deploy the key file first.",
                  file=sys.stderr)
            return 1
        live = [url for url in urls if is_live(url)]
        missing = len(urls) - len(live)
        if missing:
            print(f"skipping {missing} URL(s) that are not live yet", file=sys.stderr)
        urls = live
        if not urls:
            print("none of the URLs are live -- nothing submitted", file=sys.stderr)
            return 1

    return submit(urls, key, key_name)


if __name__ == "__main__":
    raise SystemExit(main())
