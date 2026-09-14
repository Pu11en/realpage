"""Part 4.1/4.2 -- which leasing software a project's website runs.

Loads our own Wappalyzer-format rules from rules.json (not the GPL webappanalyzer
technologies file -- written from scratch for this project) and merges the same
detection approach proven in tooling/pms_detect.py: look for a known vendor host
inside a resident/login/pay/apply-type link on the homepage first (signal=portal,
the strongest evidence); if none, follow up to 3 such links one hop and re-check
(signal=hop-portal); if still none, fall back to a vendor host anywhere on the
page, e.g. an asset CDN (signal=asset); if still none, try a plain-text match
against the rules' html patterns (signal=text, the cheapest and weakest signal);
if still none, check known in-house portals (UDR, Camden) as a last resort.

Part 4.2: a `portal`, `asset` or `text` verdict is only fetched from one page, so
before it's final we fetch a *second* page (the resident-portal link itself, or
another link on the homepage if the proof link isn't a separate page) and check
it still shows the same vendor. If the second page disagrees, can't be fetched,
or there is no second page to check, the verdict drops to `unknown` with
`unconfirmed`. `hop-portal` already required two pages to agree (the homepage
link plus the page it points to), so it's confirmed by construction.

"Cheap page check first, full browser only if unclear" is inherited from
WebHelper.fetch() (propertystack/skills/lead-finder/fetch.py), which already
tries crawl4ai before falling back to Scrapling/Playwright only when a page
looks blocked -- this module never opens a browser directly.

No place names anywhere in this module -- areas/cities are always caller-supplied
data via the LeadRecord, never literals here.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEAD_FINDER = HERE.parents[0] / "lead-finder"
if str(LEAD_FINDER) not in sys.path:
    sys.path.insert(0, str(LEAD_FINDER))

RULES_PATH = HERE / "rules.json"

PORTAL = re.compile(r"resident|login|portal|pay|userlogin|onlineleasing|apply", re.I)
HOP = re.compile(r"resident|login|pay-?rent|portal", re.I)
SKIP = re.compile(r"facebook|onetrust|cookie|google|\.(png|jpe?g|svg|css|js|pdf)(\?|$)", re.I)
URL_RE = re.compile(r"https?://[^\s)\"'<>]+")


def load_rules(path: Path = RULES_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _vendor_url_patterns(rules: dict) -> list[tuple[str, re.Pattern]]:
    return [(name, re.compile(spec["url"], re.I)) for name, spec in rules["technologies"].items() if spec.get("url")]


def _vendor_html_patterns(rules: dict) -> list[tuple[str, re.Pattern]]:
    return [(name, re.compile(spec["html"], re.I)) for name, spec in rules["technologies"].items() if spec.get("html")]


def classify_links(html: str, rules: dict) -> tuple[dict, str]:
    """Look for vendor hosts among the page's links. Returns (hits, kind)."""
    urls = URL_RE.findall(html)
    vendor_urls = _vendor_url_patterns(rules)
    for strong in (True, False):  # portal-type links first, then any vendor host
        hits: dict[str, str] = {}
        for u in urls:
            if strong and not PORTAL.search(u):
                continue
            for vendor, pat in vendor_urls:
                if pat.search(u):
                    hits.setdefault(vendor, u)
        if hits:
            return hits, "portal" if strong else "asset"
    return {}, ""


def classify_text(html: str, rules: dict) -> str | None:
    """Cheap fallback: plain-text vendor mention with no matching link."""
    for vendor, pat in _vendor_html_patterns(rules):
        if pat.search(html):
            return vendor
    return None


def classify_in_house(html: str, rules: dict) -> tuple[str, str] | tuple[None, None]:
    for name, pattern in rules.get("in_house", {}).items():
        m = re.search(pattern, html, re.I)
        if m:
            return f"in-house:{name}", m.group(0)
    return None, None


def _second_page_url(html: str, primary_url: str, proof_url: str) -> str | None:
    """Pick another page on the site to double-check a one-page verdict."""
    if proof_url and proof_url != primary_url and not SKIP.search(proof_url):
        return proof_url
    for u in dict.fromkeys(URL_RE.findall(html)):
        if u != primary_url and not SKIP.search(u):
            return u
    return None


def _confirm_on_second_page(vendor: str, html: str, primary_url: str, proof_url: str, web, rules: dict) -> bool:
    """Part 4.2: a portal/asset/text verdict is only good once a second page agrees."""
    second_url = _second_page_url(html, primary_url, proof_url)
    if not second_url:
        return False
    result = web.fetch(second_url)
    if not result.ok:
        return False
    hits, _ = classify_links(result.html, rules)
    if vendor in hits:
        return True
    return classify_text(result.html, rules) == vendor


def detect_software(url: str, web, rules: dict | None = None) -> dict:
    """Fetch a project's website (via the shared WebHelper) and classify its software.

    Returns {"software": ..., "signal": ..., "proof_url": ..., "unknown_reason": ...}.
    """
    rules = rules or load_rules()
    if not url:
        return {"software": "unknown", "signal": "none", "proof_url": "", "unknown_reason": "no-website"}

    result = web.fetch(url)
    if not result.ok:
        reason = result.skipped_reason or "fetch-failed"
        return {"software": "unknown", "signal": "none", "proof_url": "", "unknown_reason": reason}

    html = result.html
    hits, kind = classify_links(html, rules)
    if kind == "portal":
        vendor = next(iter(hits))
        proof_url = hits[vendor]
        if not _confirm_on_second_page(vendor, html, url, proof_url, web, rules):
            return {"software": "unknown", "signal": "none", "proof_url": "", "unknown_reason": "unconfirmed"}
        return {"software": vendor, "signal": "portal", "proof_url": proof_url, "unknown_reason": ""}

    hop_links = [u for u in dict.fromkeys(URL_RE.findall(html)) if HOP.search(u) and not SKIP.search(u)][:3]
    for link in hop_links:
        hop_result = web.fetch(link)
        if not hop_result.ok:
            continue
        h2, _ = classify_links(hop_result.html, rules)
        if h2:
            vendor = next(iter(h2))
            # Two pages (the homepage link and the page it points to) already agree.
            return {"software": vendor, "signal": "hop-portal", "proof_url": h2[vendor], "unknown_reason": ""}

    if kind == "asset" and hits:
        vendor = next(iter(hits))
        proof_url = hits[vendor]
        if not _confirm_on_second_page(vendor, html, url, proof_url, web, rules):
            return {"software": "unknown", "signal": "none", "proof_url": "", "unknown_reason": "unconfirmed"}
        return {"software": vendor, "signal": "asset", "proof_url": proof_url, "unknown_reason": ""}

    text_vendor = classify_text(html, rules)
    if text_vendor:
        if not _confirm_on_second_page(text_vendor, html, url, url, web, rules):
            return {"software": "unknown", "signal": "none", "proof_url": "", "unknown_reason": "unconfirmed"}
        return {"software": text_vendor, "signal": "text", "proof_url": url, "unknown_reason": ""}

    name, proof = classify_in_house(html, rules)
    if name:
        return {"software": name, "signal": "portal", "proof_url": proof, "unknown_reason": ""}

    return {"software": "unknown", "signal": "none", "proof_url": "", "unknown_reason": "no-portal-link"}
