"""Vendor sample (S3) tests: fake search + fake crawl4ai responses, no network."""
import csv, pathlib, sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run, sample  # noqa: E402

TUCSON = {"slug": "tucson-az", "name": "Tucson", "state": "AZ"}

PAGES = {
    "https://a-apts.com/": "<a href='https://a.loftliving.com/login'>Resident login</a>",
    "https://b-apts.com/": "<a href='https://b.securecafe.com/residentservices/b/userlogin.aspx'>Pay rent</a>",
    "https://c-apts.com/": "<a href='https://c-apts.com/residents'>Residents</a>",
    "https://c-apts.com/residents": "<a href='https://c.residentportal.com/auth'>Portal</a>",
    "https://d-apts.com/": "<p>no portal here</p>",
}


def fake_search(results_per_query):
    calls = []
    def search(q):
        calls.append(q)
        return results_per_query[min(len(calls) - 1, len(results_per_query) - 1)]
    return search, calls


class FakePost:
    """Mimics crawl4ai POST /crawl JSON: links + html."""
    def __call__(self, endpoint, json, timeout):
        url = json["urls"][0]
        class R:
            def json(_):
                if url not in PAGES:
                    return {"results": [{"success": False, "error_message": "404"}]}
                hrefs = [h for h in sample.pms_detect.URL.findall(PAGES[url])]
                return {"results": [{"success": True, "html": PAGES[url],
                                     "links": {"internal": [], "external": [{"href": h} for h in hrefs]}}]}
        return R()


def test_community_url_skips_portals_keeps_vendor_sites():
    assert sample.community_url("https://www.apartments.com/tucson-az/") is None
    assert sample.community_url("https://www.zillow.com/x") is None
    assert sample.community_url("https://pima.gov/housing") is None
    assert sample.community_url("https://downtowntucson.org/") is None
    assert sample.community_url("https://residentportal.com/") is None
    assert sample.community_url("https://www.a-apts.com/floorplans?x=1") == "https://www.a-apts.com/"
    assert sample.community_url("https://b.securecafe.com/onlineleasing/b") == "https://b.securecafe.com/"


def test_find_sites_dedupes_and_counts_each_search():
    batch = [[{"url": "https://a-apts.com/x"}, {"url": "https://apartments.com/y"}, {"url": "https://a-apts.com/z"}],
             [{"url": "https://b-apts.com/"}, {"url": "https://c-apts.com/"}]]
    search, calls = fake_search(batch)
    budget = run.SearchBudget(100)
    sites = sample.find_sites(TUCSON, budget, search, target=3)
    assert [s["url"] for s in sites] == ["https://a-apts.com/", "https://b-apts.com/", "https://c-apts.com/"]
    assert budget.used == len(calls) == 2         # stopped once target was reached
    assert "Tucson AZ" in calls[0]


def test_find_sites_obeys_cap():
    search, calls = fake_search([[]])            # never finds anything -> would keep searching
    budget = run.SearchBudget(3)
    with pytest.raises(run.CapReached):
        sample.find_sites(TUCSON, budget, search)
    assert budget.used == 3 and len(calls) == 3  # never over the cap


def test_classify_with_crawl4ai_reader_and_summary(tmp_path):
    sites = [{"url": u, "title": ""} for u in ("https://a-apts.com/", "https://b-apts.com/",
                                               "https://c-apts.com/", "https://d-apts.com/", "https://gone.com/")]
    rows = sample.classify_sites(sites, sample.Crawl4aiReader(post=FakePost()), workers=1)
    got = {r["url"]: (r["vendor"], r["signal"]) for r in rows}
    assert got["https://a-apts.com/"] == ("RealPage", "portal")
    assert got["https://b-apts.com/"] == ("Yardi", "portal")
    assert got["https://c-apts.com/"] == ("Entrata", "hop-portal")   # one-hop follow
    assert got["https://d-apts.com/"][0] == "unknown"
    assert got["https://gone.com/"] == ("unknown", "error")
    s = sample.summarize(rows)
    assert s == {"total": 5, "RealPage": 1, "Yardi": 1, "Entrata": 1, "unknown": 2}
    # plugs straight into scoring: RealPage share 1/5, rivals 2/5
    assert run.score_metro({"sample": s})["pain"] == 24
    path = sample.write_sample(rows, "tucson-az", tmp_path)
    assert path == tmp_path / "tucson-az" / "sample.csv"
    saved = list(csv.DictReader(open(path)))
    assert saved[0]["evidence"] == "https://a.loftliving.com/login"


def test_sample_metro_end_to_end(tmp_path):
    search, _ = fake_search([[{"url": u} for u in PAGES if u.count("/") == 3]])
    summary, proof, path = sample.sample_metro(TUCSON, run.SearchBudget(10), search,
                                               sample.Crawl4aiReader(post=FakePost()), dest=tmp_path)
    assert summary["total"] == 4 and summary["RealPage"] == 1
    assert "https://a.loftliving.com/login" in proof and path.exists()
