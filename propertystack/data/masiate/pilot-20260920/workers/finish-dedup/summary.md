# Masiate Pilot Dedup Summary

## Result

- Input records checked: 267
- Canonical project groups written: 254
- Multi-record groups: 13
- Singleton groups: 241
- Offline duplicate tests: 8/8 passed
- Missing preserved local evidence paths encountered: 0

## Conservative Merges

- dedup-burleson-saam-house-441-gun-range: burleson-somerville-ord-25-018-441-gun-range-road-zoning, statewide-tdlr-tabs-TABS2026010963
- dedup-burleson-somerville-city-hall-150-8th: burleson-somerville-rfq-2025-new-city-hall-150-8th, statewide-tdlr-tabs-TABS2026021872
- dedup-grimes-altamira-hwy-90-east: grimes-navasota-dashboard-20260920-altamira-hwy90-east, statewide-tdlr-tabs-TABS2026004667
- dedup-grimes-eag-chevrolet-9030-hwy-6: grimes-navasota-pz-20260827-sterling-auto-expansion, statewide-tdlr-tabs-TABS2026023660
- dedup-washington-citizens-bank-400-s-austin: washington-brenham-permit-com-new-26-0012, statewide-tdlr-tabs-TABS2026021492
- dedup-washington-edward-jones-1504-s-day: washington-brenham-permit-com-new-26-0014, statewide-tdlr-tabs-TABS2026023085
- dedup-washington-frost-bank-862-us-290-e: washington-brenham-permit-com-new-26-0011, statewide-tdlr-tabs-TABS2026020346
- dedup-washington-grace-community-107-s-saeger: washington-brenham-permit-misc-prkg-26-0018-grace-drainage, statewide-tdlr-tabs-TABS2026022754
- dedup-washington-henderson-park-cover: washington-brenham-bid-26-015-henderson-park, statewide-tdlr-tabs-TABS2026025600
- dedup-washington-maintenance-building-506-s-austin: washington-brenham-permit-com-rem-26-0028, statewide-tdlr-tabs-TABS2026027978
- dedup-washington-moeller-1119-industrial: washington-brenham-permit-com-add-26-0006, statewide-tdlr-tabs-TABS2026017664
- dedup-washington-redeemer-church-2111-s-blue-bell: washington-brenham-permit-com-new-26-0007, statewide-tdlr-tabs-TABS2026008498
- dedup-washington-water-treatment-1105-s-austin: washington-brenham-permit-com-add-26-0009, statewide-tdlr-tabs-TABS2026006791

## Guardrails Applied

- Ambiguous same-campus, same-subdivision, same-owner and same-address records stayed separate when unit, building, phase, date or scope showed a distinct project.
- TDLR registrations were treated as registration/review evidence, not as open contracts.
- Expired bid records stayed historical even when grouped with a later registration for the same project.
- Private homeowner contact details were not added or exported.

## Runtime Artifacts

- /home/drewp/.local/state/cranesignal/masiate/pilot-20260920-2048/finish/dedup/groups.json
- /home/drewp/.local/state/cranesignal/masiate/pilot-20260920-2048/finish/dedup/duplicate_tests.json
- /home/drewp/.local/state/cranesignal/masiate/pilot-20260920-2048/finish/dedup/status.json
- /home/drewp/.local/state/cranesignal/masiate/pilot-20260920-2048/finish/dedup/summary.md
