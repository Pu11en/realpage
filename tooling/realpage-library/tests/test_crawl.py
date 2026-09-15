import csv
import importlib.util
from pathlib import Path

HERE = Path(__file__).parent
FX = HERE / "fixtures"
spec = importlib.util.spec_from_file_location("crawl", HERE.parent / "crawl.py")
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)

URL = "https://www.realpage.com/sample-product-software/"
HTML = (FX / "product-page.html").read_text()
ROW = {"url": URL, "type": "pages", "lastmod": "2026-01-02T00:00:00-06:00"}


def no_sleep(_):
    pass


def run(tmp_path, rows, fetch, fallback=None, **kw):
    return cr.crawl(rows, fetch, fallback, site=tmp_path, delay=0, today="2026-09-15",
                    log=lambda *_: None, sleep=no_sleep, **kw)


def test_cleaner_keeps_content_drops_junk():
    title, md = cr.html_page_to_markdown(HTML, URL)
    assert title == "Sample Product Software"
    assert "# Sample Product Software" in md
    assert "one connected platform" in md
    assert "Faster onboarding" in md
    assert "(https://www.realpage.com/case-studies/sample-story/" in md
    for junk in ["MENU-JUNK", "COOKIE-JUNK", "SUBNAV-JUNK", "SCRIPT-JUNK", "FOOTER-JUNK", "Skip to content", "Accept All"]:
        assert junk not in md, junk


def test_saves_page_with_header(tmp_path):
    stats = run(tmp_path, [ROW], lambda u: HTML)
    assert stats["saved"] == 1
    out = tmp_path / "pages" / "pages" / "sample-product-software.md"
    text = out.read_text()
    assert text.startswith("---\nurl: \"" + URL + "\"\n")
    for key in ['title: "Sample Product Software"', 'type: "pages"', 'lastmod: "2026-01-02', 'crawled: "2026-09-15"']:
        assert key in text
    assert text.count("# Sample Product Software") == 1


def test_resume_skips_saved_and_limit(tmp_path):
    rows = [ROW, {"url": URL + "two/", "type": "pages", "lastmod": ""},
            {"url": URL + "three/", "type": "pages", "lastmod": ""}]
    calls = []
    fetch = lambda u: calls.append(u) or HTML
    assert run(tmp_path, rows, fetch, limit=1)["saved"] == 1
    stats = run(tmp_path, rows, fetch)
    assert stats == {"saved": 2, "skipped": 1, "failed": 0, "fallback": 0}
    assert calls == [URL, URL + "two/", URL + "three/"]


def test_fallback_when_short_or_error(tmp_path):
    long_md = "Jina text about the product. " * 20
    rows = [ROW, {"url": URL + "err/", "type": "posts", "lastmod": ""}]

    def fetch(u):
        if u.endswith("err/"):
            raise RuntimeError("boom")
        return "<main><p>tiny</p></main>"

    stats = run(tmp_path, rows, fetch, fallback=lambda u: ("From Jina", long_md))
    assert stats["saved"] == 2 and stats["fallback"] == 2
    text = (tmp_path / "pages" / "posts" / "sample-product-software-err.md").read_text()
    assert 'source: "jina"' in text and "# From Jina" in text


def test_failures_logged(tmp_path):
    def fetch(u):
        raise RuntimeError("503 down")

    def fallback(u):
        raise RuntimeError("no key")

    stats = run(tmp_path, [ROW], fetch, fallback=fallback)
    assert stats["failed"] == 1
    rows = list(csv.DictReader((tmp_path / "failed.csv").open()))
    assert rows[0]["url"] == URL and "503 down" in rows[0]["reason"] and "no key" in rows[0]["reason"]
    assert not (tmp_path / "pages").exists()


def test_slugs():
    assert cr.slug_for("https://www.realpage.com/") == "home"
    assert cr.slug_for("https://www.realpage.com/blog/Some_Post/") == "blog-some-post"


def test_tidy_drops_share_and_contact_junk():
    md = "# Title\n--\nBy Staff\n|\nShare\n[ Facebook ](https://x) [ Twitter ](https://y)\nBody text.\n##### Have a question about our products or services?\nContact Us\n"
    out = cr.tidy_markdown(md)
    assert out == "# Title\nBy Staff\nBody text.\n"
