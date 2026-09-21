#!/usr/bin/env python3
"""Create the Masiate pilot contacts finish-lane artifacts.

The script is intentionally deterministic: it reads the immutable review-input
snapshot, selects only pre-vetted business contact routes, checks preserved
evidence paths exist, and writes the contacts runtime outputs.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import shutil
from typing import Any


REVIEW_INPUT = pathlib.Path(
    "/home/drewp/.local/state/cranesignal/masiate/pilot-20260920-2048/review-input"
)
RUNTIME_OUT = pathlib.Path(
    "/home/drewp/.local/state/cranesignal/masiate/pilot-20260920-2048/finish/contacts"
)
MIRROR_OUT = pathlib.Path("propertystack/data/masiate/pilot-20260920/workers/finish-contacts")


SELECTED_CONTACTS = [
    {
        "record_id": "washington-brenham-permit-com-new-26-0011",
        "business": "SpawGlass",
        "role": "permit-listed general contractor",
        "basis": "City permit report names SpawGlass as contractor for Frost Bank new construction; preserved SpawGlass website evidence verifies it is a Texas construction-services business.",
    },
    {
        "record_id": "washington-brenham-permit-com-new-26-0011",
        "business": "Frost Bank",
        "role": "permit applicant / CAD owner / future branch operator",
        "basis": "City permit report and CAD identify Frost Bank as owner/applicant; preserved Frost location page lists the Brenham financial center at the permit address as coming 2027.",
    },
    {
        "record_id": "washington-brenham-permit-com-new-26-0012",
        "business": "EBCO General Contractor",
        "role": "permit-listed general contractor",
        "basis": "City permit report names EBCO as contractor for Citizens National Bank new construction; preserved company site evidence verifies commercial, industrial, public and multifamily construction services.",
    },
    {
        "record_id": "washington-brenham-permit-com-new-26-0012",
        "business": "Citizens National Bank",
        "role": "permit applicant / CAD owner",
        "basis": "City permit report and CAD identify Citizens National Bank as applicant and parcel owner for the new bank construction.",
    },
    {
        "record_id": "washington-brenham-permit-com-new-26-0013",
        "business": "Collier Construction LLC",
        "role": "permit-listed construction participant",
        "basis": "City permit report names Collier Construction on the Wilkins Valley phase 3 infrastructure/office permit; preserved contact-page evidence verifies Collier Construction LLC as a Brenham construction business.",
    },
    {
        "record_id": "washington-brenham-permit-com-add-26-0006",
        "business": "Davis Custom Builders of Texas",
        "role": "permit-listed contractor",
        "basis": "City permit report names Davis Custom Builders of Texas as contractor for the Moeller Electric metal-building addition.",
    },
    {
        "record_id": "washington-brenham-permit-com-roof-26-0003",
        "business": "Guardian Roof Systems",
        "role": "permit-listed roofing contractor",
        "basis": "City permit report names Guardian Roof Systems as contractor for the commercial roof replacement at 1901 Longwood Drive.",
    },
    {
        "record_id": "washington-brenham-permit-com-new-26-0014",
        "business": "United Constructors of Texas",
        "role": "permit-listed contractor",
        "basis": "City permit report names United Constructors of Texas as contractor for the Lex Investments tenant office buildout.",
    },
    {
        "record_id": "washington-brenham-permit-com-new-26-0010-apartment",
        "business": "Valco Builders",
        "role": "permit-listed contractor",
        "basis": "City permit report names Valco Builders as contractor for the Nelson Sosa multifamily apartment building; private owner contact details were not exported.",
    },
    {
        "record_id": "washington-brenham-permit-com-new-26-0007",
        "business": "Redeemer Church Brenham",
        "role": "owner/applicant",
        "basis": "City permit report and CAD identify Redeemer Church Brenham for the permitted parking-lot improvements; no private contact details were exported.",
    },
    {
        "record_id": "washington-brenham-permit-com-new-26-0007",
        "business": "Atlas Sign Services",
        "role": "permit-listed sign/wall contractor",
        "basis": "City permit report names Atlas Sign Services for the related wall/sign construction at Redeemer Church.",
    },
    {
        "record_id": "washington-brenham-permit-com-add-26-0009",
        "business": "Dudley Construction",
        "role": "permit-listed contractor",
        "basis": "City permit report names Dudley Construction for the Brenham Water Treatment Plant rehabilitation and expansion.",
    },
    {
        "record_id": "washington-brenham-permit-misc-prkg-26-0018-grace-drainage",
        "business": "Grace Community Fellowship - Brenham",
        "role": "permit applicant / owner-listed contractor",
        "basis": "City permit report identifies Grace Community Fellowship for paving and drainage improvements; source does not prove outside subcontract packages remain open.",
    },
    {
        "record_id": "grimes-navasota-dashboard-20260920-minnie-street-cdbg",
        "business": "Terra Bella Construction",
        "role": "awarded contractor named by city dashboard",
        "basis": "City dashboard names Terra Bella Construction as awarded contractor for the Minnie Street water and sewer replacement project.",
    },
    {
        "record_id": "grimes-navasota-dashboard-20260920-fosters-levy-louise-mitmod",
        "business": "JTM Construction",
        "role": "awarded contractor named by city dashboard",
        "basis": "City dashboard names JTM Construction as awarded contractor and reports active sewer-main replacement on Foster Street.",
    },
    {
        "record_id": "grimes-iola-20260811-wwtp-contract",
        "business": "Teal Services, LLC",
        "role": "construction contract party named in public agenda",
        "basis": "City of Iola agenda item names Teal Services, LLC as construction contract party for the TWDB wastewater-treatment-plant project.",
    },
    {
        "record_id": "grimes-iola-20260811-wwtp-contract",
        "business": "City of Iola",
        "role": "owner/public buyer",
        "basis": "City current-projects and agenda evidence identify City of Iola as public owner/buyer for the WWTP project.",
    },
    {
        "record_id": "leon-county-rfp-2026-355-courthouse-building-improvements",
        "business": "Phoenix I Restoration and Construction LLC",
        "role": "bidder / recommended CMAR",
        "basis": "Leon County bid-tab evidence names Phoenix I Restoration and Construction LLC as bidder/recommended CMAR for courthouse/building improvements.",
    },
    {
        "record_id": "leon-county-rfp-2026-355-courthouse-building-improvements",
        "business": "Leon County, Texas",
        "role": "owner/public buyer",
        "basis": "Leon County bid-tab evidence identifies the county as owner for the courthouse/building improvements project.",
    },
    {
        "record_id": "grimes-navasota-pz-20260827-sterling-auto-expansion",
        "business": "Lay Construction",
        "role": "project representative verified in city memo",
        "basis": "Navasota P&Z memo identifies Lay Construction as project representative for the Sterling Auto / Navasota Ventures site expansion.",
    },
    {
        "record_id": "grimes-navasota-pz-20260827-sterling-auto-expansion",
        "business": "Navasota Ventures, LLC",
        "role": "owner/applicant verified in city memo",
        "basis": "Navasota P&Z memo and CAD evidence identify Navasota Ventures, LLC as owner/applicant for the site-expansion planning case.",
    },
    {
        "record_id": "burleson-somerville-ord-26-011-avenue-p-multifamily",
        "business": "ALTURA CAPITAL LLC",
        "role": "CAD-listed owner/developer",
        "basis": "Somerville ordinance and Burleson CAD evidence identify ALTURA CAPITAL LLC as owner/developer for the Avenue P multifamily special-use permit.",
    },
    {
        "record_id": "robertson-hearne-el-construction-w-blackshear-2026-09-15",
        "business": "EL Construction, LLC",
        "role": "property owner / applicant business",
        "basis": "Hearne agenda and Robertson CAD evidence identify EL Construction, LLC as business owner/applicant for the West Blackshear Street tract petition.",
    },
    {
        "record_id": "robertson-hearne-iron-oak-lots-114-115-variance-2026-08-25",
        "business": "Iron Oak Reserve, LLC",
        "role": "property owner of unsold Iron Oak Reserve lots",
        "basis": "Hearne variance agenda and Robertson CAD evidence identify Iron Oak Reserve, LLC for lots 114 and 115.",
    },
    {
        "record_id": "brazos-bryan-sdrc-sp26-000053-oxbow-business-park",
        "business": "Oxbow Construction, LLC",
        "role": "owner/developer",
        "basis": "Bryan SDRC plan evidence identifies Oxbow Construction, LLC as owner/developer for the Oxbow Business Park site plan.",
    },
]


CONTACT_DETAIL_OVERRIDES = {
    (
        "washington-brenham-permit-com-new-26-0013",
        "Collier Construction LLC",
    ): {
        "phone": "979-836-4477",
        "email": "maceyt@collierconstruction.com",
    },
    (
        "washington-brenham-permit-com-new-26-0012",
        "EBCO General Contractor",
    ): {
        "phone": "254-697-8516",
    },
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_records() -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(REVIEW_INPUT.glob("*/records.json")):
        for record in json.loads(path.read_text()):
            records[record["id"]] = record
    return records


def find_contact(record: dict[str, Any], business: str) -> dict[str, Any] | None:
    needle = business.casefold()
    for contact in record.get("business_contacts") or []:
        if contact.get("name", "").casefold() == needle:
            return contact
    for participant in record.get("participants") or []:
        if participant.get("name", "").casefold() == needle:
            return {
                "name": participant.get("name"),
                "role": participant.get("role"),
                "phone": None,
                "email": None,
                "website": None,
                "source_url": participant.get("source_url"),
            }
    raise KeyError(f"{business!r} not found on {record['id']}")


def existing_source_paths(record: dict[str, Any]) -> list[str]:
    paths = []
    for source in record.get("sources") or []:
        local = source.get("local_path")
        if local and pathlib.Path(local).exists():
            paths.append(local)
    return paths


def build_contacts(records: dict[str, dict[str, Any]], retrieved_at: str) -> list[dict[str, Any]]:
    contacts = []
    for selected in SELECTED_CONTACTS:
        record = records[selected["record_id"]]
        contact = find_contact(record, selected["business"])
        contact.update(CONTACT_DETAIL_OVERRIDES.get((record["id"], selected["business"]), {}))
        source_url = contact.get("source_url") or (record.get("sources") or [{}])[0].get("url")
        contacts.append(
            {
                "record_ids": [record["id"]],
                "verified_business_name": contact.get("name") or selected["business"],
                "role": selected["role"],
                "phone": contact.get("phone"),
                "email": contact.get("email"),
                "website": contact.get("website"),
                "source_url": source_url,
                "retrieved_at": retrieved_at,
                "role_basis": selected["basis"],
                "county": record.get("county"),
                "project_name": record.get("project_name"),
                "address": record.get("address"),
                "record_type": record.get("record_type"),
                "record_stage": record.get("stage"),
                "record_date": record.get("record_date"),
                "contact_limits": "No guessed emails, no private homeowner contact details, and no inferred purchasing authority. A permit-listed contractor or public award does not prove open subcontracting.",
                "evidence_local_paths_checked": existing_source_paths(record),
            }
        )
    return contacts


def write_summary(path: pathlib.Path, contacts: list[dict[str, Any]], total_records: int, now: str) -> None:
    by_county: dict[str, int] = {}
    official_only = 0
    website_count = 0
    phone_count = 0
    email_count = 0
    for contact in contacts:
        by_county[contact["county"]] = by_county.get(contact["county"], 0) + 1
        if not any([contact["phone"], contact["email"], contact["website"]]):
            official_only += 1
        if contact["website"]:
            website_count += 1
        if contact["phone"]:
            phone_count += 1
        if contact["email"]:
            email_count += 1

    lines = [
        "# Masiate Pilot Contacts Finish Summary",
        "",
        "## Result",
        "",
        f"- Finished at: {now}",
        f"- Snapshot records reviewed/scored: {total_records}",
        f"- Contact routes saved: {len(contacts)}",
        f"- Routes with verified business websites: {website_count}",
        f"- Routes with supported phones: {phone_count}",
        f"- Routes with supported emails: {email_count}",
        f"- Official-record-only routes with no phone/email/website: {official_only}",
        "",
        "## County Spread",
        "",
    ]
    for county, count in sorted(by_county.items()):
        lines.append(f"- {county}: {count}")
    lines.extend(
        [
            "",
            "## Selection Rules Applied",
            "",
            "- Preferred actual owners, permit-listed contractors, awarded contractors, public buyers and named project representatives.",
            "- Excluded private homeowner contacts and did not export any private phone or email data.",
            "- Did not infer purchasing authority, open subcontract packages or current construction from registrations alone.",
            "- Demoted architect-only, designer-only and accessibility-registrant-only routes unless they were not needed for this contact lane.",
            "- Preserved planning versus permit versus public-award status in each contact entry.",
            "",
            "## Strongest Business Routes",
            "",
        ]
    )
    for contact in contacts:
        website = contact["website"] or "official source only"
        lines.append(
            f"- {contact['county']} — {contact['verified_business_name']} ({contact['role']}) for {contact['project_name']}; route: {website}."
        )
    lines.extend(
        [
            "",
            "## Gaps And Continuation",
            "",
            "- Most preserved source records identify business entities but not direct procurement contacts.",
            "- Open availability remains unknown for permit-stage and awarded-contractor records.",
            "- Several strong projects have business names only from permits; direct official business-site lookup can deepen them later if allowed.",
            "- No paid API, outreach, new crawl or private-contact export was performed.",
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-out", type=pathlib.Path, default=RUNTIME_OUT)
    parser.add_argument("--mirror-out", type=pathlib.Path, default=MIRROR_OUT)
    args = parser.parse_args()

    now = utc_now()
    records = load_records()
    contacts = build_contacts(records, now)

    args.runtime_out.mkdir(parents=True, exist_ok=True)
    contacts_path = args.runtime_out / "contacts.json"
    summary_path = args.runtime_out / "summary.md"
    status_path = args.runtime_out / "status.json"
    contacts_path.write_text(json.dumps(contacts, indent=2) + "\n")
    write_summary(summary_path, contacts, len(records), now)
    status = {
        "role": "contacts",
        "state": "complete",
        "started_at": json.loads(status_path.read_text()).get("started_at") if status_path.exists() else now,
        "checkpoint_at": now,
        "finished_at": now,
        "records_reviewed": len(records),
        "contacts_saved": len(contacts),
        "output_paths": {
            "contacts_json": str(contacts_path),
            "summary_md": str(summary_path),
            "status_json": str(status_path),
        },
        "notes": [
            "Selected verified business routes from strongest service-fit candidate records.",
            "Excluded private homeowner contacts and architect/designer-only routes where stronger owner/GC routes existed.",
            "Used preserved local evidence paths; no paid APIs, outreach, pushes, live changes, extra agents or broad crawl.",
        ],
    }
    status_path.write_text(json.dumps(status, indent=2) + "\n")

    args.mirror_out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(contacts_path, args.mirror_out / "contacts.json")
    shutil.copy2(summary_path, args.mirror_out / "summary.md")
    shutil.copy2(status_path, args.mirror_out / "status.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
