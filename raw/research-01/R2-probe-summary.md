# PMS Vendor Detection Feasibility Probe - Round 2

**Source:** 50 apartment communities (25 targeted Richardson TX + 25 targeted Plano TX area)  
**Fetched:** 2026-09-10  
**Method:** Jina Search API for discovery + httpx + BeautifulSoup for analysis  
**Confidence:** Medium (42% identified; limited by bot protection and JS-heavy sites)

---

## STEP 1: Community Discovery

Successfully identified 50 apartment communities using Jina Search API:
- Initial search: 50 valid communities after filtering aggregators
- Search queries: Location + property type variations (apartments, luxury, residential, multifamily)
- Filtering: Removed apartments.com, zillow.com, rentcafe.com, yelp.com, LinkedIn, and other non-primary-site domains

**Communities by location:**
- Mixed/Plano area: 34
- Richardson area: 16
- (Note: Many found under "Plano/Mixed" due to search query variations)

---

## STEP 2: Tool Bake-Off (First 10 Sites)

Tested three tools for extracting links and detecting portal/apply links:

| Tool | Success Rate | Portal Found | Avg Time | Notes |
|------|--------------|--------------|----------|-------|
| **httpx + BeautifulSoup** | 10/10 (100%) | 4/10 (40%) | 0.2s | **WINNER** - Fast, reliable, extracts static HTML |
| Jina Reader API | 0/10 (0%) | 0/10 (0%) | - | Authentication issues or empty responses |
| crawl4ai AsyncWebCrawler | 0/10 (0%) | 0/10 (0%) | - | Timeouts / crash on link extraction |

**Winner:** httpx + BeautifulSoup

**Rationale:** 
- Only tool with consistent success
- Fastest (200ms avg per site)
- 40% found portal links on first 10 sites (vs 0% for others)
- Main limitation: Misses JavaScript-rendered content (many modern apartment sites load via JS)

---

## STEP 3: Vendor Detection Across All 50 Communities

**Tool used:** httpx + BeautifulSoup (with multi-strategy fallback for blocked sites)

**Results Overview:**
- Total analyzed: 50 communities
- Successfully fetched: 37 (74%)
- Blocked by bot protection (403): 13 (26%)
- Failed to fetch: 1 (2%)

**Vendor Identification:**
- **Identified:** 21 communities (42%)
- **Unknown:** 15 communities (30%)
- **Blocked/Error:** 14 communities (28%)

**Vendor Breakdown (identified only):**
- RealPage: 11 (52%)
- Yardi: 7 (33%)
- Entrata: 3 (14%)
- AppFolio: 0
- Buildium: 0
- ResMan: 0
- MRI/Rent Manager: 0

**Evidence URLs Found:**
- RealPage: loftliving.com, realpage.com, onlineleasing.realpage
- Yardi: securecafe.com, rentcafe.com
- Entrata: residentportal.com, prospectportal.com

---

## Key Findings

### Bot Protection: 26% of sites block automated access
13 sites returned 403 Forbidden even with multiple User-Agent variations:
- Architectural/design-focused (e.g., beltan.com, marquiswaterview.com)
- Older platform migrations (e.g., legendsatchaseoaks.com)
- Likely use Cloudflare or Akamai anti-bot protection

**Impact:** These blocked sites cannot be analyzed with plain HTTP fetching; headless browser required

### JavaScript-Heavy Sites: ~30% unidentified
Sites with no vendor signals extracted despite successful fetch:
- Anthem Cityline, Axis 110, Cortland properties, Westside, etc.
- Likely load resident portal links via JavaScript (e.g., React, Vue)
- httpx misses these; crawl4ai headless approach would find them

### Vendor Concentration:
- RealPage dominates (52% of identified)
- Yardi strong second (33%)
- Entrata present (14%)
- No AppFolio, Buildium, ResMan, or MRI detected in sample

---

## Problems & Limitations

1. **Bot Protection (26% of sites)** - 13 sites actively block HTTP clients
   - Fix: Use headless browser (Playwright/Puppeteer via crawl4ai)
   - Trade-off: Much slower (2-6s per site vs 0.2s with httpx)

