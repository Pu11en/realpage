import csv
import importlib.util
from pathlib import Path

HERE = Path(__file__).parent
FX = HERE / "fixtures"
spec = importlib.util.spec_from_file_location("sitemap", HERE.parent / "sitemap.py")
sm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sm)


def fake_fetch(url):
    name = url.rsplit("/", 1)[-1]
    if url == sm.INDEX_URL:
        name = "index.xml"
    p = FX / name
    if not p.exists():
        raise OSError("404 " + url)
    return p.read_text()


def test_types_from_sitemap_names():
    assert sm.sitemap_type("https://x/storage/posts-sitemap.xml") == "posts"
    assert sm.sitemap_type("https://x/storage/management-team-sitemap.xml") == "management-team"
    assert sm.sitemap_type("https://x/storage/case-studies-sitemap2.xml") == "case-studies"


def test_build_rows_dedupes_and_drops_search(capsys):
    rows = sm.build_rows(fake_fetch, delay=0)
    urls = [r["url"] for r in rows]
    assert len(urls) == len(set(urls))
    assert not any("/search/" in u or "/search?" in u for u in urls)
    assert "https://www.realpage.com/searchable-thing/" in urls
    by_url = {r["url"]: r for r in rows}
    assert by_url["https://www.realpage.com/blog/post-one/"]["type"] == "posts"
    assert by_url["https://www.realpage.com/blog/post-one/"]["lastmod"].startswith("2026-09-01")
    assert by_url["https://www.realpage.com/blog/post-two/"]["lastmod"] == ""
    assert by_url["https://www.realpage.com/company/management-team/david-monk/"]["type"] == "management-team"
    assert by_url["https://www.realpage.com/products/"]["type"] == "pages"
    assert len(rows) == 5
    assert "broken-sitemap" in capsys.readouterr().err


def test_write_csv(tmp_path):
    rows = sm.build_rows(fake_fetch, delay=0)
    out = tmp_path / "sub" / "urls.csv"
    sm.write_csv(rows, out)
    got = list(csv.DictReader(out.open()))
    assert got[0].keys() == {"url", "type", "lastmod"}
    assert len(got) == 5
