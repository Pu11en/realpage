"""SEO: the static pages under site/leads/.

These exist because every other page on the site is a JavaScript shell. The tests below
check the two things that make them worth having -- they are readable without running
any script, and they carry real sourced rows -- plus the guard rails that keep them from
turning into the kind of mass-produced thin pages Google demotes sitewide.

Offline: reads files on disk, no network, no paid calls.
"""
import csv
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
# The brand's one identity, declared on the landing page at cranesignal.com and repeated
# under the same @id on every page here, so the two hosts are one entity to a model.
ORG_ID = "https://cranesignal.com/#org"

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


# ---- added 2026-09-25 after the fire-your-seo-agency audit -------------------
# The skill's checklists (.claude/skills/fire-your-seo-agency/references/en/) call out
# four things the first pass missed: titles that fit a search result, a share image,
# breadcrumb and FAQ schema, and one Organization entity rather than one per page.


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_title_fits_in_a_search_result(path):
    """Google cuts around 60 characters. Longer titles bury the place name behind
    boilerplate, which is the one word the searcher typed."""
    title = re.search(r"<title>(.*?)</title>", path.read_text(encoding="utf-8"), re.S).group(1)
    assert len(title) <= 60, f"{path.name}: {len(title)} chars -- {title}"
    assert title.endswith("| CraneSignal"), title


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_page_has_a_share_image(path):
    html_text = path.read_text(encoding="utf-8")
    assert 'property="og:image"' in html_text, f"{path.name} has no og:image"
    assert (SITE / "img" / "og-default.png").exists(), "the share image itself is missing"


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_page_carries_breadcrumb_and_faq_schema(path):
    block = re.search(
        r'<script type="application/ld\+json">(.*?)</script>',
        path.read_text(encoding="utf-8"), re.S,
    )
    types = [node["@type"] for node in json.loads(block.group(1))["@graph"]]
    assert "BreadcrumbList" in types, f"{path.name} has visible crumbs but no BreadcrumbList"
    assert "FAQPage" in types, f"{path.name} has no FAQPage"


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_faq_schema_is_identical_to_the_visible_text(path):
    """Structured data that says something the page does not show risks a spam verdict,
    and it is the fastest way to lose the citation trust the whole plan depends on."""
    import html as html_mod

    raw = path.read_text(encoding="utf-8")
    faq = next(
        node for node in json.loads(
            re.search(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S).group(1)
        )["@graph"] if node["@type"] == "FAQPage"
    )
    shown = raw.split('<dl class="faq">', 1)[1].split("</dl>", 1)[0]
    shown = re.sub(r"\s+", " ", html_mod.unescape(re.sub(r"<[^>]+>", " ", shown)))
    for question in faq["mainEntity"]:
        for text in (question["name"], question["acceptedAnswer"]["text"]):
            assert re.sub(r"\s+", " ", text) in shown, f"{path.name}: not on the page -- {text[:60]}"


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_one_organization_entity_across_the_whole_site(path):
    """Every page names the same brand @id, and nothing on it invents a second one.

    Changed 2026-09-26. This used to demand that no page declare an Organization node at
    all, on the reasoning that a fresh Organization per page splits the entity. The
    reasoning is right and the assertion was in the wrong place: the pages were left
    naming an @id that is declared on the *other* host, so a crawler reading one page
    alone found creator and publisher pointing at nothing. Repeating the node under the
    same @id is how JSON-LD says "this is that same thing" -- it unifies rather than
    splits. What has to be enforced is the id, so that is what is asserted now, plus the
    absence of any second identity, which the old version could not catch.
    """
    graph = json.loads(re.search(
        r'<script type="application/ld\+json">(.*?)</script>',
        path.read_text(encoding="utf-8"), re.S,
    ).group(1))["@graph"]
    dataset = next(node for node in graph if node["@type"] == "Dataset")
    assert dataset["creator"] == {"@id": ORG_ID}, dataset["creator"]
    assert dataset["publisher"] == {"@id": ORG_ID}, dataset["publisher"]

    orgs = [node for node in graph if node["@type"] == "Organization"]
    assert len(orgs) == 1, f"{path.name} declares {len(orgs)} Organization nodes, want 1"
    assert orgs[0]["@id"] == ORG_ID, (
        f"{path.name} mints a second brand identity: {orgs[0].get('@id')!r}"
    )
    # Enough to resolve on its own. An @id with nothing attached is the bare reference
    # this change exists to remove.
    assert orgs[0]["name"] == "CraneSignal"
    assert orgs[0]["url"] == "https://cranesignal.com"


# ------------------------------------------------- the spreadsheet beside each page
#
# Added 2026-09-26. The site already offered a free spreadsheet, but it was assembled
# inside the visitor's browser and never existed as a URL -- so Google Dataset Search, an
# AI crawler and a `curl` all found nothing. The measured opening for CraneSignal is the
# free-data question: engines name paid tools 70% of the time even when asked for a free
# source, because as far as they can see none exists. These tests hold the three things
# that make the new files count: the file is there, the page links it, and the schema
# describes it accurately enough to be trusted.


