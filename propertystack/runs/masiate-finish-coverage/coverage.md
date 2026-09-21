# Masiate Pilot Coverage Summary

## Scope

- This is a reconciliation of the immutable review-input snapshots only; it is not a new crawl.
- Counts below are **raw collected records**, **source receipts** and **saved evidence checks**.
- These numbers are not deduped projects, final leads, open contracts or available Masiate scopes.
- TDLR/TABS records are accessibility registrations and should be labeled as planning/registration signals unless another source proves current bid or work status.

## Top-Level Counts

- Raw records collected: **267**.
- Source coverage receipts reconciled: **76**.
- Record source entries checked for local evidence paths: **336**.
- Missing record evidence local paths: **0**.
- Duplicate record IDs found: **0**.

## Coverage Status

- complete: **18** source receipts.
- partial: **42** source receipts.
- blocked: **12** source receipts.
- empty: **3** source receipts.
- not_checked: **1** source receipts.

## County Coverage

### Brazos

- Raw records: **129** total (**9** local, **120** statewide TDLR/TABS).
- Dispositions before final review: **117** candidate, **12** watchlist, **0** excluded.
- Source receipts: **9** total; 2 complete, 4 partial, 3 blocked, 0 empty, 0 not checked.
- Coverage read: **mixed; some exhausted sources plus important partial/blocked sources**.
- Main gaps:
  - City of Bryan SDRC 2026 development-review archive: partial - Inspected the dated archive index and downloaded/extracted the strongest address-level PDFs from 2026-07-28 through 2026-09-15. The 2026-09-22 folder existed but was outside the requested cutoff/current run date and was not used for candidates.
  - City of Bryan monthly building reports: partial - Downloaded the public page and August 2026 PDF. It reports aggregate counts/values only, not address-level permits; August showed residential remodel/addition, multifamily and commercial activity but no project identities.
  - City of Bryan online permitting / Citizenserve: blocked - Official page says users must create an account to access the portal and track application activity. No login/register action was taken.
  - City of College Station building permits issued listing: blocked - Downloaded current and past listing pages. The static page exposes a Govstack document filter but no document rows in the fetched HTML; a direct POST to the official filter endpoint returned HTTP 400, so no address-level permit file was safely collected.

### Burleson

- Raw records: **20** total (**8** local, **12** statewide TDLR/TABS).
- Dispositions before final review: **9** candidate, **11** watchlist, **0** excluded.
- Source receipts: **12** total; 3 complete, 6 partial, 3 blocked, 0 empty, 0 not checked.
- Coverage read: **mixed; some exhausted sources plus important partial/blocked sources**.
- Main gaps:
  - City of Somerville ordinances: partial - Official ordinance index exposed 2025-2026 SUP/zoning/building-fee PDFs. Read/downloaded current relevant SUP/zoning PDFs and extracted project-level address/scope from official scans; did not exhaust every non-project ordinance or full application packet.
  - City of Somerville permits page: partial - Page provides permit contact, SafeBuilt inspection schedule, and application forms; no issued-permit register visible.
  - City of Somerville Planning & Zoning agendas/minutes: partial - Public P&Z page exposed 2024 agendas/minutes only; extracted address-level accessory/subdivision/planning items. 2025-2026 P&Z agendas were not visible on this page, but related adopted ordinances were available separately.
  - City of Somerville RFQ/RFP documents: partial - Downloaded RFQ New City Hall and addenda plus non-construction solid-waste RFP. New City Hall is expired but address-level and relevant; no award status found.

### Grimes

- Raw records: **27** total (**13** local, **14** statewide TDLR/TABS).
- Dispositions before final review: **23** candidate, **4** watchlist, **0** excluded.
- Source receipts: **14** total; 5 complete, 7 partial, 2 blocked, 0 empty, 0 not checked.
- Coverage read: **mixed; some exhausted sources plus important partial/blocked sources**.
- Main gaps:
  - Navasota Planning & Zoning Destiny agendas: partial - Reviewed June-September meeting index pages and extracted address-level development items from August 13, August 27 and September 24 P&Z agendas/memos; also checked City Council follow-up for NKQ and found denial-risk memo. September 24 is a future meeting.
  - Navasota Citizenserve building/development permit portal: blocked - Anonymous search page and permit fields loaded, but normal form POST with page token/cookie returned HTTP 401 Access Denied. Stopped rather than bypassing access controls.
  - Grimes County development/floodplain/road pages: partial - Pages define required development, residential construction, driveway/culvert and road-use permit processes but do not publish issued address-level permit registers.
  - Grimes County request for bids/qualifications: partial - Current bid page lists annual contracts including bridge construction labor, reinforced concrete and culverts; PDFs preserved but image-only through pdftotext, so detailed dates/status were not extracted.

### Leon

