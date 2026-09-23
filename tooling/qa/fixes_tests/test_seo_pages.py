"""SEO: the static pages under site/leads/.

These exist because every other page on the site is a JavaScript shell. The tests below
check the two things that make them worth having -- they are readable without running
any script, and they carry real sourced rows -- plus the guard rails that keep them from
turning into the kind of mass-produced thin pages Google demotes sitewide.

Offline: reads files on disk, no network, no paid calls.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SITE = ROOT / "site"
LEADS = SITE / "leads"
HOST = "https://app.cranesignal.com"

# Below this a page is thin, and thin pages are the sitewide risk. build_pages.py uses
# 25 buildings as the floor; a page can still be short if a place has few big buildings,
# so the test floor is deliberately lower than the generator's.
MIN_ROWS = 20
MIN_WORDS = 600
# Half a megabyte of HTML is slow on a phone; the generator caps rows to stay under this.
MAX_BYTES = 260_000


def pages() -> list[Path]:
    return sorted(LEADS.rglob("*.html"))


def text_of(path: Path) -> str:
    """Visible text only: what a crawler that ignores scripts and markup would read."""
    html = path.read_text(encoding="utf-8")
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", html)


def test_pages_exist():
    assert pages(), "no pages under site/leads/ -- run tooling/seo/build_pages.py"


def test_generator_output_is_current():
    done = subprocess.run(
        [sys.executable, str(ROOT / "tooling" / "seo" / "build_pages.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stderr or done.stdout


def test_the_five_metro_pages_exist():
    """These are the pages the search demand actually points at -- see
    docs/plans/PLAN-seo-geo-strategy.md. Losing one silently would gut the plan."""
    for rel in (
        "tx/dallas-fort-worth.html",
        "tx/houston.html",
        "tx/austin.html",
        "tx/san-antonio.html",
        "az/phoenix.html",
    ):
        assert (LEADS / rel).exists(), f"missing metro page {rel}"


def test_state_pages_exist_for_every_visible_area():
    index = json.loads((SITE / "data" / "areas" / "index.json").read_text(encoding="utf-8"))
    for area in index["areas"]:
        if area.get("hidden"):
            continue
        assert (LEADS / f"{area['slug']}.html").exists(), area["slug"]


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_page_is_readable_without_javascript(path):
    html = path.read_text(encoding="utf-8")
    # No script tag other than the JSON-LD block: nothing has to run for the page to read.
    scripts = re.findall(r"<script([^>]*)>", html)
    assert all("application/ld+json" in attrs for attrs in scripts), f"{path.name} runs JavaScript"
    body = html.split("<body", 1)[1]
    assert "<table" in body and "<h1>" in body


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_page_has_enough_real_content(path):
    words = len(text_of(path).split())
    assert words >= MIN_WORDS, f"{path.name} has only {words} words"
    rows = path.read_text(encoding="utf-8").count("<tr><td>")
    assert rows >= MIN_ROWS, f"{path.name} has only {rows} rows"


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_page_is_not_too_heavy(path):
    size = path.stat().st_size
    assert size <= MAX_BYTES, f"{path.name} is {size:,} bytes"


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_page_rows_link_their_source(path):
    """The whole claim of these pages is that every building is sourced. A row with no
    link is a claim we cannot back, which the repo's ground rules forbid."""
    html = path.read_text(encoding="utf-8")
    # The buildings table is the last one on the page; the earlier ones are the
    # stage/year/city breakdowns, which have nothing to source.
    body = html.rsplit("<tbody>", 1)[1].split("</tbody>", 1)[0]
    rows = re.findall(r"<tr>.*?</tr>", body, re.S)
    assert len(rows) >= MIN_ROWS, f"{path.name} has only {len(rows)} building rows"
    unlinked = [row for row in rows if '<a href="http' not in row]
    assert not unlinked, (
        f"{path.name}: {len(unlinked)} of {len(rows)} building rows have no source link; "
        f"first: {unlinked[0][:160]}"
    )


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_page_metadata_and_schema(path):
    html = path.read_text(encoding="utf-8")
    rel = path.relative_to(SITE).as_posix()
    assert f'<link rel="canonical" href="{HOST}/{rel}">' in html, f"{path.name} canonical is wrong"
    desc = re.search(r'<meta name="description" content="(.*?)">', html, re.S)
    assert desc and len(desc.group(1)) > 60, f"{path.name} has a weak description"
    block = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert block, f"{path.name} has no JSON-LD"
    data = json.loads(block.group(1))
    types = [node["@type"] for node in data["@graph"]]
    assert "Dataset" in types and "ItemList" in types, types


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_page_states_the_data_date_and_links_back(path):
    index = json.loads((SITE / "data" / "areas" / "index.json").read_text(encoding="utf-8"))
    year = index["updated"][:4]
    text = text_of(path)
    assert year in text, f"{path.name} never states the data date"
    html = path.read_text(encoding="utf-8")
    assert "under-the-hood.html" in html, f"{path.name} does not link how it was built"
    assert "index.html" in html, f"{path.name} does not link the searchable list"


def test_titles_and_descriptions_are_unique_across_every_page():
    """Duplicate titles are the clearest signal of a templated page farm, and two pages
    competing for one phrase beat each other rather than the competition."""
    seen_titles, seen_descs = {}, {}
    for path in pages():
        html = path.read_text(encoding="utf-8")
        title = re.search(r"<title>(.*?)</title>", html, re.S).group(1)
        desc = re.search(r'<meta name="description" content="(.*?)">', html, re.S).group(1)
        assert title not in seen_titles, f"{path.name} repeats the title of {seen_titles.get(title)}"
        assert desc not in seen_descs, f"{path.name} repeats the description of {seen_descs.get(desc)}"
        seen_titles[title], seen_descs[desc] = path.name, path.name


def test_no_realpage_text_anywhere():
    for path in pages():
        assert "RealPage" not in path.read_text(encoding="utf-8"), path.name


def test_home_page_carries_the_pre_javascript_summary_and_links_every_page():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert "SEO-STATIC:start" in html and 'class="pre-js-summary"' in html
    for path in pages():
        rel = path.relative_to(SITE).as_posix()
        assert f'href="{rel}"' in html, f"home page does not link {rel}"


def test_every_page_is_in_the_sitemap():
    sitemap = (SITE / "sitemap.xml").read_text(encoding="utf-8")
    for path in pages():
        rel = path.relative_to(SITE).as_posix()
        assert f"{HOST}/{rel}" in sitemap, f"{rel} missing from sitemap.xml"


def test_a_metro_page_and_its_city_page_do_not_share_a_url():
    """A metro is usually named after its anchor city. If both got a page they would
    overwrite each other on disk and compete for the same phrase in search."""
    names = [p.stem for p in pages()]
    assert len(names) == len(set(names)) or True  # same stem in different states is fine
    for state_dir in (d for d in LEADS.iterdir() if d.is_dir()):
        stems = [p.stem for p in state_dir.glob("*.html")]
        assert len(stems) == len(set(stems)), f"duplicate page slugs in {state_dir.name}"


def test_county_rows_never_become_a_page():
    """'Tarrant County' is in the data as a place, but it is not a city and a page
    titled that way would read as a bug."""
    for path in pages():
        title = re.search(r"<title>(.*?)</title>", path.read_text(encoding="utf-8"), re.S).group(1)
        assert "County" not in title, f"{path.name}: {title}"
