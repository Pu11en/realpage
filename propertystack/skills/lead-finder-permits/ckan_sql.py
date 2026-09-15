"""T3: a thin CKAN datastore_search_sql adapter so find_upcoming's generic
engine (built for Socrata JSON lists and ArcGIS FeatureServer {features:[]}
responses) can also read a CKAN portal's SQL endpoint.

CKAN's `datastore_search_sql` action wraps its rows in
`{"result": {"records": [...]}}` rather than either shape find_upcoming's
own `_fetch_rows` already understands, so this module hands find_upcoming a
plain http_get that unwraps the envelope itself -- find_upcoming and its
tests are untouched; no place names live here, only the generic unwrap.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Callable

HttpGet = Callable[[str], object]


def ckan_sql_http_get(action_url: str, sql: str, real_http_get: HttpGet | None = None) -> HttpGet:
    """Return a zero-argument-effective http_get: find_upcoming calls
    `http_get(endpoint)` with the recipe's `endpoint` value (a CKAN
    `datastore_search_sql` action URL, for a ckan-sql recipe), but the
    actual query text lives in the recipe's own `sql` field, since a
    CKAN SQL query is not itself a fetchable URL the way a Socrata/ArcGIS
    endpoint is -- this closure ignores the `endpoint` argument it's
    called with and always runs `sql` against `action_url`, unwrapping
    CKAN's `{"result": {"records": [...]}}` envelope down to a plain list
    so find_upcoming's own `_fetch_rows` sees the same shape it already
    handles from Socrata. `real_http_get` defaults to a plain urllib GET
    (with a UA header, matching every other lead-finder* live fetch) --
    injected in tests."""

    def default_get(url: str):
        req = urllib.request.Request(url, headers={"User-Agent": "propertystack-live-self-test"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())

    fetch = real_http_get or default_get

    def http_get(_endpoint: str):
        url = action_url + "?" + urllib.parse.urlencode({"sql": sql})
        data = fetch(url)
        if isinstance(data, dict):
            result = data.get("result", {})
            return result.get("records", [])
        return []

    return http_get
