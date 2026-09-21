# Evidence QA Summary

Generated at 2026-09-21T02:23:37Z. Checked 267 records from the immutable review-input snapshot and 336 preserved evidence file paths.

## Outcome
- All referenced local evidence files existed at QA time.
- Checked IDs: 267; unchecked IDs: 0.
- Findings written: 10 grouped findings ({'high': 3, 'medium': 5, 'low': 2}).
- Do not rewrite source records from this lane; use these findings to label, downgrade, exclude, or verify during review/PDF assembly.

## Highest-Risk Findings
- **future-record-dates** (high, 4 records): Record date is after the QA clock, so the item is an upcoming agenda/checkpoint rather than completed action. Sample: grimes-navasota-pz-20260924-316-mcalpine-carport, grimes-navasota-pz-20260924-nkq-plumbing-217-hill, grimes-navasota-pz-20260924-pecan-grove-phase2, washington-burton-isd-fire-suppression-line
- **future-status-checkpoints** (medium, 0 records): A lane status file contains checkpoint/finished timestamps later than the evidence-qa clock. Sample: lane status file only
- **stage-outside-contract** (medium, 1 records): Stage value is outside the worker-contract enum. Sample: grimes-navasota-dashboard-20260920-hidden-hills-phase3
- **expired-bid-deadlines** (high, 10 records): Bid deadline is before the QA date. Sample: burleson-somerville-rfq-2025-new-city-hall-150-8th, grimes-iola-20260811-wwtp-contract, leon-county-rfb-2026-364-expo, leon-county-rfb-2026-364-hilltop-lakes, leon-county-rfb-2026-364-leon-high ...
- **past-estimated-completion-candidates** (medium, 23 records): Candidate record has an estimated completion date before the QA date while still labeled planned/permitted. Sample: statewide-tdlr-tabs-TABS2026003432, statewide-tdlr-tabs-TABS2026004667, statewide-tdlr-tabs-TABS2026008498, statewide-tdlr-tabs-TABS2026009609, statewide-tdlr-tabs-TABS2026011740 ...
- **tdlr-registration-not-open-contract** (medium, 178 records): TDLR registration candidates show accessibility registration/review, not an open Masiate contract or subcontract opportunity. Sample: statewide-tdlr-tabs-TABS2026001636, statewide-tdlr-tabs-TABS2026003432, statewide-tdlr-tabs-TABS2026003929, statewide-tdlr-tabs-TABS2026004667, statewide-tdlr-tabs-TABS2026005166 ...
- **planning-record-not-open-contract** (medium, 24 records): Planning/agenda candidates do not by themselves prove issued permits, approved work, or open contractor purchasing. Sample: brazos-bryan-sdrc-sp26-000047-11183-sh30, brazos-bryan-sdrc-sp26-000053-oxbow-business-park, brazos-bryan-sdrc-sp26-000055-traditions-villages-6b, brazos-bryan-sdrc-sp26-000056-lorca-apartments, brazos-bryan-sdrc-sp26-000059-tabor-road-apartments ...
- **statewide-geography-mismatch** (high, 3 records): Statewide TDLR matching pulled records outside the intended county/geography. Sample: statewide-tdlr-tabs-TABS2026020630, statewide-tdlr-tabs-TABS2026023109, statewide-tdlr-tabs-TABS2026025873

## Strongest Service-Fit Records Spot-Checked
- **brazos-bryan-sdrc-sp26-000062-north-dunn-apartments** - North and Dunn Apartments (Brazos): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **brazos-bryan-sdrc-sp26-000059-tabor-road-apartments** - Tabor Road Apartments (Brazos): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **brazos-bryan-sdrc-sp26-000056-lorca-apartments** - Lorca Apartments (Brazos): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **grimes-navasota-pz-20260924-pecan-grove-phase2** - Pecan Grove Estates Phase 2 final plat and subdivision agreement (Grimes): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **grimes-navasota-dashboard-20260920-autozone** - Autozone Navasota construction underway (Grimes): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **grimes-navasota-dashboard-20260920-hidden-hills-phase3** - Hidden Hills Subdivision Phase 3 pre-construction (Grimes): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **grimes-navasota-dashboard-20260920-8th-street-townhomes** - 8th Street Townhomes preliminary plat and construction drawings (Grimes): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **washington-brenham-permit-com-new-26-0009-apartments** - Arete Property Group apartment buildings (Washington): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **washington-brenham-permit-com-roof-26-0003** - Sage Longwood Holdings commercial roof replacement (Washington): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **washington-brenham-permit-com-add-26-0006** - Moeller Electric metal building addition (Washington): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **washington-brenham-permit-com-new-26-0012** - Citizens National Bank new construction and parking addition (Washington): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **statewide-tdlr-tabs-TABS2026024787** - Somerville ISD - Phase 2 (Burleson): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **statewide-tdlr-tabs-TABS2026023660** - EAG Chevrolet New Showroom & Service Center (Grimes): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **statewide-tdlr-tabs-TABS2026005166** - Home2Suites by Hilton - Brenham (Washington): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **statewide-tdlr-tabs-TABS2026019833** - Studio 6 Extended Stay (Robertson): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **statewide-tdlr-tabs-TABS2026026486** - Remodel/Expansion Wal-Mart Brenham, TX (Washington): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **statewide-tdlr-tabs-TABS2027001327** - Southern Pointe Section 502 (Brazos): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.
- **statewide-tdlr-tabs-TABS2026027514** - MRC Bryan Communities (Brazos): keep availability cautious; source supports identity/scope, not open purchasing unless separately noted.

## Coordinator Actions
- Exclude or verify the three statewide geography mismatches before PDF use: Marshall SKECHERS, Port Arthur Fire Station No. 2, and City of Burleson City Hall Rebuild.
- Treat TDLR registrations and planning agendas as lead signals, not open contracts.
- Downgrade expired bids and past-estimated-completion candidates unless later evidence proves active work.
- Keep designer/engineer contacts separate from buyers or GCs.
