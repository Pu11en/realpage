#!/usr/bin/env python3
"""Conservative dedup output builder for the 2026-09-20 Masiate pilot."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
from typing import Any


DEFAULT_INPUT = pathlib.Path(
    "/home/drewp/.local/state/cranesignal/masiate/pilot-20260920-2048/review-input"
)
DEFAULT_OUTPUT = pathlib.Path(
    "/home/drewp/.local/state/cranesignal/masiate/pilot-20260920-2048/finish/dedup"
)


REVIEWED_GROUPS: list[dict[str, Any]] = [
    {
        "canonical_id": "dedup-washington-edward-jones-1504-s-day",
        "member_ids": [
            "washington-brenham-permit-com-new-26-0014",
            "statewide-tdlr-tabs-TABS2026023085",
        ],
        "match_basis": [
            "same county and same address: 1504 S Day Street / 1504 S Day St., Ste 1504",
            "city permit value $181,300 closely matches TDLR estimated cost $181,234",
            "permit scope tenant office buildout aligns with TDLR interior build-out",
        ],
        "conflicts": [
            "project names differ: Lex Investments owner/permit wording versus Edward Jones branch tenant wording",
            "city permit proves permitted work; TDLR proves registration/review status only",
        ],
    },
    {
        "canonical_id": "dedup-washington-water-treatment-1105-s-austin",
        "member_ids": [
            "washington-brenham-permit-com-add-26-0009",
            "statewide-tdlr-tabs-TABS2026006791",
        ],
        "match_basis": [
            "same county and same address: 1105 S Austin Street",
            "both scopes describe rehabilitation/expansion of Brenham water treatment plant",
            "city permit and TDLR both support the same large public works project",
        ],
        "conflicts": [
            "estimated values differ: city permit $28,297,500 versus TDLR $25,770,000",
            "TDLR registration predates the city permit and is not open-bid evidence",
        ],
    },
    {
        "canonical_id": "dedup-washington-redeemer-church-2111-s-blue-bell",
        "member_ids": [
            "washington-brenham-permit-com-new-26-0007",
            "statewide-tdlr-tabs-TABS2026008498",
        ],
        "match_basis": [
            "same county and same address: 2111 S Blue Bell Road",
            "both identify Redeemer Church / Redeemer Church Campus",
            "permit and TDLR scopes both cover exterior/site work around the existing church campus",
        ],
        "conflicts": [
            "city permit specifically records parking lot and sign-wall work; TDLR describes broader interior/exterior modifications",
            "TDLR expected completion is a past/near-term date and does not prove current subcontract availability",
        ],
    },
    {
        "canonical_id": "dedup-washington-grace-community-107-s-saeger",
        "member_ids": [
            "washington-brenham-permit-misc-prkg-26-0018-grace-drainage",
            "statewide-tdlr-tabs-TABS2026022754",
        ],
        "match_basis": [
            "same county and same address: 107 S/South Saeger Street",
            "same $1,000,000 paving/drainage scope",
            "permit identifies Grace Community Fellowship; TDLR identifies Grace Community Church-Brenham",
        ],
        "conflicts": [
            "city permit contractor field says Owner and does not establish open trade packages",
            "TDLR is registration/review evidence only",
        ],
    },
    {
        "canonical_id": "dedup-washington-frost-bank-862-us-290-e",
        "member_ids": [
            "washington-brenham-permit-com-new-26-0011",
            "statewide-tdlr-tabs-TABS2026020346",
        ],
        "match_basis": [
            "same county and same address: 862 US Highway 290 E",
            "both identify Frost/Frost Bank financial center",
            "both describe new ground-up bank construction",
        ],
        "conflicts": [
            "estimated values differ: city permit $7,831,737 versus TDLR $9,000,000",
            "Frost business page says coming 2027 while TDLR lists estimated completion 2027-02-07",
        ],
    },
    {
        "canonical_id": "dedup-washington-moeller-1119-industrial",
        "member_ids": [
            "washington-brenham-permit-com-add-26-0006",
            "statewide-tdlr-tabs-TABS2026017664",
        ],
        "match_basis": [
            "same county and same address: 1119 Industrial Boulevard/Blvd",
            "both scopes describe adding 5,000 sf to an existing metal building",
            "city permit gives current permitted status after the earlier TDLR registration",
        ],
        "conflicts": [
            "city permit names Moeller Electric; TDLR project name is generic address addition",
            "estimated values differ: city permit $400,000 versus TDLR $100,000",
        ],
    },
    {
        "canonical_id": "dedup-washington-maintenance-building-506-s-austin",
        "member_ids": [
            "washington-brenham-permit-com-rem-26-0028",
            "statewide-tdlr-tabs-TABS2026027978",
        ],
        "match_basis": [
            "same county and same address: 506 S Austin Street",
            "both identify City of Brenham maintenance building remodel",
            "both scopes describe fire-related remodel/code work",
        ],
        "conflicts": [
            "estimated values differ: city permit $737,212 versus TDLR $275,000",
            "TDLR registration date is before the city permit date and is not bid evidence",
        ],
    },
    {
        "canonical_id": "dedup-washington-citizens-bank-400-s-austin",
        "member_ids": [
            "washington-brenham-permit-com-new-26-0012",
            "statewide-tdlr-tabs-TABS2026021492",
        ],
        "match_basis": [
            "same county and same address: 400 S Austin Street",
            "both identify Citizens National Bank",
            "both describe new bank construction",
        ],
        "conflicts": [
            "city permit includes a related parking-spaces permit not included in the TDLR scope",
            "estimated values differ: city permit $2,568,491 building plus $15,000 parking versus TDLR $2,400,000",
        ],
    },
    {
        "canonical_id": "dedup-washington-henderson-park-cover",
        "member_ids": [
            "washington-brenham-bid-26-015-henderson-park",
            "statewide-tdlr-tabs-TABS2026025600",
        ],
        "match_basis": [
            "same county and same project name: Henderson Park Basketball Court Cover",
            "bid packet and TDLR both describe an open-air basketball court cover/pavilion with concrete flatwork",
            "TDLR supplies address where the bid record only named Henderson Park, Brenham",
        ],
        "conflicts": [
            "bid deadline expired on 2026-08-18 before the finalization run",
            "TDLR registration is not evidence that bidding remains open",
        ],
    },
    {
        "canonical_id": "dedup-burleson-somerville-city-hall-150-8th",
        "member_ids": [
            "burleson-somerville-rfq-2025-new-city-hall-150-8th",
            "statewide-tdlr-tabs-TABS2026021872",
        ],
        "match_basis": [
            "same county and same address: 150 8th Street",
            "both identify new Somerville City Hall",
            "historical RFQ plus later TDLR registration appear to describe the same civic building project",
        ],
        "conflicts": [
            "RFQ bid deadline expired 2025-03-05; do not treat as open bid",
            "scope sizes differ: RFQ says approximately 4,000 sf and TDLR says 3,045 sf",
        ],
    },
    {
        "canonical_id": "dedup-burleson-saam-house-441-gun-range",
        "member_ids": [
            "burleson-somerville-ord-25-018-441-gun-range-road-zoning",
            "statewide-tdlr-tabs-TABS2026010963",
        ],
        "match_basis": [
            "same county and same address: 441 Gun Range Road",
            "local zoning change to C-2 general business plausibly supports the later TDLR S.A.A.M. House expansion at the same site",
            "records are complementary planning/registration records rather than duplicate bid records",
        ],
        "conflicts": [
            "local ordinance does not name S.A.A.M. House or establish construction status",
            "TDLR registration gives expansion scope but no open contract evidence",
        ],
    },
    {
        "canonical_id": "dedup-grimes-eag-chevrolet-9030-hwy-6",
        "member_ids": [
            "grimes-navasota-pz-20260827-sterling-auto-expansion",
            "statewide-tdlr-tabs-TABS2026023660",
        ],
        "match_basis": [
            "same county and same address: 9030 Highway/State Hwy 6, Navasota",
            "local planning record concerns expanding a vehicle-sales site; TDLR concerns new showroom/service center with sitework",
            "both point to a dealership/auto-use project at the same parcel",
        ],
        "conflicts": [
            "project names differ: Sterling Auto / Navasota Ventures versus EAG Chevrolet",
            "local planning source does not prove a permit or open subcontract package",
        ],
    },
    {
        "canonical_id": "dedup-grimes-altamira-hwy-90-east",
        "member_ids": [
            "grimes-navasota-dashboard-20260920-altamira-hwy90-east",
            "statewide-tdlr-tabs-TABS2026004667",
        ],
        "match_basis": [
            "same county and same development name: Altamira / Hwy 90 East Development",
            "both reference Phase 1/2 infrastructure for the east-side development area",
            "city dashboard adds underway utility status while TDLR supplies registered sitework scope",
        ],
        "conflicts": [
            "city dashboard has coordinates/development area, not a street address",
            "TDLR estimated completion 2026-07-01 is not proof of current work by itself",
        ],
    },
]


NEGATIVE_NOTES: dict[str, list[str]] = {
    "washington-brenham-bid-26-013-city-hall-rtu5": [
        "kept separate from TABS2026003432: same civic street address string appears, but local record is City Hall RTU-5 replacement and TDLR record is Brenham Family Park Phase 1",
    ],
    "statewide-tdlr-tabs-TABS2026003432": [
        "kept separate from Washington City Hall RTU-5 bid despite 200 W Vulcan address because the project names/scopes conflict",
    ],
    "washington-brenham-permit-misc-prkg-26-0022-sherwin-williams": [
        "kept separate from TABS2026019757: same street number only; N Park driveway replacement and E Academy interior restroom addition are different projects",
    ],
    "statewide-tdlr-tabs-TABS2026019757": [
        "kept separate from Sherwin Williams driveway permit because the address and scope do not match",
    ],
    "brazos-bryan-sdrc-sp26-000061-reveille-park-phase-1": [
        "kept separate from nearby Reveille TDLR records at 4317/4319 G Rollie White because names and parcels indicate different Reveille-area projects",
    ],
}


TEST_CASES: list[dict[str, Any]] = [
    {
        "name": "group exact permit and TDLR Frost Bank",
        "ids": ["washington-brenham-permit-com-new-26-0011", "statewide-tdlr-tabs-TABS2026020346"],
        "expected_same_group": True,
        "reason": "same address, same bank name, same new-construction scope",
    },
    {
        "name": "group exact permit and TDLR Grace paving",
        "ids": [
            "washington-brenham-permit-misc-prkg-26-0018-grace-drainage",
            "statewide-tdlr-tabs-TABS2026022754",
        ],
        "expected_same_group": True,
        "reason": "same address and same paving/drainage scope/value",
    },
    {
        "name": "group historical RFQ and later TDLR Somerville City Hall",
        "ids": ["burleson-somerville-rfq-2025-new-city-hall-150-8th", "statewide-tdlr-tabs-TABS2026021872"],
        "expected_same_group": True,
        "reason": "same address and same city hall project, while preserving expired bid status",
    },
    {
        "name": "do not merge Barron Landing different buildings/units",
        "ids": ["statewide-tdlr-tabs-TABS2026027188", "statewide-tdlr-tabs-TABS2026024607"],
        "expected_same_group": False,
        "reason": "same campus/address but Building 700 and Building 600 Unit 602 are separate units/phases",
    },
    {
        "name": "do not merge Greens Prairie phases",
        "ids": ["statewide-tdlr-tabs-TABS2026028296", "statewide-tdlr-tabs-TABS2026027977"],
        "expected_same_group": False,
        "reason": "same base address but Section 6 Phase 603 and Section 8 Phase 801 are distinct phases",
    },
    {
        "name": "do not merge Gameday Suites numbered registrations",
        "ids": ["statewide-tdlr-tabs-TABS2026024885", "statewide-tdlr-tabs-TABS2026024883"],
        "expected_same_group": False,
        "reason": "same base address but separate numbered records Aggieland-3 and Aggieland-2",
    },
    {
        "name": "do not merge City Hall RTU with Brenham Family Park",
        "ids": ["washington-brenham-bid-26-013-city-hall-rtu5", "statewide-tdlr-tabs-TABS2026003432"],
        "expected_same_group": False,
        "reason": "same civic-address string but different project name and scope",
    },
    {
        "name": "do not merge Sherwin driveway with Cannery Center",
        "ids": [
            "washington-brenham-permit-misc-prkg-26-0022-sherwin-williams",
            "statewide-tdlr-tabs-TABS2026019757",
        ],
        "expected_same_group": False,
        "reason": "same street number only; different street, party and scope",
    },
]


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug_id(record_id: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", record_id.lower()).strip("-")
    return f"dedup-single-{value}"


def load_records(input_root: pathlib.Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(input_root.glob("*/records.json")):
        lane = path.parent.name
        for record in json.loads(path.read_text()):
            record = dict(record)
            record["_lane"] = lane
            records[record["id"]] = record
    return records


def validate_reviewed_groups(records: dict[str, dict[str, Any]]) -> None:
    missing = []
    seen = set()
    repeated = []
    for group in REVIEWED_GROUPS:
        for record_id in group["member_ids"]:
            if record_id not in records:
                missing.append(record_id)
            if record_id in seen:
                repeated.append(record_id)
            seen.add(record_id)
    if missing:
        raise SystemExit(f"reviewed group references missing record ids: {missing}")
    if repeated:
        raise SystemExit(f"record ids repeated across reviewed groups: {repeated}")


def build_groups(records: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    validate_reviewed_groups(records)
    grouped_ids = {record_id for group in REVIEWED_GROUPS for record_id in group["member_ids"]}
    groups = [dict(group) for group in REVIEWED_GROUPS]
    for record_id in sorted(records):
        if record_id in grouped_ids:
            continue
        groups.append(
            {
                "canonical_id": slug_id(record_id),
                "member_ids": [record_id],
                "match_basis": [
                    "singleton: no conservative duplicate match found in the supplied review inputs",
                ],
                "conflicts": NEGATIVE_NOTES.get(record_id, []),
            }
        )
    return sorted(groups, key=lambda item: item["canonical_id"])


def run_tests(groups: list[dict[str, Any]]) -> dict[str, Any]:
    record_to_group = {
        record_id: group["canonical_id"]
        for group in groups
        for record_id in group["member_ids"]
    }
    cases = []
    for case in TEST_CASES:
        group_ids = [record_to_group.get(record_id) for record_id in case["ids"]]
        actual_same = len(set(group_ids)) == 1
        passed = actual_same == case["expected_same_group"]
        cases.append(
            {
                "name": case["name"],
                "record_ids": case["ids"],
                "expected_same_group": case["expected_same_group"],
                "actual_canonical_ids": group_ids,
                "passed": passed,
                "reason": case["reason"],
            }
        )
    return {
        "generated_at": now_utc(),
        "tests_run": len(cases),
        "tests_passed": sum(1 for case in cases if case["passed"]),
        "tests_failed": sum(1 for case in cases if not case["passed"]),
        "cases": cases,
    }


def evidence_missing_count(records: dict[str, dict[str, Any]]) -> int:
    missing = 0
    for record in records.values():
        for source in record.get("sources", []):
            local_path = source.get("local_path")
            if local_path and not pathlib.Path(local_path).exists():
                missing += 1
    return missing


def write_summary(
    output_root: pathlib.Path,
    records: dict[str, dict[str, Any]],
    groups: list[dict[str, Any]],
    tests: dict[str, Any],
) -> None:
    duplicate_groups = [group for group in groups if len(group["member_ids"]) > 1]
    singletons = [group for group in groups if len(group["member_ids"]) == 1]
    lines = [
        "# Masiate Pilot Dedup Summary",
        "",
        "## Result",
        "",
        f"- Input records checked: {len(records)}",
        f"- Canonical project groups written: {len(groups)}",
        f"- Multi-record groups: {len(duplicate_groups)}",
        f"- Singleton groups: {len(singletons)}",
        f"- Offline duplicate tests: {tests['tests_passed']}/{tests['tests_run']} passed",
        f"- Missing preserved local evidence paths encountered: {evidence_missing_count(records)}",
        "",
        "## Conservative Merges",
        "",
    ]
    for group in duplicate_groups:
        lines.append(f"- {group['canonical_id']}: {', '.join(group['member_ids'])}")
    lines.extend(
        [
            "",
            "## Guardrails Applied",
            "",
            "- Ambiguous same-campus, same-subdivision, same-owner and same-address records stayed separate when unit, building, phase, date or scope showed a distinct project.",
            "- TDLR registrations were treated as registration/review evidence, not as open contracts.",
            "- Expired bid records stayed historical even when grouped with a later registration for the same project.",
            "- Private homeowner contact details were not added or exported.",
            "",
            "## Runtime Artifacts",
            "",
            f"- {output_root / 'groups.json'}",
            f"- {output_root / 'duplicate_tests.json'}",
            f"- {output_root / 'status.json'}",
            f"- {output_root / 'summary.md'}",
            "",
        ]
    )
    (output_root / "summary.md").write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=pathlib.Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-root", type=pathlib.Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--started-at", default=None)
    args = parser.parse_args()

    args.output_root.mkdir(parents=True, exist_ok=True)
    existing_status_path = args.output_root / "status.json"
    started_at = args.started_at
    if started_at is None and existing_status_path.exists():
        try:
            started_at = json.loads(existing_status_path.read_text()).get("started_at")
        except json.JSONDecodeError:
            started_at = None
    if started_at is None:
        started_at = now_utc()
    records = load_records(args.input_root)
    groups = build_groups(records)
    tests = run_tests(groups)
    finished_at = now_utc()

    (args.output_root / "groups.json").write_text(json.dumps(groups, indent=2) + "\n")
    (args.output_root / "duplicate_tests.json").write_text(json.dumps(tests, indent=2) + "\n")
    write_summary(args.output_root, records, groups, tests)

    status = {
        "state": "complete" if tests["tests_failed"] == 0 else "partial",
        "started_at": started_at,
        "checkpoint_at": finished_at,
        "finished_at": finished_at,
        "input_record_count": len(records),
        "canonical_group_count": len(groups),
        "multi_record_group_count": sum(1 for group in groups if len(group["member_ids"]) > 1),
        "singleton_group_count": sum(1 for group in groups if len(group["member_ids"]) == 1),
        "duplicate_tests": {
            "tests_run": tests["tests_run"],
            "tests_passed": tests["tests_passed"],
            "tests_failed": tests["tests_failed"],
        },
        "output_paths": {
            "groups_json": str(args.output_root / "groups.json"),
            "duplicate_tests_json": str(args.output_root / "duplicate_tests.json"),
            "summary_md": str(args.output_root / "summary.md"),
            "status_json": str(args.output_root / "status.json"),
        },
        "notes": [
            "Conservative dedup pass only; no collection crawl, paid API, prospect message, push or live change.",
            "Ambiguous same-address unit/phase records are intentionally retained as separate canonical groups.",
        ],
    }
    (args.output_root / "status.json").write_text(json.dumps(status, indent=2) + "\n")


if __name__ == "__main__":
    main()