- Raw records: **18** total (**14** local, **4** statewide TDLR/TABS).
- Dispositions before final review: **11** candidate, **7** watchlist, **0** excluded.
- Source receipts: **12** total; 2 complete, 7 partial, 2 blocked, 1 empty, 0 not checked.
- Coverage read: **mixed; some exhausted sources plus important partial/blocked sources**.
- Main gaps:
  - Leon County Bid Documents: partial - Current RFB 2026-364 shelter package and RFB 2026-365 postponement found; no issued-permit register.
  - Leon County Bid Tabulations: partial - Reviewed construction-related tabs; most were historical or non-building, CMAR courthouse/building improvements promoted as candidate.
  - Leon County floodplain/development permits: empty - Page provides procedures/applications and says permits are required for new construction/substantial improvements, but no public issued-record register was found.
  - Leon County subdivision/county judge page: partial - Subdivision requirements and checklist found, but not address-level subdivision applications/approvals.

### Madison

- Raw records: **5** total (**3** local, **2** statewide TDLR/TABS).
- Dispositions before final review: **5** candidate, **0** watchlist, **0** excluded.
- Source receipts: **8** total; 2 complete, 5 partial, 0 blocked, 1 empty, 0 not checked.
- Coverage read: **mixed; some exhausted sources plus important partial/blocked sources**.
- Main gaps:
  - City of Madisonville document resources feed: partial - Official CMS feed exposed 349 files. Recent P&Z packets/minutes plus July, August and September 2026 council packets were downloaded and searched; not every council file was read end-to-end.
  - Madisonville Planning and Zoning packets/minutes: partial - Recent planning files yielded three address-level candidates; coverage is partial because not every file in the 24-month planning window was fully reviewed.
  - Madisonville forms and permits page: partial - Page confirms permit forms/application route but did not expose an issued-permit register in the page HTML checked.
  - Madison County permits page: partial - County page lists application forms for electric, solar, septic, food, driveway and floodplain but no public issued-record register was found in the page.

### Robertson

- Raw records: **13** total (**6** local, **7** statewide TDLR/TABS).
- Dispositions before final review: **9** candidate, **3** watchlist, **1** excluded.
- Source receipts: **8** total; 3 complete, 3 partial, 1 blocked, 1 empty, 0 not checked.
- Coverage read: **mixed; some exhausted sources plus important partial/blocked sources**.
- Main gaps:
  - Robertson CAD property search: partial - CAD was used to match agenda items to ownership and parcel context. EL Construction and Iron Oak parent tract matched; exact Iron Oak lots 114/115, 208 Fulton and LT 9X/LT 9F did not produce clean exact matches in this pass.
  - City of Franklin official agendas: partial - The official agenda page only exposed three recent agenda PDFs in this pass. They were scanned, so images were preserved and reviewed. One City Park pickleball/lighting item was found; Aug. 24 and Sept. 21 did not show construction leads.
  - City of Calvert agendas/minutes and forms/permits: blocked - Official pages and MembershipWare resource metadata were accessible and listed HDC/agendas, but direct blob downloads returned access-denied or viewer shells rather than readable official PDFs. No issued permit register was exposed on the forms/permits page during this pass.
  - City of Bremond official website: empty - The official site was saved and searched for agenda, permit, bid, project and construction terms. Visible navigation/pages did not expose recent address-level building/project records during this pass.

### Washington

- Raw records: **55** total (**20** local, **35** statewide TDLR/TABS).
- Dispositions before final review: **46** candidate, **9** watchlist, **0** excluded.
- Source receipts: **10** total; 1 complete, 8 partial, 0 blocked, 0 empty, 1 not checked.
- Coverage read: **mixed; some exhausted sources plus important partial/blocked sources**.
- Main gaps:
  - TDLR TABS Washington backfill: partial - Official TDLR SearchProjects endpoint returned 28 rows for county id 2239; 25 project detail pages were downloaded and converted to records in this bounded pass.
  - City of Brenham building permits monthly reports: partial - January-August 2026 files are listed; September 2026 was not listed on the archive page at retrieval. June-August official PDFs produced the promoted address-level permit candidates in records.json.
  - Washington CAD official property search: partial - Used official Washington CAD esearch for selected candidate addresses only; 411 Church matched, several additional final targeted pulls returned empty/session responses and were not promoted as matches.
  - Washington County Engineering and Development Services / Road and Bridge: partial - Page identifies permit routes including MGO, floodplain, OSSF, culvert, utility installation and subdivision application, but no issued-record register was found on the page.

## Report Language To Preserve

- Do not say the pilot covered every permit or project in any county.
- Do say the pilot combined selected local official sources with statewide TDLR/TABS registrations.
- Keep registrations, planning cases, permits, historical awards and open bids separate.
- A partial or blocked source means the PDF should expose a gap, not smooth it over.
- Existing local_path evidence was present for every record source checked in this coverage pass, but private paths should not be printed in public-facing PDF output.

