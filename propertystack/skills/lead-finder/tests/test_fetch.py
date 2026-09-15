"""Fixture tests for fetch.py -- no network, no real Jina/Brave/crawl4ai calls."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fetch as fetch_mod  # noqa: E402


class _FakeBraveUsage:
    def __init__(self, under_cap: bool = True) -> None:
        self.calls = 0
        self._under_cap = under_cap

    def under_cap(self, cap: int | None = None) -> bool:
        return self._under_cap

    def record_call(self) -> None:
        self.calls += 1


def _helper(
    tmp_path,
    page_fetchers=None,
    jina_api_key=fetch_mod._UNSET,
    brave_api_key=fetch_mod._UNSET,
    brave_usage=None,
):
    return fetch_mod.WebHelper(
        cache_dir=tmp_path,
        jina_api_key=jina_api_key,
        brave_api_key=brave_api_key,
        brave_usage=brave_usage if brave_usage is not None else _FakeBraveUsage(),
        page_fetchers=page_fetchers,
        site_gap_s=0.0,
    )


def test_search_uses_jina_when_it_has_results(tmp_path, monkeypatch):
    def fake_jina(self, query, n):
        return [{"title": "t", "url": "https://example.com", "snippet": "s"}]

    monkeypatch.setattr(fetch_mod.WebHelper, "_search_jina", fake_jina)
    helper = _helper(tmp_path, jina_api_key="fake-key", brave_api_key="fake-brave")
    results = helper.search("apartment permits")
    assert results[0]["url"] == "https://example.com"
    assert helper.counts.jina == 1
    assert helper.counts.brave == 0


def test_search_falls_back_to_brave_when_jina_is_down(tmp_path, monkeypatch):
    def fake_jina(self, query, n):
        raise OSError("connection refused")

    def fake_brave(self, query, n):
        return [{"title": "b", "url": "https://brave-result.example", "snippet": ""}]

    monkeypatch.setattr(fetch_mod.WebHelper, "_search_jina", fake_jina)
    monkeypatch.setattr(fetch_mod.WebHelper, "_search_brave", fake_brave)
    helper = _helper(tmp_path, jina_api_key="fake-key", brave_api_key="fake-brave")
    results = helper.search("apartment permits")
    assert results[0]["url"] == "https://brave-result.example"
    assert helper.counts.jina == 1
    assert helper.counts.brave == 1


def test_search_falls_back_to_brave_when_jina_returns_nothing(tmp_path, monkeypatch):
    def fake_jina(self, query, n):
        return []

    def fake_brave(self, query, n):
        return [{"title": "b", "url": "https://brave-result.example", "snippet": ""}]

    monkeypatch.setattr(fetch_mod.WebHelper, "_search_jina", fake_jina)
    monkeypatch.setattr(fetch_mod.WebHelper, "_search_brave", fake_brave)
    helper = _helper(tmp_path, jina_api_key="fake-key", brave_api_key="fake-brave")
    results = helper.search("apartment permits")
    assert results and helper.counts.brave == 1


def test_search_returns_nothing_without_any_keys(tmp_path):
    helper = _helper(tmp_path, jina_api_key=None, brave_api_key=None)
    assert helper.search("apartment permits") == []
    assert helper.counts.jina == 0
    assert helper.counts.brave == 0


def test_search_falls_back_to_brave_when_jina_results_are_junk(tmp_path, monkeypatch):
    def fake_jina(self, query, n):
        # Junk-style results: unrelated Wikipedia hits that ignore the query.
        return [
            {"title": "Rivertown (mythology)", "url": "https://en.wikipedia.org/wiki/Rivertown", "snippet": "A bird."},
            {"title": "Skybird", "url": "https://en.wikipedia.org/wiki/Skybird", "snippet": "Also a bird."},
        ]

    def fake_brave(self, query, n):
        return [{"title": "Building Permits Portal", "url": "https://city.example/permits", "snippet": ""}]

    monkeypatch.setattr(fetch_mod.WebHelper, "_search_jina", fake_jina)
    monkeypatch.setattr(fetch_mod.WebHelper, "_search_brave", fake_brave)
    helper = _helper(tmp_path, jina_api_key="fake-key", brave_api_key="fake-brave")
    results = helper.search('"Rivertown" building permits open data')
    assert results[0]["url"] == "https://city.example/permits"
    assert helper.counts.brave == 1
    assert helper.junk_jina == 1


def test_search_keeps_jina_results_that_match_the_query(tmp_path, monkeypatch):
    def fake_jina(self, query, n):
        return [{"title": "City of Rivertown Building Permits", "url": "https://rivertown.gov/permits", "snippet": "apartment permit data"}]

    monkeypatch.setattr(fetch_mod.WebHelper, "_search_jina", fake_jina)
    helper = _helper(tmp_path, jina_api_key="fake-key", brave_api_key="fake-brave")
    results = helper.search("Rivertown building permits open data")
    assert results[0]["url"] == "https://rivertown.gov/permits"
    assert helper.counts.brave == 0
    assert helper.junk_jina == 0


def test_search_skips_brave_over_monthly_cap(tmp_path, monkeypatch):
    def fake_jina(self, query, n):
        return []

    calls = []

    def fake_brave(self, query, n):
        calls.append(query)
        return [{"title": "b", "url": "https://brave-result.example", "snippet": ""}]

    monkeypatch.setattr(fetch_mod.WebHelper, "_search_jina", fake_jina)
    monkeypatch.setattr(fetch_mod.WebHelper, "_search_brave", fake_brave)
    helper = _helper(
        tmp_path,
        jina_api_key="fake-key",
        brave_api_key="fake-brave",
        brave_usage=_FakeBraveUsage(under_cap=False),
    )
    results = helper.search("apartment permits")
    assert results == []
    assert calls == []
    assert helper.counts.brave == 0


def test_fetch_caches_page_and_never_refetches(tmp_path):
    calls = []

    def fetcher(url):
        calls.append(url)
        return "<html>ok</html>"

    helper = _helper(tmp_path, jina_api_key=None, brave_api_key=None, page_fetchers=[fetcher])
    r1 = helper.fetch("https://example.com/page")
    r2 = helper.fetch("https://example.com/page")
    assert r1.ok and not r1.from_cache
    assert r2.ok and r2.from_cache
    assert calls == ["https://example.com/page"]  # fetcher only called once


def test_fetch_skips_site_after_three_blocks(tmp_path):
    def blocked_fetcher(url):
        return "<html>Access Denied - captcha required</html>"

    helper = _helper(tmp_path, jina_api_key=None, brave_api_key=None, page_fetchers=[blocked_fetcher])
    for _ in range(fetch_mod.BLOCK_LIMIT - 1):
        r = helper.fetch("https://blocked.example/a")
        assert not r.ok
        assert r.skipped_reason == "blocked"

    r = helper.fetch("https://blocked.example/b")
    assert not r.ok
    assert "blocked 3 times" in r.skipped_reason

    # A 4th URL on the same site is skipped immediately, no fetcher call.
    calls_before = []

    def counting_fetcher(url):
        calls_before.append(url)
        return "<html>Access Denied</html>"

    helper._page_fetchers = [counting_fetcher]
    r = helper.fetch("https://blocked.example/c")
    assert not r.ok
    assert calls_before == []


def test_fetch_falls_through_fetcher_chain(tmp_path):
    def crawl4ai_fails(url):
        return None

    def scrapling_blocked(url):
        return "<html>please solve the captcha to continue</html>"

    def playwright_succeeds(url):
        return "<html>real content</html>"

    helper = _helper(
        tmp_path,
        jina_api_key=None,
        brave_api_key=None,
        page_fetchers=[crawl4ai_fails, scrapling_blocked, playwright_succeeds],
    )
    r = helper.fetch("https://example.com/chain")
    assert r.ok
    assert r.html == "<html>real content</html>"


def test_brave_usage_tracks_calls_by_month(tmp_path):
    usage_path = tmp_path / "brave-usage.json"
    usage = fetch_mod.BraveUsage(path=usage_path)
    assert usage.count_this_month() == 0
    assert usage.under_cap()
    usage.record_call()
    usage.record_call()
    assert usage.count_this_month() == 2

    usage2 = fetch_mod.BraveUsage(path=usage_path)
    assert usage2.count_this_month() == 2


def test_brave_usage_hits_cap(tmp_path):
    usage_path = tmp_path / "brave-usage.json"
    usage = fetch_mod.BraveUsage(path=usage_path)
    for _ in range(fetch_mod.BRAVE_MONTHLY_CAP):
        usage.record_call()
    assert not usage.under_cap()


def test_fetch_from_several_threads_respects_same_site_gap(tmp_path):
    """S1: run.py now fetches several records' pages at once (thread pool).
    Two threads hitting the same site must still be >= site_gap_s apart --
    proves `_respect_gap`'s lock/reserve pattern actually serializes visits
    instead of both threads reading "no recent visit" and firing together."""
    import threading
    import time

    visit_times = []
    lock = threading.Lock()

    def fetcher(url):
        with lock:
            visit_times.append(time.monotonic())
        return "<html>ok</html>"

    helper = fetch_mod.WebHelper(
        cache_dir=tmp_path, jina_api_key=None, brave_api_key=None,
        page_fetchers=[fetcher], site_gap_s=0.2,
    )
    urls = [f"https://same-site.example/page{i}" for i in range(4)]
    threads = [threading.Thread(target=helper.fetch, args=(u,)) for u in urls]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    visit_times.sort()
    assert len(visit_times) == 4
    gaps = [b - a for a, b in zip(visit_times, visit_times[1:])]
    assert all(gap >= 0.19 for gap in gaps)  # small slack for scheduling jitter


def test_fetch_block_counts_are_race_free_across_threads(tmp_path):
    """Many concurrent blocked fetches to the same site must still trip
    BLOCK_LIMIT exactly -- a lost increment under a race would let the site
    keep being retried past the limit."""
    import threading

    def blocked_fetcher(url):
        return "<html>Access Denied</html>"

    helper = fetch_mod.WebHelper(
        cache_dir=tmp_path, jina_api_key=None, brave_api_key=None,
        page_fetchers=[blocked_fetcher], site_gap_s=0.0,
    )
    urls = [f"https://blocked-concurrent.example/{i}" for i in range(10)]
    results = [None] * len(urls)

    def _run(i, u):
        results[i] = helper.fetch(u)

    threads = [threading.Thread(target=_run, args=(i, u)) for i, u in enumerate(urls)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    site = fetch_mod._site_key(urls[0])
    assert helper._skipped[site] == f"blocked {fetch_mod.BLOCK_LIMIT} times"
    assert sum(1 for r in results if not r.ok) == len(urls)
