# Grimes County Masiate Pilot Findings

## Source Notes

- Coordinator plan assigns Grimes to Navasota, other cities, county development and current construction bids.
- Worker contract requires actual address-level records where available, coverage entries for every source checked, and downloaded originals under the runtime evidence directory.
- Statewide portals are excluded because the statewide worker owns TDLR, TCEQ, TABC and Comptroller sources.
- Navasota's ArcGIS dashboard exposes a public FeatureServer layer with 32 active project rows. Several rows have coordinates and construction status but no street address or permit number; useful extracted rows include Autozone, Hidden Hills Phase 3, 8th Street Townhomes, Minnie Street water/sewer and Foster/Levy/Louise water/sewer.
- Navasota Citizenserve exposes search pages and permit fields anonymously, including permit type/status and "Permits Issued After," but the actual search POST returned HTTP 401 Access Denied even with token/cookie.
- Navasota Planning & Zoning Destiny agendas produced the best address-level records: Pecan Grove Phase 2, NKQ Plumbing at 217 W Hill, 316 E McAlpine carport/garage, Sterling Auto at 9030 Highway 6, and SKP Hospitality at 9345 Highway 6.
- Grimes CAD quick search verified selected parcels/owners for R14167, 217 W Hill, 316 E McAlpine, 9030 Highway 6 and 9345 Highway 6.
- Grimes County development/floodplain/road pages publish requirements and forms, not issued permit registers.
- Grimes County bid page lists annual bridge/concrete/culvert-type packets, but downloaded PDFs were image-only through pdftotext.
- CivicClerk county agenda API returned 28 commissioners event/detail JSON files for the requested window; keyword search did not surface address-level development rows.
- Iola current projects and August 11 agenda produced a real WWTP construction signal with Teal Services named in the agenda and Bleyl Engineering plans preserved.
- Anderson, Bedias and Todd Mission pages mostly expose forms/agendas/permit portals, not issued address-level registers in the pages checked; Bedias target-window minutes links returned 404, and Todd Mission agenda PDFs had building-permit updates plus non-addressed drainage/replat items.

## Candidate Notes

- Strongest: Pecan Grove Phase 2; Sterling Auto expansion; Autozone dashboard construction underway; Hidden Hills Phase 3; 8th Street Townhomes; Iola WWTP.
- Public infrastructure candidates: Minnie Street water/sewer with Terra Bella Construction; Foster/Levy/Louise water/sewer with JTM Construction.
- Watchlist: NKQ Plumbing 217 W Hill, downgraded due City Council denial-risk memo; 316 E McAlpine carport/garage; SKP Hospitality 9345 Highway 6 replat; Hwy 90 East / Altamira utilities.
