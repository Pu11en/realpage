# Masiate Contact Research Ledger Contract

## Purpose

This directory records the contact research for the fixed 49-property Masiate
snapshot. The original property JSON and earlier PDFs stay unchanged. The
manifest is the immutable assignment inventory; the four batch files contain
new research results.

## Files And Ownership

- `manifest.json` contains ranks 1-49, stable property IDs, original actors,
  deduplicated source links, fixed batch assignments, and the nine previously
  researched construction-company phone records as reusable seeds.
- `batch-01.json` owns ranks 1-13.
- `batch-02.json` owns ranks 14-26.
- `batch-03.json` owns ranks 27-39.
- `batch-04.json` owns ranks 40-49.
- A research worker edits only its assigned batch file and scoped notes.
- A missing batch file is valid during partial work. It is invalid at the final
  gate.

## Batch Document Shape

Each batch file is a JSON object:

```json
{
  "batch_id": "batch-01",
  "properties": []
}
```

Each property result uses this shape:

```json
{
  "property_id": "the-stable-manifest-id",
  "rank": 1,
  "research_status": "researched",
  "sources_checked": [],
  "actors_checked": [],
  "contacts": [],
  "selected_route_id": "primary",
  "alternative_route_ids": [],
  "researched_gap": null
}
```

`research_status` is `not_yet_researched`, `in_progress`, or `researched`.
Only `researched` passes the final gate. Partial validation accepts unfinished
or absent properties without describing them as complete.

## Source Checks

Every original `source_links` URL from the manifest must appear once in
`sources_checked`. Add official contact pages and other newly used evidence to
the same list. Every item requires:

- `url`: public HTTP or HTTPS source.
- `disposition`: one of `contact_found`, `no_contact_fields`, `inaccessible`,
  `irrelevant`, `duplicate`, `privacy_only`, or `ambiguous_entity`.
- `outcome`: a source-specific written result, not a blank or generic label.
- `checked_on`: the actual `YYYY-MM-DD` check date.

Repeated URLs should be checked once. A failed extraction is not a completed
source check when the public page or PDF can be inspected another way.

## Actors Checked

`actors_checked` records the relevant owner, tenant, builder, designer,
engineer, manager, representative, or institution considered. Every entry must
include `name`, its actual `role`, and a written `outcome`. Do not turn a
designer or engineer into a builder, or a company office into a direct project
manager.

## Contact Routes

Each item in `contacts` requires:

- `route_id`: unique within the property, such as `builder-office`.
- `contact_name` and the contact's actual `role`.
- At least one of `phone`, `email`, or `website`.
- `public_business_basis`: why the route is public business information.
- `match_evidence`: why the business and location/project identity match.
- `source_type`: `official_company`, `government_record`, `institution`,
  `association`, `professional_profile`, `directory`, or `other`.
- `source_url`: a URL also recorded in `sources_checked`.
- `checked_on`: `YYYY-MM-DD`.
- `match_status`: `confirmed` or `provisional`.
- `source_strength`: `strong` or `provisional`.

Directory-only or otherwise ambiguous entity matches must be both
`match_status: provisional` and `source_strength: provisional`. They are
counted separately from stronger company, institution, association, or public
record matches. Publication is not proof the phone still connects; no test
calls are part of this ledger.

`selected_route_id` must point to the best contact containing a public business
phone. `alternative_route_ids` can point to at most two other useful contacts.
The selected route and alternatives must be distinct. Consumer order lines,
unrelated stores, registered agents, fax numbers, and unverified private-owner
numbers are not suitable fillers.

## Researched Gaps

When no suitable public business phone is selected, set `selected_route_id` to
`null` and provide `researched_gap` with:

- `reason_code`: `actor_unknown`, `no_public_business_contact`,
  `inaccessible_source`, `ambiguous_entity`, `privacy_only`,
  `no_suitable_role`, or `other_specific`.
- `explanation`: a specific explanation of what blocked a suitable number.
- `research_steps`: at least two concrete checks, including an official-contact
  lookup and a targeted alternate lookup when an identifiable business exists.
- `checked_on`: `YYYY-MM-DD`.

Generic statements such as "not found" or "no phone found" fail validation.
A single inaccessible tool or a missing contractor name is not enough by
itself.

## Offline Validation

During research, run:

```bash
python3 tooling/masiate_pdf/contact_coverage.py
```

It reports partial coverage and returns success when completed rows are valid.
For the final all-49 gate, run:

```bash
python3 tooling/masiate_pdf/contact_coverage.py --require-complete
```

The final command fails on missing or duplicate IDs, unfinished rows, unchecked
original links, missing phone provenance, missing roles, ambiguous contacts
counted as strong, unsupported generic gaps, or any other schema error. Its
summary keeps confirmed/strong phones, provisional/best-guess phones, and
researched no-number gaps separate.
