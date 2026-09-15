"""T13: a building page must never show the same source link twice under two
different labels (e.g. "Website" and "State project record" pointing at the
same tdlr.texas.gov URL). Offline: checks the sourceItems() logic in
site/property.html by source inspection, since it's inline page JS with no
Node test runner in this repo."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROPERTY = (ROOT / "site/property.html").read_text()


def test_source_items_dedupes_by_url_not_by_label_pair():
    # The old bug: dedup key included the label, so the same URL survived
    # twice under "Website" and "State project record".
    assert "`${e.label}|${e.url || \"\"}`" not in PROPERTY
    assert 'e.url ? `url|${e.url}` : `label|${e.label}`' in PROPERTY


def test_sources_card_still_includes_website_alongside_saved_sources():
    # The website field must still feed into the same dedup pass as p.sources.
    assert "extra.push(p.proof, p.website)" in PROPERTY
    assert "sourceItems([...(p.sources || []), ...extra])" in PROPERTY


def _fake_source_items(sources_list):
    """Reimplements the fixed JS dedupe logic in Python to verify behavior."""
    seen = set()
    out = []
    for s in sources_list:
        if isinstance(s, dict):
            e = {"label": s.get("label") or "Source", "url": s.get("url")}
        elif not s:
            e = None
        else:
            e = {"label": "Website", "url": s} if s.startswith("http") else {"label": s, "url": None}
        key = f"url|{e['url']}" if e and e.get("url") else (f"label|{e['label']}" if e else "")
        if e and key not in seen:
            seen.add(key)
            out.append(e)
    return out


def test_same_url_under_two_labels_collapses_to_one_entry():
    same_url = "https://www.tdlr.texas.gov/TABS/Search/Project/TABS2025001287"
    sources = [{"label": "State project record", "url": same_url}]
    website = same_url
    items = _fake_source_items(sources + [website])
    matching = [i for i in items if i["url"] == same_url]
    assert len(matching) == 1
    assert matching[0]["label"] == "State project record"


def test_different_urls_still_both_show():
    items = _fake_source_items([
        {"label": "State project record", "url": "https://www.tdlr.texas.gov/a"},
        "https://example.com/leasing",
    ])
    urls = {i["url"] for i in items}
    assert urls == {"https://www.tdlr.texas.gov/a", "https://example.com/leasing"}