2. **JavaScript-Rendered Content** - ~15% of sites load portal links via JS
   - httpx can't execute JS; misses dynamic links
   - Jina Reader API returned 401 auth errors or empty responses in testing
   - crawl4ai would work but had implementation issues in bake-off

3. **Vendor Coverage** - Only 4 of 7+ PMS vendors detectable
   - Missing: AppFolio, Buildium, ResMan, MRI
   - Suggests these vendors less common in Dallas area (or different link patterns)

4. **Data Quality**  
   - Some sites in "unknown" might have portal portals, just via JS or hidden from static HTML
   - 403-blocked sites impossible to classify without alternate approach

---

## Verdict: **FIX** (42% identified)

**Threshold:** 70% for PASS | 50-70% for FIX | <50% for KILL  
**Result:** 42% identified = FIX

### To Achieve PASS (70%+):

1. **Implement crawl4ai properly** (or Playwright headless) for all sites
   - Solves JS-rendering issue
   - Can bypass some bot protection with browser fingerprint
   - Cost: 2-6s per site instead of 0.2s (250x slower)

2. **Handle 403 blocks gracefully**
   - Accept that 26% of sites won't cooperate
   - Use cached link patterns, whois data, or reverse-IP lookup
   - Or focus on Yardi/RealPage detection (85% of market in sample) and accept 20% unknowns

3. **Improve Jina Reader integration**
   - Current implementation failed; might be API auth or parsing issue
   - If fixed, could be faster than crawl4ai for JS sites

4. **Add vendor pattern expansion**
   - Discover patterns for AppFolio, Buildium, ResMan, MRI
   - Check company websites, SEC filings, or partner lists

---

## Jina Search API Usage

- Queries run: 25 (5 Richardson x 5 base queries + additional targeted searches)
- Credits consumed: ~500-750 (est. 20-30 credits per search)
- Status: All searches successful; no errors

---

## Recommendations for Next Phase

1. **Quick win (60% + time-efficient):**
   - Stick with httpx for fetchable sites
   - Accept 26% bot-protected sites as "unknown"
   - Focus confidence on RealPage/Yardi detection (both highly linkable)
   - Result: 42% confidently identified, 26% blocked, 32% JS/other

2. **Complete solution (70%+ but 10x slower):**
   - Add Playwright-based crawl4ai for all sites
   - Parallel execution to mitigate speed penalty
   - Classify all sites; confidently identify most
   - Cost: 5-10 hours run time for 50 sites

3. **Hybrid approach (65% + balanced):**
   - Use httpx first (fast, 0.2s)
   - For sites with no vendor signals AND not blocked: run crawl4ai (2s)
   - Result: ~65% identified, reasonable speed


## Correction — Jina re-run (main session, 2026-09-10)

The bake-off's Jina and crawl4ai rows (0/10) were a bug in the probe script, not a tool failure. Jina Reader works: re-run on all 50 via `tooling/probe/jina_classify.py`, output `R2-jina-results.csv`.

- All 50 fetched (HTTP 200, no blocks via Jina). **24/50 identified**: Yardi 17, RealPage 6, Entrata 1. Nearly all came from resident-login or pay-rent links (23 portal, 1 asset).
- **About 9 of the 26 unknowns are bad list rows**: duplicates, index/contact pages, a Facebook page, a truncated URL. On roughly 41 valid community sites, that's **~59% identified → FIX**.
- **The remaining unknowns are big operators with white-labeled portals**: Camden (mycamden.com), UDR, Cortland (Funnel leasing), Greystar (greystar.com portal). Also seen: leaselabs.com (a RealPage-owned website builder), yotta, repli360.
- Fix ideas: (1) one extra hop into the operator's resident-login page; (2) map operator → PMS at the company level from public sources for the big white-label operators; (3) build a clean community list with no duplicates or non-community pages.
- Tool verdict: **Jina Reader is the primary tool** (handles JavaScript and bot walls, ~5 parallel requests). Plain httpx works as a free first pass on static sites.
