"""Churn + pain (S4) tests: fake search + fake Reddit results, no network."""
import datetime, json, pathlib, sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run, churn_pain as cp  # noqa: E402

TODAY = datetime.date(2026, 9, 13)
TUCSON = {"slug": "tucson-az", "name": "Tucson", "state": "AZ"}


def test_find_date_from_url_text_and_relative():
    assert cp.find_date("", "https://news.com/2025/03/14/story") == datetime.date(2025, 3, 14)
    assert cp.find_date("Published Mar 5, 2026 by staff") == datetime.date(2026, 3, 5)
    assert cp.find_date("updated 2025-11-02") == datetime.date(2025, 11, 2)
    assert cp.find_date("3 weeks ago", today=TODAY) == datetime.date(2026, 8, 23)
    assert cp.find_date("no date here") is None
    assert cp.in_window(datetime.date(2025, 1, 1), TODAY)
    assert not cp.in_window(datetime.date(2024, 1, 1), TODAY)     # older than 24 months
    assert not cp.in_window(None, TODAY)


NEWS = [
    {"url": "https://bizjournals.com/phoenix/news/2026/02/10/tucson-apartment-sold.html",
     "title": "Tucson apartment complex sold for $40M", "description": "312 units change hands"},
    {"url": "https://azdailystar.com/x", "title": "Investor acquires Tucson multifamily community",
     "description": "Jan 12, 2026 — the 200-unit property gets new management"},
    {"url": "https://old.com/2022/05/01/tucson-apartments-sold", "title": "Tucson apartments sold",
     "description": "old deal"},                                   # outside the window
    {"url": "https://nodate.com/tucson", "title": "Tucson apartments sold", "description": "no date"},
    {"url": "https://phx.com/2026/01/01/x", "title": "Phoenix apartments sold", "description": "units"},  # wrong city
    {"url": "https://tucson.com/2026/01/05/zoo", "title": "Tucson zoo opens", "description": ""},     # not a deal
]


def test_churn_items_keep_dated_recent_relevant_only():
    calls = []
    def search(q):
        calls.append(q)
        return NEWS
    budget = run.SearchBudget(100)
    items = cp.churn_items(TUCSON, budget, search, today=TODAY)
    assert [i["url"] for i in items] == [NEWS[0]["url"], NEWS[1]["url"]]
    assert items[1]["date"] == "2026-01-12"
    assert budget.used == len(calls) == len(cp.NEWS_QUERIES)
    assert "Tucson AZ" in calls[0]


class FakeReader:
    def __init__(self, pages):
        self.pages, self.calls = pages, []
    def get(self, url):
        self.calls.append(url)
        if url not in self.pages:
            raise RuntimeError("crawl failed")
        return self.pages[url]


def test_undated_news_gets_date_from_page_metadata_and_portals_skipped():
    results = [
        {"url": "https://costar.com/article/1/acquires", "title": "Bascom acquires 289-unit Tucson apartment complex",
         "description": ""},
        {"url": "https://mhn.com/buys-tucson", "title": "Fund buys Tucson community", "description": "304 units"},
        {"url": "https://www.trulia.com/sold/Tucson,AZ/", "title": "Recently Sold Homes in Tucson",
         "description": "SOLD SEP 9, 2026 3 units"},                  # listing portal, skipped
    ]
    reader = FakeReader({"https://costar.com/article/1/acquires":
                         '<script type="application/ld+json">{"datePublished": "2026-05-04T10:00"}</script>'})
    items = cp.churn_items(TUCSON, run.SearchBudget(100), lambda q: results, reader, today=TODAY)
    assert [(i["url"], i["date"]) for i in items] == [("https://costar.com/article/1/acquires", "2026-05-04")]
    assert "https://www.trulia.com/sold/Tucson,AZ/" not in reader.calls   # skipped before any fetch
    assert cp.page_date('<meta property="article:published_time" content="2025-10-01T08:00:00Z">') \
        == datetime.date(2025, 10, 1)
    assert cp.page_date('automation-id="article-date">June 5, 2026 | 6:19 P.M.</div>') == datetime.date(2026, 6, 5)
    assert cp.page_date('\\"publishDate\\":\\"2026-06-05T18:19:20+00:00\\"') == datetime.date(2026, 6, 5)
    assert cp.page_date("<p>© 2026</p>") is None


def test_churn_obeys_cap():
    budget = run.SearchBudget(2)
    with pytest.raises(run.CapReached):
        cp.churn_items(TUCSON, budget, lambda q: [])
    assert budget.used == 2


WEB_PAIN = [
    {"url": "https://reviews.com/2026/04/02/tucson", "title": "Tucson renters: RentCafe portal charged a fee twice",
     "description": ""},
    {"url": "https://x.com/2026/04/02/y", "title": "Tucson apartment pool", "description": "Yardi"},  # no pain word
    {"url": "https://z.com/tucson", "title": "Entrata portal down", "description": ""},              # no date
]
REDDIT = [
    {"url": "https://www.reddit.com/r/Tucson/1", "title": "Entrata resident portal login broken again",
     "body": "", "createdUtc": datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc).timestamp()},
    {"url": "https://www.reddit.com/r/Tucson/2", "title": "Best tacos", "body": "",
     "createdUtc": datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc).timestamp()},
    {"url": "https://www.reddit.com/r/Tucson/3", "title": "RealPage payment fees", "body": "",
     "createdUtc": datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc).timestamp()},   # too old
]


def test_pain_items_web_and_reddit_name_vendor():
    budget = run.SearchBudget(100)
    reddit_calls = []
    def reddit(q, sub):
        reddit_calls.append((q, sub))
        return REDDIT
    items = cp.pain_items(TUCSON, budget, lambda q: WEB_PAIN, reddit, today=TODAY)
    assert [(i["source"], i["vendors"]) for i in items] == [("web", ["Yardi"]), ("reddit", ["Entrata"])]
    assert budget.used == len(cp.PAIN_QUERIES)                   # Reddit is free, not counted
    assert reddit_calls[0][1] == "Tucson" and len(reddit_calls) == len(cp.REDDIT_QUERIES)
    # no Reddit cookie -> web only, still works
    assert len(cp.pain_items(TUCSON, run.SearchBudget(100), lambda q: WEB_PAIN, None, today=TODAY)) == 1


def test_churn_pain_metro_writes_evidence_and_feeds_score(tmp_path, monkeypatch):
    monkeypatch.setattr(cp.datetime, "date", type("D", (datetime.date,), {"today": staticmethod(lambda: TODAY)}))
    search = lambda q: NEWS if "sold" in q or "acquired" in q or "management" in q or "buyer" in q else WEB_PAIN
    n_churn, n_pain, links, path = cp.churn_pain_metro(TUCSON, run.SearchBudget(100), search, lambda q, sub: REDDIT, tmp_path)
    saved = json.loads(path.read_text())
    assert path == tmp_path / "tucson-az" / "evidence.json"
    assert (n_churn, n_pain) == (2, 2) and len(saved["churn"]) == 2 and len(saved["complaints"]) == 2
    assert all(i["url"] and i["date"] for i in saved["churn"] + saved["complaints"])
    assert NEWS[0]["url"] in links
    s = run.score_metro({"churn_items": n_churn, "complaints": n_pain})
    assert s["churn"] == 10 and s["pain"] == 8