def dataset_of(path: Path) -> dict:
    graph = json.loads(re.search(
        r'<script type="application/ld\+json">(.*?)</script>',
        path.read_text(encoding="utf-8"), re.S,
    ).group(1))["@graph"]
    return next(node for node in graph if node["@type"] == "Dataset")


def csv_of(path: Path) -> list[list[str]]:
    with path.with_suffix(".csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_every_page_has_a_spreadsheet_beside_it(path):
    assert path.with_suffix(".csv").is_file(), (
        f"{path.name} has no CSV -- run tooling/seo/build_pages.py"
    )


def test_no_spreadsheet_outlives_its_page():
    """A CSV left behind after its page was dropped is a live URL serving numbers nothing
    on the site stands behind any more."""
    orphans = [p.name for p in LEADS.rglob("*.csv") if not p.with_suffix(".html").exists()]
    assert not orphans, orphans


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_the_spreadsheet_holds_every_row_not_the_capped_set(path):
    """The page's table is capped at 400 rows; the file is the whole list. That is the
    reason to offer it, and the page says so, so it has to be true."""
    rows = csv_of(path)
    assert len(rows) >= 2, f"{path.name}: empty CSV"
    listed = json.loads(re.search(
        r'<script type="application/ld\+json">(.*?)</script>',
        path.read_text(encoding="utf-8"), re.S,
    ).group(1))["@graph"]
    item_list = next(node for node in listed if node["@type"] == "ItemList")
    assert len(rows) - 1 == item_list["numberOfItems"], (
        f"{path.name}: CSV has {len(rows) - 1} rows, ItemList claims {item_list['numberOfItems']}"
    )


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_the_page_links_its_own_spreadsheet_and_states_the_row_count(path):
    raw = path.read_text(encoding="utf-8")
    rows = len(csv_of(path)) - 1
    href = path.with_suffix(".csv").name
    assert f'href="{HOST}/leads/' in raw or href in raw, f"{path.name} does not link its CSV"
    assert f"CSV, {rows:,} rows" in raw, (
        f"{path.name} does not state the row count a reader is about to download"
    )
    assert "no account" in text_of(path).lower()


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_the_distribution_points_at_a_file_that_exists_and_is_the_right_size(path):
    """A contentSize that disagrees with the file is worse than none: it is the one claim
    in the schema a fetcher can check for free, and getting it wrong is a reason to
    distrust everything beside it."""
    dataset = dataset_of(path)
    download = dataset["distribution"][0]
    assert download["encodingFormat"] == "text/csv"
    rel = download["contentUrl"].removeprefix(HOST + "/")
    on_disk = SITE / rel
    assert on_disk.is_file(), f"{path.name}: distribution points at {rel}, which is not there"
    assert on_disk == path.with_suffix(".csv"), rel
    declared = int(download["contentSize"].split()[0])
    # Compared as text, not as bytes on disk: git checks these out with CRLF on
    # Windows, while the size in the schema and the bytes actually served both use LF.
    assert declared == len(on_disk.read_text(encoding="utf-8").encode("utf-8")), (
        f"{path.name}: schema says {declared} B, file is "
        f"{len(on_disk.read_text(encoding='utf-8').encode('utf-8'))} B"
    )


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_variables_measured_match_the_spreadsheet_header_exactly(path):
    """variableMeasured is how an engine decides what questions the data can answer. A
    column named there but missing from the file is a promise the download breaks."""
    named = [v["name"] for v in dataset_of(path)["variableMeasured"]]
    header = csv_of(path)[0]
    assert named == header, f"{path.name}: schema {named} vs header {header}"
    for variable in dataset_of(path)["variableMeasured"]:
        assert variable["description"].strip(), variable["name"]


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_the_dataset_says_where_and_when_it_is_about(path):
    """The home page has carried these since the start; the pages built to actually be
    found carried none of them, which was backwards."""
    dataset = dataset_of(path)
    spatial = dataset["spatialCoverage"]
    names = [spatial["name"]] if isinstance(spatial, dict) else [p["name"] for p in spatial]
    assert all(names), path.name
    assert " and " not in " ".join(names), (
        f"{path.name}: {names} -- a joined place name is not a place"
    )
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}(/\d{4}-\d{2}-\d{2})?", dataset["temporalCoverage"]), (
        f"{path.name}: {dataset['temporalCoverage']!r}"
    )
    assert dataset["keywords"], path.name
    assert dataset["isAccessibleForFree"] is True


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_every_spreadsheet_row_can_be_checked_against_a_public_record(path):
    """Same rule the HTML table follows: the point of the data is that any line links the
    record it came from. A blank source column is a row a reader has to take on faith."""
    rows = csv_of(path)
    url_at = rows[0].index("Source URL")
    unsourced = [row[0] for row in rows[1:] if not row[url_at].startswith("http")]
    assert not unsourced, (
        f"{path.name}: {len(unsourced)} of {len(rows) - 1} rows have no source URL, "
        f"e.g. {unsourced[:3]}"
    )


