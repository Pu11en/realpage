# Masiate Pilot Delivery Record

## Outcome

- Fixed 63-page PDF with 49 detailed profiles across all seven counties.
- 267 source records collected, not 267 unique or qualified opportunities.
- 58 source record IDs underpin the 49 profiles; no selected profiles share a member ID.
- 76 coverage receipts retained, including blocked and partial routes.
- Six profiles have a sourced business phone, email or website; no currently open trade package confirmed.
- Matching sanitized JSON saved locally for later agent integration, not connected to the live site or agent.
- No new broad collection pass, outreach, paid-data purchase, deployment or push.

## Evidence Decisions

- Rejected three out-of-area state registrations flagged by geography review.
- Moved Lorca Apartments to watchlist because its exact street address was not resolved.
- Moved Iola WWTP to watchlist because its tender expired and an agenda does not establish available work.
- Moved Pecan Grove Phase 2 to watchlist because September 24 is an upcoming agenda, not completed approval.
- Kept distinct projects/phases where a proposed duplicate join was not established; did not blindly use all 254 proposed duplicate groups as verified unique leads.
- Disclosed 98 Brazos registrations not deeply reviewed, older estimated completion dates, conflicting scope values, and role/availability uncertainty.
- Preserved all original and reviewer evidence outside the public export.
- The three-item watchlist is the coordinator's demotion list, not the full collected watchlist.

## Verification

- Lead-finder test suite: 78 passing, including new assembly, geography, contact, evidence and HTML escaping regressions.
- Extracted all 63 pages: no blank pages or out-of-page characters detected.
- Inspected cover, profile, watchlist/coverage and final page images.
- Public export scanned for `/home/` and `/tmp/` paths: none found.
- Source links and contact methods remain separate from inferred fit and unknown purchasing authority.
- All eight collectors and eight reviewers are archived, with clean committed worker outputs preserved.

## Reproduction

Run from this session's project worktree:

```bash
python3 tooling/masiate_pdf/assemble_pilot.py --root /home/drewp/.local/state/cranesignal/masiate/pilot-20260920-2048 --output propertystack/data/masiate/pilot-20260920
python3 -m pytest propertystack/skills/lead-finder/tests -q
```

Uses existing WeasyPrint, pypdf and pytest. No network is needed to assemble the
frozen evidence. The report deliberately blocks external rendering assets.
Report date is September 20, 2026 Central; coordinator assembly clock is
September 21 UTC. Worker future checkpoint times were not used for elapsed-time claims.

## Delivery Boundary

Attach the final PDF and plain-English results Markdown to the parent thread.
All outputs stay on the local session branch until Drew tests and approves.
The deleted fifty-task plan stays stopped. Late completion messages must not
restart collection or spawn additional review workers. The next pass needs a
new human choice about contacts, availability, or missing-source coverage.
