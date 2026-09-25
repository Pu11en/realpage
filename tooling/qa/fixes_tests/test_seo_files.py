"""SEO: robots.txt, sitemap.xml, llms.txt, per-page metadata and the home page's
JSON-LD. Offline: reads files on disk, makes no network or paid calls.

The site had none of this before 2026-09-23: no robots.txt, no sitemap, no schema,
one shared description across every page, and "/" answering a 302. These tests pin
each of those down so a later edit cannot quietly undo them.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SITE = ROOT / "site"
HOST = "https://app.cranesignal.com"

# Pages a search engine should be able to reach and index on its own.
INDEXABLE = ["index.html", "under-the-hood.html", "privacy.html"]
# Pages that must stay out of the index: a template behind ?id=, an error page, a stub.
NOINDEX = ["property.html", "404.html", "master-table.html"]


def read(name: str) -> str:
    return (SITE / name).read_text(encoding="utf-8")


def test_the_three_files_exist():
    for name in ("robots.txt", "sitemap.xml", "llms.txt"):
        assert (SITE / name).exists(), f"site/{name} is missing"


def test_generator_output_is_current():
    """The files are generated. If the data moved and nobody re-ran the builder,
    the sitemap's lastmod and llms.txt's counts would be lying."""
    done = subprocess.run(
        [sys.executable, str(ROOT / "tooling" / "seo" / "build_seo_files.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stderr or done.stdout


def test_robots_allows_the_ai_crawlers_and_points_at_the_sitemap():
    robots = read("robots.txt")
    for agent in ("GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended", "Bingbot"):
        assert f"User-agent: {agent}" in robots, f"{agent} not named in robots.txt"
    assert f"Sitemap: {HOST}/sitemap.xml" in robots
    # A blanket disallow would undo the whole exercise.
    assert "\nDisallow: /\n" not in robots


def test_sitemap_is_valid_xml_and_lists_every_indexable_page():
    from xml.etree import ElementTree

    root = ElementTree.fromstring(read("sitemap.xml"))
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [el.text for el in root.findall("s:url/s:loc", ns)]
    assert locs, "sitemap has no URLs"
    for page in INDEXABLE:
        assert f"{HOST}/{page}" in locs, f"{page} missing from sitemap"
    for page in NOINDEX:
        assert f"{HOST}/{page}" not in locs, f"{page} should not be in the sitemap"
    for loc in locs:
        assert loc.startswith(HOST + "/"), loc
        rel = loc[len(HOST) + 1 :]
        assert (SITE / rel).exists(), f"sitemap lists {rel}, which is not on disk"
    assert len(locs) == len(set(locs)), "duplicate URLs in sitemap"


def test_sitemap_lastmod_matches_the_data_date():
    index = json.loads((SITE / "data" / "areas" / "index.json").read_text(encoding="utf-8"))
    assert f"<lastmod>{index['updated']}</lastmod>" in read("sitemap.xml")


def test_llms_txt_says_what_this_is_and_where_it_came_from():
    llms = read("llms.txt")
    assert llms.startswith("# CraneSignal")
    assert "> " in llms, "llms.txt needs a one-line summary blockquote"
    for heading in ("## What the data is", "## Where it comes from", "## Coverage", "## Pages"):
        assert heading in llms, f"llms.txt missing {heading}"
    # The counts must be real, not rounded marketing numbers.
    index = json.loads((SITE / "data" / "areas" / "index.json").read_text(encoding="utf-8"))
    total = sum(int(a.get("leads") or 0) for a in index["areas"] if not a.get("hidden"))
    assert f"{total:,}" in llms, f"llms.txt does not state the real building count {total:,}"
    assert index["updated"] in llms


@pytest.mark.parametrize("page", INDEXABLE)
def test_each_indexable_page_has_its_own_title_description_and_canonical(page):
    html = read(page)
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    assert title and title.group(1).strip(), f"{page} has no title"
    desc = re.search(r'<meta name="description" content="(.*?)">', html, re.S)
    assert desc and len(desc.group(1)) > 50, f"{page} has no real description"
    assert f'<link rel="canonical" href="{HOST}/{page}">' in html, f"{page} has no canonical"
    assert 'property="og:title"' in html and 'property="og:description"' in html


def test_titles_and_descriptions_are_unique_across_pages():
    titles, descs = {}, {}
    for page in INDEXABLE:
        html = read(page)
        title = re.search(r"<title>(.*?)</title>", html, re.S).group(1)
        desc = re.search(r'<meta name="description" content="(.*?)">', html, re.S).group(1)
        assert title not in titles, f"{page} repeats the title of {titles.get(title)}"
        assert desc not in descs, f"{page} repeats the description of {descs.get(desc)}"
        titles[title], descs[desc] = page, page


@pytest.mark.parametrize("page", NOINDEX)
def test_template_and_error_pages_are_noindex(page):
    assert '<meta name="robots" content="noindex,follow">' in read(page), page


def test_home_page_jsonld_parses_and_states_the_real_dataset_size():
    html = read("index.html")
    block = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert block, "index.html has no JSON-LD"
    data = json.loads(block.group(1))
    types = [node["@type"] for node in data["@graph"]]
    for wanted in ("Organization", "WebSite", "Dataset"):
        assert wanted in types, f"JSON-LD is missing {wanted}"

    dataset = next(n for n in data["@graph"] if n["@type"] == "Dataset")
    index = json.loads((SITE / "data" / "areas" / "index.json").read_text(encoding="utf-8"))
    total = sum(int(a.get("leads") or 0) for a in index["areas"] if not a.get("hidden"))
    assert f"{total:,}" in dataset["description"]
    assert dataset["dateModified"] == index["updated"]
    assert dataset["isAccessibleForFree"] is True


def test_caddy_serves_the_new_files_and_stops_redirecting_the_home_page():
    caddy = (SITE / "Caddyfile").read_text(encoding="utf-8")
    for path in ("/robots.txt", "/sitemap.xml", "/llms.txt"):
        assert path in caddy, f"Caddyfile never serves {path}"
    assert "/leads/*" in caddy, "Caddyfile does not serve the generated /leads/ pages"
    assert "redir * /index.html 302" not in caddy, "home page is still a 302"
    assert "rewrite * /index.html" in caddy, "home page is not served directly"


# ---- added 2026-09-25 after the fire-your-seo-agency audit -------------------


def test_robots_names_the_three_kinds_of_ai_crawler():
    """Training, search-index and live-fetch crawlers are different user-agents with
    different consequences. Allowing only the training ones costs the citations."""
    robots = read("robots.txt")
    for agent in (
        "GPTBot", "ClaudeBot", "Google-Extended", "CCBot",        # training
        "OAI-SearchBot", "Claude-SearchBot", "PerplexityBot",     # search index
        "ChatGPT-User", "Claude-User", "Perplexity-User",         # live fetch
    ):
        assert f"User-agent: {agent}" in robots, f"{agent} not named in robots.txt"


def test_llms_full_exists_and_carries_the_real_totals():
    full = read("llms-full.txt")
    index = json.loads((SITE / "data" / "areas" / "index.json").read_text(encoding="utf-8"))
    assert index["updated"] in full, "llms-full.txt does not state the data date"
    for area in index["areas"]:
        if area.get("hidden"):
            continue
        assert area["label"] in full, f"{area['label']} missing from llms-full.txt"
        assert f"{int(area['leads']):,}" in full, f"{area['label']} count missing"


def test_the_share_image_is_the_size_every_platform_expects():
    image = SITE / "img" / "og-default.png"
    assert image.exists(), "site/img/og-default.png is missing"
    # PNG header: width and height are big-endian uint32 at bytes 16..24.
    header = image.read_bytes()[:24]
    width = int.from_bytes(header[16:20], "big")
    height = int.from_bytes(header[20:24], "big")
    assert (width, height) == (1200, 630), f"{width}x{height}"


def test_every_indexable_page_has_a_share_image():
    for page in INDEXABLE:
        assert 'property="og:image"' in read(page), f"{page} has no og:image"


def test_caddy_serves_llms_full_and_the_indexnow_key():
    caddy = (SITE / "Caddyfile").read_text(encoding="utf-8")
    assert "/llms-full.txt" in caddy
    assert "/indexnow-*.txt" in caddy