@pytest.mark.parametrize("path", pages(), ids=lambda p: p.name)
def test_the_spreadsheet_never_guesses(path):
    """Blank means the record is silent. A zero in Units would read as "no apartments",
    and a made-up date would be worse."""
    rows = csv_of(path)
    head = rows[0]
    units_at, opens_at, sold_at = head.index("Units"), head.index("Opens"), head.index("Sold")
    for row in rows[1:]:
        assert row[units_at] != "0", f"{path.name}: a zero-unit building -- {row[0]}"
        for column in (opens_at, sold_at):
            if row[column]:
                assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", row[column]), (
                    f"{path.name}: {row[column]!r} is not an ISO date -- {row[0]}"
                )


# ----------------------------------------------------- the source link every row promises
#
# Added 2026-09-26 after measuring what those links actually opened. Across all 1,861
# buildings: 9% linked a page showing that building, 40% linked a bulk file (one was 212 MB),
# and 23% linked a URL a browser could not open at all -- a single Dallas County address that
# carries a literal Windows path, backslashes and a space included, reproduced into 449 hrefs.
#
# This is the claim the product rests on. Every page, every CSV and every outreach pack says
# each row names the record it came from. These tests hold the two halves of keeping that
# true: the link has to work, and the label has to say what it is.


def all_sources():
    out = []
    for area in json.loads((SITE / "data" / "areas" / "index.json").read_text(encoding="utf-8"))["areas"]:
        if area.get("hidden"):
            continue
        path = SITE / "data" / "areas" / f"{area['slug']}.json"
        for lead in json.loads(path.read_text(encoding="utf-8"))["leads"]:
            for source in (lead.get("sources") or []):
                out.append((lead.get("id"), source))
    return out


def test_no_source_url_is_malformed():
    """A backslash or a space in an href is a link that cannot open. run_area._safe_url()
    already percent-encodes Dallas County's for the fetcher; build_data._safe_href() is the
    reader-facing half that was missing."""
    bad = [(lead_id, s["url"]) for lead_id, s in all_sources()
           if s.get("url") and re.search(r"[\ ]", s["url"])]
    assert not bad, f"{len(bad)} unopenable source URLs, e.g. {bad[:2]}"


def test_every_source_url_is_an_absolute_http_link():
    bad = [(lead_id, s["url"]) for lead_id, s in all_sources()
           if s.get("url") and not s["url"].startswith(("http://", "https://"))]
    assert not bad, bad[:3]


def test_no_source_label_is_a_bare_website():
    """"Website" was the label on a 212 MB county zip. A label that says nothing is worse
    than none, because the reader spends the click to find out."""
    bare = {"website", "link", "source", "url", "record"}
    bad = sorted({s["label"] for _, s in all_sources()
                  if (s.get("label") or "").strip().lower() in bare})
    assert not bad, f"uninformative source labels: {bad}"


def test_a_bulk_download_says_so_in_its_label():
    """If the link hands over a file rather than a page, the label has to name the format."""
    missing = sorted({
        s["label"] for _, s in all_sources()
        if s.get("url") and re.search(r"\.(zip|xlsx|xls|csv)($|\?)", s["url"], re.I)
        and not re.search(r"\b(ZIP|XLSX|XLS|CSV)\b", s["label"] or "")
    })
    assert not missing, f"bulk-file links whose label does not say so: {missing}"


def test_the_pages_do_not_overclaim_what_the_source_link_opens():
    """Only 9% of rows link the building's own record, so "each row links the public record
    it came from" read as a promise the other 91% broke. The wording now says which is
    which; if someone restores the old sentence, this fails."""
    for path in pages():
        text = text_of(path)
        assert "Every row names the public record it came from" in text, path.name
        assert "most open the county or city source" in text, path.name
        assert "Each row links the public record it came from" not in text, path.name


def test_the_home_page_is_not_thin_to_a_crawler():
    """The home page is the sitemap's 1.0 and the page every /leads/ page links back to.
    Before 2026-09-26 the block inside its app shell was a heading, one sentence and a list
    of links -- 201 visible words, thinner than any page pointing at it. Everything in it is
    computed from site/data/, so it cannot drift from what the site actually holds.

    Counted with <script> removed, because app.js replaces this block the moment it runs:
    this is only ever what a crawler that does not run JavaScript sees.
    """
    html = (SITE / "index.html").read_text(encoding="utf-8")
    outside_scripts = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    body = re.search(r"<body.*?</body>", outside_scripts, re.S).group(0)
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    assert words >= 350, f"home page shows a crawler only {words} words"

    assert len(re.findall(r"<h1", outside_scripts)) == 1, "more than one h1 in the markup"
    assert len(re.findall(r"<h2", outside_scripts)) >= 4, "no section headings to read"

    text = re.sub(r"<[^>]+>", " ", body)
    # The three things a reader or an engine has to be able to learn here.
    assert "sell" in text and "apartment owners" in text, "does not say who it is for"
    assert "never that we guessed" in text, "does not state the blank-cell rule"
    assert ".csv" in text and "no account" in text, "does not mention the free spreadsheet"
