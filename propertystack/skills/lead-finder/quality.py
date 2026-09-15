"""F9: quality alarms.

After a run, compare the final LeadRecords against the state's hand-built
answer key (propertystack/answer-keys/<state>.json, from F6) and check
completeness (units/website/software/phone), and write the result as
quality.json in the run folder. A run below the bar is marked "failed
quality" so run.py must not build it into the site.

Bar (from the plan): answer-key recall >= 60%, software correct on >= 80%
of key buildings; existing buildings (leasing/sold) need website on >= 70%,
a software verdict on >= 70%, phone on >= 50%; not-yet-built projects
(permitted/under construction) need software == "not picked yet" correct,
and a developer/owner name + office phone on >= 50%.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from record import LeadRecord, normalize_address  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
ANSWER_KEYS_DIR = REPO_ROOT / "propertystack" / "answer-keys"

EXISTING_STAGES = {"leasing", "sold"}
NOT_YET_BUILT_STAGES = {"permitted", "under construction"}

RECALL_BAR = 0.60
SOFTWARE_ACCURACY_BAR = 0.80
EXISTING_WEBSITE_BAR = 0.70
EXISTING_SOFTWARE_BAR = 0.70
EXISTING_PHONE_BAR = 0.50
NOT_YET_BUILT_CONTACT_BAR = 0.50


def load_answer_key(state: str, answer_keys_dir: Path | None = None) -> dict | None:
    path = (answer_keys_dir or ANSWER_KEYS_DIR) / f"{state.lower()}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _match_record(key_entry: dict, records: list[LeadRecord]) -> LeadRecord | None:
    """A record counts as the same building as an answer-key entry if their
    normalized addresses match, or (no address on either side) their names
    match case-insensitively -- same rule merge.py uses for de-duping."""
    key_addr = normalize_address(key_entry.get("address", ""))
    key_name = (key_entry.get("name") or "").strip().lower()
    for record in records:
        if key_addr and normalize_address(record.address) == key_addr:
            return record
        if not key_addr and key_name and record.name.strip().lower() == key_name:
            return record
    return None


def _pct(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def check_quality(state: str, records: list[LeadRecord], cities_with_source: int,
                   total_cities: int, answer_keys_dir: Path | None = None,
                   single_city: bool = False) -> dict:
    """Compute the quality report for a finished run. Returns a dict (also
    written as quality.json) with `passed: bool` and every metric behind it.

    `single_city=True` (a run scoped to one city with `--city`) still reports
    answer-key recall against the whole state's key, but never fails the run
    on it -- the plan judges recall for the whole state only."""
    total_leads = len(records)

    with_units = sum(1 for r in records if r.units is not None)
    with_website = sum(1 for r in records if r.website)
    with_software = sum(1 for r in records if r.software not in ("unknown", ""))
    with_phone = sum(1 for r in records if r.office_phone)

    existing = [r for r in records if r.stage in EXISTING_STAGES]
    not_yet_built = [r for r in records if r.stage in NOT_YET_BUILT_STAGES]

    existing_website_pct = _pct(sum(1 for r in existing if r.website), len(existing))
    existing_software_pct = _pct(
        sum(1 for r in existing if r.software not in ("unknown", "")), len(existing)
    )
    existing_phone_pct = _pct(sum(1 for r in existing if r.office_phone), len(existing))

    not_yet_built_software_correct = sum(
        1 for r in not_yet_built if r.software == "not picked yet"
    )
    not_yet_built_software_pct = _pct(not_yet_built_software_correct, len(not_yet_built))
    not_yet_built_contact_pct = _pct(
        sum(1 for r in not_yet_built if r.developer and r.office_phone), len(not_yet_built)
    )

    answer_key = load_answer_key(state, answer_keys_dir)
    key_leads = answer_key["leads"] if answer_key else []
    found = 0
    software_checked = 0
    software_correct = 0
    for entry in key_leads:
        match = _match_record(entry, records)
        if match is not None:
            found += 1
            key_software = entry.get("software")
            if key_software:
                software_checked += 1
                if match.software == key_software:
                    software_correct += 1

    recall_pct = _pct(found, len(key_leads))
    software_accuracy_pct = _pct(software_correct, software_checked)

    reasons = []
    if not key_leads:
        reasons.append("no answer key found for this state")
    if not single_city and recall_pct < RECALL_BAR:
        reasons.append(f"answer-key recall {recall_pct:.0%} < {RECALL_BAR:.0%}")
    if software_checked and software_accuracy_pct < SOFTWARE_ACCURACY_BAR:
        reasons.append(f"software accuracy {software_accuracy_pct:.0%} < {SOFTWARE_ACCURACY_BAR:.0%}")
    if existing and existing_website_pct < EXISTING_WEBSITE_BAR:
        reasons.append(f"existing-building website {existing_website_pct:.0%} < {EXISTING_WEBSITE_BAR:.0%}")
    if existing and existing_software_pct < EXISTING_SOFTWARE_BAR:
        reasons.append(f"existing-building software {existing_software_pct:.0%} < {EXISTING_SOFTWARE_BAR:.0%}")
    if existing and existing_phone_pct < EXISTING_PHONE_BAR:
        reasons.append(f"existing-building phone {existing_phone_pct:.0%} < {EXISTING_PHONE_BAR:.0%}")
    if not_yet_built and not_yet_built_contact_pct < NOT_YET_BUILT_CONTACT_BAR:
        reasons.append(
            f"not-yet-built developer+phone {not_yet_built_contact_pct:.0%} < {NOT_YET_BUILT_CONTACT_BAR:.0%}"
        )

    passed = not reasons

    return {
        "state": state,
        "passed": passed,
        "fail_reasons": reasons,
        "total_leads": total_leads,
        "cities_with_source_pct": _pct(cities_with_source, total_cities),
        "pct_with_units": _pct(with_units, total_leads),
        "pct_with_website": _pct(with_website, total_leads),
        "pct_with_software": _pct(with_software, total_leads),
        "pct_with_phone": _pct(with_phone, total_leads),
        "answer_key_recall": recall_pct,
        "answer_key_found": found,
        "answer_key_total": len(key_leads),
        "software_accuracy": software_accuracy_pct,
        "software_checked": software_checked,
        "software_correct": software_correct,
        "existing_buildings": {
            "count": len(existing),
            "website_pct": existing_website_pct,
            "software_pct": existing_software_pct,
            "phone_pct": existing_phone_pct,
        },
        "not_yet_built": {
            "count": len(not_yet_built),
            "software_not_picked_pct": not_yet_built_software_pct,
            "developer_and_phone_pct": not_yet_built_contact_pct,
        },
    }


def write_quality_json(run_folder_path: Path, report: dict) -> Path:
    out = run_folder_path / "quality.json"
    out.write_text(json.dumps(report, indent=1))
    return out
