"""S5: permit_only.py's free data-first extras -- a county sales file must
be usable for (a) sold-building leads and (b) filling a new permit's owner
by address, without ever re-downloading the zip file more than once per run
(the parcel file is ~100MB+ and only `default_fetch_rows` touches the
network, so this stays offline via a fake `fetch_rows`)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import permit_only  # noqa: E402


def test_cached_fetch_rows_only_calls_the_real_fetch_once_per_url(monkeypatch):
    calls = []

    def fake_default_fetch_rows(source):
        calls.append(source["url"])
        return [{"row": 1}]

    monkeypatch.setattr(permit_only, "default_fetch_rows", fake_default_fetch_rows)
    cache = {}
    source = {"url": "https://example.test/parcels.zip"}

    first = permit_only._cached_fetch_rows(source, cache)
    second = permit_only._cached_fetch_rows(source, cache)

    assert first == second == [{"row": 1}]
    assert calls == ["https://example.test/parcels.zip"]


def test_cached_fetch_rows_fetches_each_distinct_url_separately(monkeypatch):
    monkeypatch.setattr(permit_only, "default_fetch_rows", lambda source: [source["url"]])
    cache = {}

    a = permit_only._cached_fetch_rows({"url": "https://example.test/a.zip"}, cache)
    b = permit_only._cached_fetch_rows({"url": "https://example.test/b.zip"}, cache)

    assert a == ["https://example.test/a.zip"]
    assert b == ["https://example.test/b.zip"]
