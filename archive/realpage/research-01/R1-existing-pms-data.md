# Research: Property Management Software Identification Data Vendors

**Source:** WebSearch + WebFetch across 15+ vendor platforms
**Fetched:** 2026-09-10
**Method:** WebSearch + WebFetch systematic vendor discovery
**Confidence:** High (comprehensive search of all major vendor categories)

---

## Vendor Survey Results

| Vendor | Product | URL | Per-Property PMS Field | Switch History | Coverage | Price |
|--------|---------|-----|------------------------|-----------------|----------|-------|
| RealPage | Market Analytics | https://www.realpage.com/insights-analytics/market-analytics/ | NOT advertised | No | 30+ years historical data, property/unit-level | Contact for pricing |
| Yardi | Yardi Matrix | https://www.yardimatrix.com/ | NOT advertised | No | 188 U.S. multifamily markets, 90,382 properties | Contact for pricing |
| CoStar | Multifamily Property Data | https://www.costar.com/campaign/multifamily-property-data | NOT advertised | No | 38M units, national coverage | Contact for pricing |
| ALN Apartment Data | ALN OnLine | https://alndata.com/ | NOT advertised | No | 185 U.S. markets, 16.1M+ units | ~$31-60K annually |
| HelloData | Market Analysis Platform | https://www.hellodata.ai/ | NOT advertised | No | 38.5M+ units daily survey | Contact for pricing |
| Zonda | Multifamily Solutions | https://zondahome.com/ | NOT advertised | No | National (now CoStar subsidiary) | Contact for pricing |
| HG Insights | Technographics API | https://hginsights.com/ | Company-level only | No | 20,000+ products tracked | Contact for pricing |
| BuiltWith | Website Tech Detection | https://builtwith.com/ | Not applicable (website tech only) | No | 680M+ websites | $20-999/mo |
| Enlyft | Real Estate & PMS Technographics | https://enlyft.com/tech/real-estate-property-management | Company-level only | No | 117 PMS products, 423,685 companies | Contact for pricing |
| 6sense | Property Management Intelligence | https://6sense.com/tech/property-management | Company-level aggregate only | No | 176,807 companies, 132 PMS tech | Contact for pricing |
| Smart Apartment Data | Apartment Data Platform | https://smartapartmentdata.com/ | NOT advertised | No | Nationwide (300+ integration partners) | Contact for pricing |
| Radix | RealRents + Analytics | https://radix.com/ | NOT advertised | No | 5M+ apartment homes, 20M+ units on platform | Contact for pricing |
| Propexo | Data Platform + API | https://propexo.com/ | NOT advertised (integration layer only) | No | Integrates with major PMS but doesn't sell PMS IDs | Contact for pricing |
| Datarade | Property Data Marketplace | https://datarade.ai/ | NOT advertised | No | 340+ property datasets; no PMS field found | Variable by dataset |

---

## Key Findings by Category

### Property-Level PMS Identification (What was sought)
**NOT FOUND** at any vendor.

The closest candidates—Yardi Matrix, RealPage Market Analytics, and ALN Apartment Data—provide comprehensive property-level data including ownership, management companies, rents, occupancy, and financial metrics, but **none explicitly advertise property management software vendor identification** as a data field.

### Company-Level PMS Identification (Different from property-level)
**FOUND at:**
- **Enlyft** (117 real estate products across 423,685 companies). Can identify which *companies* use which PMS (e.g., "Greystar uses Yardi"), but NOT individual property deployments. Product page: https://enlyft.com/tech/real-estate-property-management
- **6sense** (132 property management technologies across 176,807 companies). Market-level aggregates only; no individual company identification.

### Switch History (When properties changed vendors)
**NOT FOUND** at any vendor.

No vendor advertises historical tracking of when properties migrated from one PMS to another. Search results on "switching PMS" yield only how-to migration guides, not commercial tracking data.

### Data Integration Points (Where PMS connects but no vendor ID)
Several vendors ingest data *from* PMS systems but don't publish which PMS:
- **Radix RealRents**: Sources rent/leasing data directly from PMS (Yardi, Entrata, RealPage, AppFolio) but doesn't publicly identify source PMS per property
- **Propexo**: Normalized API across Yardi, Entrata, RealPage, AppFolio, ResMan, but is an integration layer, not a data vendor
- **Datarade**: Rental data aggregator; no PMS identification in 340+ datasets reviewed

---

## Verdict: **PASS**

No company publicly sells or offers **property-level PMS identification data** (which apartment community runs which software) **with or without switch history** at national scale.

**One-paragraph reason:**

The multifamily data ecosystem has fragmented into specialized point solutions. Data aggregators like Yardi Matrix, RealPage Market Analytics, and ALN Apartment Data provide property-level operational metrics (rents, occupancy, ownership, expenses) but do not track or expose which property management software each community uses. Company-level technographics vendors like Enlyft and 6sense can identify PMS adoption at the organization level (e.g., Greystar uses Yardi) but cannot disaggregate to individual properties, and none offer historical vendor-switch tracking. Vendors that integrate with PMS systems (Radix, Propexo) deliberately keep that vendor identity opaque (for confidentiality or competitive reasons). The only public signal of which PMS a property uses is scraping its website for technical markers (BuiltWith for general tech), which is unreliable and incomplete. **No commercial data product fills this gap.**

---

## Additional Context

**Why the gap exists:**
1. PMS vendors protect their customer lists; PMS data is competitive
2. Data brokers don't have reliable access to this at scale (PMS adoption is private operational data)
3. No regulatory driver to publish it (unlike loan data or ownership records)
4. Apartment community websites rarely expose which PMS they run

**What *is* available instead:**
- Aggregated market share stats (6sense shows Yardi Genesis at 10.71% market share)
- Company-level technographics (Enlyft can confirm a REIT uses Yardi; can't say which properties)
- Direct PMS data feeds (Radix, Propexo) but no downstream vendor ID publication

