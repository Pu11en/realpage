"""Permits that mention an apartment but are not a new apartment building.

Permit feeds often say "apartment" for work on an existing complex: a pool, a
carport, a stair remodel, a repair, re-roof, a fence, or a single garage
apartment behind a house. None of those is a lead. Used by the permit sources
(lead-finder-permits) and again by site/data/build_data.py so leads already
saved in a state's leads.json are dropped on rebuild.

"Structured parking garage" or "Multifamily and Garage" (a real building with
its own garage) is not junk; only a garage *apartment* is.
"""
from __future__ import annotations

import re

JUNK_PERMIT_RE = re.compile(
    r"\b("
    r"swim+(?:ing)?\s+pool|pools?"
    r"|carports?"
    r"|stairs?|stairway|remodel\w*"
    r"|repairs?"
    r"|re-?roof\w*|roof(?:ing)?"
    r"|garage[- ]apartments?"
    r"|fences?"
    r")\b"
    # ...but not a street named that way ("4500 Brentwood Stair Rd")
    r"(?!\s+(?:rd|road|st|street|dr|drive|ave|avenue|blvd|ln|lane|way|pkwy|trl|ct|cir)\b)",
    re.I,
)


def is_junk_permit(*texts: str | None) -> bool:
    """True if any of the given texts (name, description, permit comments)
    describes pool/carport/stair/remodel/repair/roof/garage-apartment work."""
    return any(t and JUNK_PERMIT_RE.search(t) for t in texts)
