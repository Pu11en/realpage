"""lead-finder 4.5: score-leads, any area.

Orders any area's LeadRecords into one ranked list:

1. Active leads (permitted / under construction / leasing), soonest opening first,
   then more units, then a lead whose software isn't already picked over one that's
   on a named competitor. A lead with no opening date ranks after all leads that
   have one, ordered among themselves by permit date (oldest permit first -- it's
   been in the pipeline longest, so likeliest to open soonest).
2. Sold leads, newest sale first.
3. Planned leads, soonest expected opening first, then more units.

Each lead gets a one-line, facts-only `why` built only from that record's own
fields -- no invented facts, no numbers or names that aren't already on the record.

No place names anywhere in this file -- city/area are always caller-supplied data.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skills" / "lead-finder"))

from record import LeadRecord  # noqa: E402

import datetime

ACTIVE_STAGES = {"permitted", "under construction", "leasing"}

# Software rank used only to break ties within a group: a lead where the
# software isn't decided yet is a better sales lead than one already on a
# named competitor, so it sorts first (lower rank number = better).
_UNDECIDED_SOFTWARE = {"", "unknown", "not picked"}


def _software_rank(software: str) -> int:
    return 0 if (software or "").strip().lower() in _UNDECIDED_SOFTWARE else 1


def _group(record: LeadRecord) -> int:
    if record.stage in ACTIVE_STAGES:
        return 0
    if record.stage == "sold":
        return 1
    return 2  # planned (and anything unrecognized falls in last)


def _active_key(record: LeadRecord):
    has_opening = bool(record.opening_date)
    return (
        0 if has_opening else 1,
        record.opening_date if has_opening else "",
        record.permit_date if not has_opening else "",
        -(record.units or 0),
        _software_rank(record.software),
    )


def _to_ordinal(date_str: str) -> int:
    try:
        return datetime.date.fromisoformat(date_str).toordinal()
    except (ValueError, TypeError):
        return 0


def _sold_key(record: LeadRecord):
    has_date = bool(record.sale_date)
    return (0 if has_date else 1, -_to_ordinal(record.sale_date) if has_date else 0)


def _planned_key(record: LeadRecord):
    has_expected = bool(record.opening_date)
    return (
        0 if has_expected else 1,
        record.opening_date if has_expected else "",
        -(record.units or 0),
    )


def _sort_key(record: LeadRecord):
    group = _group(record)
    if group == 0:
        return (group, _active_key(record))
    if group == 1:
        return (group, _sold_key(record))
    return (group, _planned_key(record))


def _why(record: LeadRecord) -> str:
    units_part = f"{record.units} units" if record.units else ""
    if record.stage in ACTIVE_STAGES:
        opens = f"opens {record.opening_date}" if record.opening_date else "opens: not public yet"
        software = (record.software or "unknown").strip().lower()
        pitch = "software not picked yet" if software in _UNDECIDED_SOFTWARE else f"on {record.software} today"
        parts = [record.stage.capitalize(), opens, units_part, pitch]
    elif record.stage == "sold":
        sold = f"Sold {record.sale_date}" if record.sale_date else "Sold"
        buyer = f"to {record.buyer}" if record.buyer else ""
        parts = [sold, buyer, units_part, "new owner may re-pick software"]
    else:
        expected = f"expected {record.opening_date}" if record.opening_date else "expected: not public yet"
        parts = ["Planned", expected, units_part, "software not chosen yet"]
    return " · ".join(p for p in parts if p)


def score_and_rank(records: list[LeadRecord]) -> list[LeadRecord]:
    """Sort records into the plan's group/tiebreak order and fill in `why`.

    Does not mutate the input list order in place beyond what's returned; each
    record's `why` field is overwritten with a facts-only summary built from its
    own fields.
    """
    ranked = sorted(records, key=_sort_key)
    for record in ranked:
        record.why = _why(record)
    return ranked
