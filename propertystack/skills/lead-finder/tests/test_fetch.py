"""Fixture tests for fetch.py -- no network, no real SearXNG/Jina/crawl4ai calls."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fetch as fetch_mod  # noqa: E402


def _helper(tmp_path, searx_search=None, page_fetchers=None, jina_api_key=fetch_mod._UNSET):
    return fetch_mod.WebHelper(
        cache_dir=tmp_path,
        jina_api_key=jina_api_key,
        searx_search=searx_search,
        page_fetchers=page_fetchers,
        site_gap_s=0.0,
    )


def test_search_uses_searxng_when_it_has_results(tmp_path):
    calls = []

    def fake_searx(query, n):
        calls.append(query)
        return [{"title": "t", "url": "https://example.com", "snippet": "s"}]

    helper = _helper(tmp_path, searx_search=fake_searx, jina_api_key="fake-key")
    results = helper.search("apartment permits")
    assert results[0]["url"] == "https://example.com"
    assert helper.counts.searxng == 1
    assert helper.counts.jina == 0


def test_search_falls_back_to_jina_when_searxng_is_down(tmp_path, monkeypatch):
    def fake_searx(query, n):
        raise OSError("connection refused")

    def fake_jina(self, query, n):
        return [{"title": "j", "url": "https://jina-result.example", "snippet": ""}]

    monkeypatch.setattr(fetch_mod.WebHelper, "_search_jina", fake_jina)
    helper = _helper(tmp_path, searx_search=fake_searx, jina_api_key="fake-key")
    results = helper.search("apartment permits")
    assert results[0]["url"] == "https://jina-result.example"
    assert helper.counts.searxng == 0
    assert helper.counts.jina == 1


def test_search_falls_back_to_jina_when_searxng_returns_nothing(tmp_path, monkeypatch):
    def fake_searx(query, n):
        return []

    def fake_jina(self, query, n):
        return [{"title": "j", "url": "https://jina-result.example", "snippet": ""}]

    monkeypatch.setattr(fetch_mod.WebHelper, "_search_jina", fake_jina)
    helper = _helper(tmp_path, searx_search=fake_searx, jina_api_key="fake-key")
    results = helper.search("apartment permits")
    assert results and helper.counts.jina == 1


def test_search_returns_nothing_without_jina_key(tmp_path):
    def fake_searx(query, n):
        return []

    helper = _helper(tmp_path, searx_search=fake_searx, jina_api_key=None)
    assert helper.search("apartment permits") == []
    assert helper.counts.jina == 0


def test_fetch_caches_page_and_never_refetches(tmp_path):
    calls = []

    def fetcher(url):
        calls.append(url)
        return "<html>ok</html>"

    helper = _helper(tmp_path, searx_search=lambda q, n: [], page_fetchers=[fetcher])
    r1 = helper.fetch("https://example.com/page")
    r2 = helper.fetch("https://example.com/page")
    assert r1.ok and not r1.from_cache
    assert r2.ok and r2.from_cache
    assert calls == ["https://example.com/page"]  # fetcher only called once


def test_fetch_skips_site_after_three_blocks(tmp_path):
    def blocked_fetcher(url):
        return "<html>Access Denied - captcha required</html>"

    helper = _helper(tmp_path, searx_search=lambda q, n: [], page_fetchers=[blocked_fetcher])
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
        return "<html>captcha</html>"

    def playwright_succeeds(url):
        return "<html>real content</html>"

    helper = _helper(
        tmp_path,
        searx_search=lambda q, n: [],
        page_fetchers=[crawl4ai_fails, scrapling_blocked, playwright_succeeds],
    )
    r = helper.fetch("https://example.com/chain")
    assert r.ok
    assert r.html == "<html>real content</html>"
