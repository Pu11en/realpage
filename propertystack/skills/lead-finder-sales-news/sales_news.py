"""lead-finder 4.3: find-sales-news -- apartment building sales, any area.

SearXNG news search covers the full 24-month window (the plan's normal free-first
search). GDELT's DOC API (https://api.gdeltproject.org/api/v2/doc/doc) is queried in
addition, not instead -- it only indexes roughly the last 3 months, so it's a
freshness add-on that can surface a sale before it shows up in a general web search.
Both feed the same filter: only sales of 20+ unit apartment buildings in the last 24
months become leads (stage "sold"); anything missing a date or a unit count, or a
too-small deal, is dropped -- never guessed.

No place names anywhere in this file -- city/area are always caller-supplied data.
"""
from __future__ import annotations

import datetime
import json
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "propertystack" / "skills" / "lead-finder"))

from record import LeadRecord, Source  # noqa: E402

SearchFn = Callable[[str], list[dict]]
GdeltFetchFn = Callable[[str], bytes]

MIN_UNITS = 20
MONTHS = 24

UNITS_RE = re.compile(r"(\d{2,4})[- ]unit", re.I)
BUYER_RE = re.compile(
    r"(?:acquired by|sold to|purchased by)\s+([A-Z][\w&.,'\- ]{2,60}?)(?:\s+for\b|\s+in a\b|[.,]|$)",
    re.I,
)
ACQUIRER_RE = re.compile(r"([A-Z][\w&.,'\- ]{2,60}?)\s+(?:acquires|buys|purchases)\b")
SALE_KEYWORDS_RE = re.compile(r"\b(sold|acquisition|acquires|acquired|purchased)\b", re.I)


def news_query(city: str) -> str:
    return f'"{city}" apartments sold OR acquires OR acquisition units'


def gdelt_url(query: str) -> str:
    return "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode(
        {"query": query, "mode": "artlist", "format": "json"}
    )


def _parse_date(value: str) -> datetime.date | None:
    if not value:
        return None
    value = value.strip()
    # GDELT seendate: "20260101T120000Z"
    m = re.match(r"^(\d{4})(\d{2})(\d{2})T", value)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _months_ago(date: datetime.date, today: datetime.date) -> float:
    return (today.year - date.year) * 12 + (today.month - date.month)


def extract_buyer(text: str) -> str:
    m = BUYER_RE.search(text)
    if m:
        return m.group(1).strip()
    m = ACQUIRER_RE.search(text)
    if m:
        return m.group(1).strip()
    return ""


def hit_to_record(
    title: str,
    snippet: str,
    url: str,
    city: str,
    area: str,
    date: datetime.date | None,
    min_units: int = MIN_UNITS,
) -> LeadRecord | None:
    """A news title/snippet -> a sold-stage LeadRecord, or None.

    Requires: a sale keyword, a units count >= min_units, and a real date --
    never guesses any of the three.
    """
    text = f"{title} {snippet}"
    if not SALE_KEYWORDS_RE.search(text):
        return None
    m = UNITS_RE.search(text)
    if not m:
        return None
    units = int(m.group(1))
    if units < min_units:
        return None
    if date is None:
        return None
    return LeadRecord(
        area=area,
        city=city,
        name=title.strip(),
        units=units,
        stage="sold",
        sale_date=date.isoformat(),
        buyer=extract_buyer(text),
        why="apartment sale reported in the news",
        links={"news": url},
        sources=[
            Source(fact="sale_date", url=url).__dict__,
            Source(fact="units", url=url).__dict__,
        ],
    )


def find_sales_news(
    city: str,
    area: str,
    search_fn: SearchFn,
    gdelt_fetch_fn: GdeltFetchFn | None = None,
    today: datetime.date | None = None,
    months: int = MONTHS,
    min_units: int = MIN_UNITS,
) -> list[LeadRecord]:
    """SearXNG news search (full window) + GDELT DOC API (last ~3 months add-on) ->
    sold-stage LeadRecords for one city, deduped by article URL."""
    today = today or datetime.date.today()
    records: list[LeadRecord] = []
    seen_urls: set[str] = set()

    for result in search_fn(news_query(city)):
        url = result.get("url", "")
        if not url or url in seen_urls:
            continue
        date = _parse_date(result.get("date", "") or result.get("published", ""))
        if date is None or date > today or _months_ago(date, today) > months:
            continue
        rec = hit_to_record(result.get("title", ""), result.get("snippet", ""), url, city, area, date, min_units)
        if rec is not None:
            records.append(rec)
            seen_urls.add(url)

    if gdelt_fetch_fn is not None:
        try:
            raw = gdelt_fetch_fn(gdelt_url(news_query(city)))
            data = json.loads(raw)
        except (json.JSONDecodeError, OSError, TypeError):
            data = {}
        for article in data.get("articles", []):
            url = article.get("url", "")
            if not url or url in seen_urls:
                continue
            date = _parse_date(article.get("seendate", ""))
            if date is None or date > today or _months_ago(date, today) > months:
                continue
            rec = hit_to_record(article.get("title", ""), "", url, city, area, date, min_units)
            if rec is not None:
                records.append(rec)
                seen_urls.add(url)

    return records


if __name__ == "__main__":
    import argparse
    import urllib.request

    p = argparse.ArgumentParser()
    p.add_argument("--city", required=True)
    p.add_argument("--area", required=True)
    args = p.parse_args()

    sys.path.insert(0, str(ROOT / "tooling"))
    import searx_search  # tooling/searx_search.py

    def _gdelt_fetch(url: str) -> bytes:
        with urllib.request.urlopen(url, timeout=20) as r:
            return r.read()

    records = find_sales_news(args.city, args.area, searx_search.search, _gdelt_fetch)
    print(json.dumps([r.to_dict() for r in records], indent=1))
    print(f"{len(records)} sale leads for {args.city}, {args.area}")
