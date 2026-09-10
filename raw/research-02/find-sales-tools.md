# Free/Open-Source Tools for Detecting Apartment Sales in Plano TX & Richardson TX

**Source:** Web research (WebFetch + WebSearch)  
**Fetched:** 2026-09-10  
**Method:** County clerk official records, Socrata Open Data API, GitHub open-source, broker press releases  
**Confidence:** High for clerk records, CAD metadata; Medium for update frequency (no published SLA)

---

## 1. Collin CAD Dataset (data.texas.gov)

### Dataset IDs & Availability
- **2026:** `5tkr-3759` (current)
- **2025:** `vffy-snc6` (prior year for owner history)
- **2024:** `6dqt-e958` (prior year for owner history)
- **URL:** https://data.texas.gov/dataset/Collin-CAD-Appraisal-Data-2026/5tkr-3759

### Update Frequency
- **Claimed:** Daily (per data.texas.gov search result)
- **Actual:** Last API metadata shows `rowsUpdatedAt` ~July 9, 2026 (no explicit SLA published)
- **Weakness:** No documented refresh schedule; CAD updates may lag 2–6 weeks behind deed filing

### Fields Available
- `ownername` (current owner only)
- `deedeffdate`, `deedfiledate` (most recent deed dates)
- `deedtypecd` (deed type)
- **Missing:** Sale price (Texas non-disclosure state), prior owners

### How to Get Previous Owner
1. Download 2026 & 2025 datasets via Socrata API or manual export
2. Join on `parcelid` (property identifier)
3. Compare `ownername` across years to detect ownership change
4. Cross-reference with deed date to confirm sale

