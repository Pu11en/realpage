"""Record text must be escaped before it reaches innerHTML.

Found 2026-09-26 reviewing the browser code with the ruleset from
alibaba/open-code-review, which prohibits putting unescaped values into innerHTML.

Not hypothetical, and not yet visible either. 122 values in the live data carry a bare "&" --
"MADERA ARMSTRONG LLC &", "Near Corner of Willowbrook St. & Valley Mills Dr." -- and 16 an
apostrophe, "L'ABRI APARTMENTS". None currently carry < > or ", which is exactly why nothing
looked broken. But these are county and city records nobody here controls, and the first
building name published with a quote in it would break every row on the page.

Checked statically, because there is no Node on this machine to run the page. Static is the
right shape anyway: it fails on the line that introduces the problem.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SITE = ROOT / "site"

# Fields that come from the public records, so their contents are not ours to trust.
RECORD_FIELDS = (
    "property", "community", "address", "subArea", "city", "stateLabel", "buyer",
    "developer", "software", "officePhone", "signal", "signalType", "why", "id",
    "propertyId", "areaSlug", "owner", "websiteConfidence",
)
# Interpolations that are not raw record text: numbers, computed markup, and helpers that
# escape their own output.
SAFE_CALLS = (
    "esc(", "link(", "vendorPill(", "sourceLinks(", "contactHtml(", "signalHtml(",
    "leadSoftwareHtml(", "fmtDate(", "scoreBadgeColor(", "scoreClass(", "toLocaleString(",
)

PAGES = ("index.html", "property.html")

# An interpolation whose whole value *is* record text: field reads, quoted fallbacks and
# `||`, nothing else.
VALUE_ONLY = re.compile(r'^\s*[\w.]+(?:\s*\|\|\s*(?:[\w.]+|"[^"]*"|\'[^\']*\'))*\s*$')
INTERPOLATION = re.compile(r"\$\{([^}]*)\}")
A_RECORD_FIELD = re.compile(r"\b\w+\.(" + "|".join(RECORD_FIELDS) + r")\b")


def js_of(name: str) -> str:
    return (SITE / name).read_text(encoding="utf-8")


def test_one_shared_escape_helper_exists_in_app_js():
    """index.html and property.html each used to define their own copy, and used it only on
    source links -- never on the rows carrying the record text."""
    app = (SITE / "js" / "app.js").read_text(encoding="utf-8")
    assert "function esc(value)" in app
    for char, entity in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"),
                         ('"', "&quot;"), ("'", "&#39;")):
        assert entity in app, f"esc() does not encode {char}"
    assert '<script src="js/app.js"></script>' in js_of("index.html")


@pytest.mark.parametrize("name", PAGES)
def test_no_record_field_is_interpolated_raw(name):
    """${l.property} inside a template string is the defect; ${esc(l.property)} is not.

    Deliberately narrow. A field used in a condition is a test rather than output, and the
    emitted branches of a ternary are separate interpolations this same loop already checks.
    A field inside a call is that call's business. Both shapes produced false alarms on the
    first run, and a check that cries wolf is a check people switch off.
    """
    raw = []
    for line_no, line in enumerate(js_of(name).splitlines(), start=1):
        # document.title takes a plain string, not markup: escaping there would show a
        # visitor "&amp;" in their browser tab.
        if "document.title" in line:
            continue
        for match in INTERPOLATION.finditer(line):
            expr = match.group(1)
            if any(call in expr for call in SAFE_CALLS):
                continue
            if not VALUE_ONLY.match(expr):
                continue
            if A_RECORD_FIELD.search(expr):
                raw.append(f"{name}:{line_no}  ${{{expr.strip()[:70]}}}")
    assert not raw, "record text reaching innerHTML unescaped:\n  " + "\n  ".join(raw)


def test_the_check_above_would_actually_catch_the_bug_it_is_for():
    """A guard this narrow is worth proving. These are the exact shapes that shipped."""
    for bad in ("l.property", "l.propertyId || l.id", " l.city ", 'l.buyer || "not listed"'):
        assert VALUE_ONLY.match(bad) and A_RECORD_FIELD.search(bad), bad
    for fine in ("!l.software && !sold ? `x` : `y`", "encodeURIComponent(tr.dataset.id)",
                 "i + 1", "s.leads.toLocaleString()"):
        flagged = (VALUE_ONLY.match(fine) and A_RECORD_FIELD.search(fine)
                   and not any(c in fine for c in SAFE_CALLS))
        assert not flagged, fine


def test_the_city_dropdown_escapes_the_name_in_both_places():
    """A city name lands in an attribute and in the option text; a quote in either would
    break the whole select."""
    line = next(l for l in js_of("index.html").splitlines() if "All cities</option>" in l)
    assert line.count("esc(c)") == 2, line.strip()


def test_vendor_pill_escapes_the_vendor_name():
    app = (SITE / "js" / "app.js").read_text(encoding="utf-8")
    pill = app.split("function vendorPill", 1)[1].split("\n}\n", 1)[0]
    assert "${esc(vendor)}" in pill, "vendorPill puts the vendor name into markup raw"