### Socrata API Access
- Endpoint: `https://data.texas.gov/api/views/5tkr-3759/rows.json`
- No authentication required; free bulk export available
- **Tool:** [libbyh/socrata_scraper](https://github.com/libbyh/socrata_scraper) or [CSAIL-LivingLab/socrata_scraper](https://github.com/CSAIL-LivingLab/socrata_scraper) for change detection

### Expected Detection Delay
**2–8 weeks** (CAD updates lag deed filing; prior-year comparison adds delay)

---

## 2. Collin County Clerk & Dallas County Clerk Online Records

### Collin County Clerk (Free)
- **URL:** https://www.collincountytx.gov/County-Clerk/land-recordings
- **Search Access:** Free 24/7 online search (guest or registered user)
- **Searchable By:** Grantor name, grantee name, document type, date range, instrument number
- **Document Types:** Deeds, liens, releases
- **Coverage:** January 2006 to present
- **Instrument Numbers:** 
  - Pre-May 2, 2022: 17 digits (format: YYYYMMDDXXXXXXX)
  - May 2, 2022+: 13 digits (format: YYYYXXXXXXX)
- **API/Bulk Export:** No official API; bulk export available on request
- **Contact:** 972-548-4185 | 2300 Bloomdale Road, Suite 2104, McKinney, TX 75071

### Dallas County Clerk (Free)
- **URL:** https://www.dallascounty.org/services/record-search/
- **Search Access:** Free online 24/7 (non-certified records)
- **Searchable By:** Grantor, grantee, document type, recording date, instrument number
- **Coverage:** 1964 to present
- **API/Bulk Export:** No official API
- **Note:** Required for Richardson TX (in Dallas County) apartment properties

### Detection Method: Deed Filing Search
1. Search by **grantee name** (buyer LLC or entity name) with date filter
2. Filter by document type: `DEED` or `WARRANTY DEED`
3. Dates: Sales typically appear **3–10 days** after closing
4. **Advantage:** Captures grantor/grantee names; faster than CAD
5. **Challenge:** Requires knowing buyer/seller entity names (not always available in advance)

### Expected Detection Delay
**3–10 days** after closing (real-time compared to CAD)

---

## 3. Other Public Signals for Apartment Sales

### A. News & Broker Press Releases
- **Dallas Business Journal:** https://www.bizjournals.com/dallas/
- **CoStar News:** https://www.costargroup.com/ (subscription)
- **Broker networks:** Northmarq, Berkadia, JLL, CBRE, Walker & Dunlop publish transaction announcements
  - Example: [Northmarq Tides at Plano sale](https://www.northmarq.com/transactions/tides-plano-debt-sale-2024-12) (2024)
  - [IPA Texas team $1.9B in deals](https://www.connectcre.com/awards/2026-top-broker-awards/texas-2/ipas-texas-team-generates-1-9-billion-in-deals-closing-35-transactions/)
- **Expected delay:** 1–3 weeks post-close

### B. Texas Secretary of State LLC Filings
- **URL:** https://www.sos.state.tx.us/corp/sosda/index.shtml (SOSDirect)
- **Access:** Free search by entity name; $1/search to order certificate
- **Limitation:** Ownership details hidden; only registered agent visible
- **Use case:** Detect new special-purpose entity (SPE) formation near closing date
- **Expected delay:** 3–14 days after filing

### C. Property Tax Notices & Appraisal Updates
- Collin CAD publishes appraisal notices (separate dataset)
- New ownership reflected in next annual notice cycle (~3–6 months)

---

## 4. GitHub Open-Source Tools & Libraries

### Top Recommended Tools

| Repo | What It Does | Last Updated | Language | Use Case |
|------|-------------|--------------|----------|----------|
| [chanderbhanswami/texas-data-scraper](https://github.com/chanderbhanswami/texas-data-scraper) | Scrapes Socrata Open Data Portal (Franchise Tax, Sales Tax) + Texas Comptroller API; intelligent deduplication + Google Places API enrichment | 2026 (v1.5.1 - active) | Python | Batch scrape CAD data; detect owner changes |
| [libbyh/socrata_scraper](https://github.com/libbyh/socrata_scraper) | Generic Python scraper for any Socrata-based platform (data.texas.gov) | Inactive (1 commit) | Python | Quick polls of CAD dataset; Git scraping for change detection |
| [CSAIL-LivingLab/socrata_scraper](https://github.com/CSAIL-LivingLab/socrata_scraper) | Socrata-specific scraper with single-threaded default | Minimal activity | Python | Lightweight change detection for CAD |
| [ZacharyHampton/HomeHarvest](https://github.com/ZacharyHampton/HomeHarvest) | Scrapes MLS + real estate listing sites (Zillow, Realtor.com); covers Austin, TX | Active | Python | Listing-based sale detection (no price, TX non-disclosure) |
| [biglocalnews/court-scraper](https://github.com/biglocalnews/court-scraper) | General US county court case scraper; PyPI package | Active (176 commits) | Python | Potential for deed record extension (county clerk ≠ court) |

### Secondary / Alternative Tools
- [mominurr/Real-Estate-Web-Scraping](https://github.com/mominurr/Real-Estate-Web-Scraping) — Zillow/Realtor.com scraper; bypasses IP blocking
- [codefornola/assessor-scraper](https://github.com/codefornola/assessor-scraper) — Assessor site scraper + PostgreSQL export

---

## Recommendation: Hybrid Detection Stack

### Primary Source: Collin County Clerk Online Records (3–10 day delay)
1. **Why:** Fastest public source; captures deed filings same-day filing
2. **Method:** 
   - Set up daily grantee name search for known buyer/investor entities
   - Or monitor for property address via instrument search
   - Manually review or parse deed images for confirmation
3. **Cost:** Free
4. **Automation:** No official API → requires web scraping or manual polling
5. **Challenge:** Requires knowing buyer entity name in advance

### Backup Source: Collin CAD Dataset (2–8 week delay)
1. **Why:** Captures all sales automatically via owner change detection
2. **Method:**
   - Use [texas-data-scraper](https://github.com/chanderbhanswami/texas-data-scraper) for Socrata polling
   - Pull 2026 & 2025 datasets; join on parcelid; detect new ownername entries
   - Cross-reference with deedeffdate to confirm timing
3. **Cost:** Free
4. **Automation:** Fully automatable; script runs weekly
5. **Gap:** Detects change after CAD processes deed (2–8 week lag)

### Previous Owner Lookup
- **Method:** Download CAD datasets (2026, 2025, 2024) via Socrata API
- **Tool:** [texas-data-scraper](https://github.com/chanderbhanswami/texas-data-scraper) or manual CSV join
- **Timeline:** Compare yearly snapshots; no intra-year tracking
- **Limitation:** If property changed hands in prior year, 2024 data shows older owner

### For Richardson TX (Dallas County portion)
- Use Dallas County Clerk search (https://www.dallascounty.org/services/record-search/) with same grantee approach

### Alternative Triggers (If Entity Name Unknown)
1. Monitor broker press releases (Northmarq, Berkadia) → 1–3 week delay
2. Search Dallas Business Journal for "Plano apartment sold" → 1–3 week delay
3. Set up Google Alerts for keywords: `"Plano apartment" "sold"`, `"Richardson apartment" "acquisition"`

### Expected Detection Timeline
- **Ideal (if buyer entity known):** 3–10 days (county clerk deed search)
- **Moderate:** 2–8 weeks (CAD owner change detection + deedeffdate cross-check)
- **Fallback:** 1–3 weeks (news/press release)

---

## Summary Table

| Data Source | Update Freq | Searchable By | Price Data | Detection Delay | Cost | API |
|-------------|------------|---------------|-----------|-----------------|------|-----|
| Collin CAD (data.texas.gov) | Daily (claimed) | Owner name, property ID | ❌ (TX non-disclosure) | 2–8 weeks | Free | Yes (Socrata) |
| Collin County Clerk | Real-time | Grantee, date, instrument # | ❌ | 3–10 days | Free | ❌ (web scrape) |
| Dallas County Clerk | Real-time | Grantee, date, instrument # | ❌ | 3–10 days | Free | ❌ (web scrape) |
| Broker press releases | Ad-hoc | Deal name, date | Sometimes | 1–3 weeks | Free | ❌ |
| Texas Secretary of State LLC | Real-time | Entity name | ❌ (ownership hidden) | 3–14 days | Free (search) | Limited |
| News (DBJ, CoStar, etc.) | Ad-hoc | Property name, deal size | Sometimes | 1–3 weeks | Free/subscription | ❌ |

---

## References & URLs

1. Collin CAD 2026 Dataset: https://data.texas.gov/dataset/Collin-CAD-Appraisal-Data-2026/5tkr-3759
2. Collin CAD 2025 Dataset: https://data.texas.gov/dataset/Collin-CAD-Appraisal-Data-2025/vffy-snc6
3. Collin CAD 2024 Dataset: https://data.texas.gov/dataset/Collin-CAD-Appraisal-Data-2024/6dqt-e958/explore
4. Collin County Clerk Land Recordings: https://www.collincountytx.gov/County-Clerk/land-recordings
5. Dallas County Clerk Record Search: https://www.dallascounty.org/services/record-search/
6. Texas Non-Disclosure State Info: https://www.redfin.com/blog/non-disclosure-states-real-estate/
7. Texas Secretary of State LLC Search: https://www.sos.state.tx.us/corp/sosda/index.shtml
8. GitHub: texas-data-scraper: https://github.com/chanderbhanswami/texas-data-scraper
9. GitHub: libbyh/socrata_scraper: https://github.com/libbyh/socrata_scraper
10. GitHub: CSAIL-LivingLab/socrata_scraper: https://github.com/CSAIL-LivingLab/socrata_scraper
11. GitHub: court-scraper: https://github.com/biglocalnews/court-scraper
12. Northmarq Plano Transaction Example: https://www.northmarq.com/transactions/tides-plano-debt-sale-2024-12
