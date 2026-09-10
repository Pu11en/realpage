#!/usr/bin/env python3
"""
STEP 3 (improved): Run vendor detection on all 50 communities with fallback strategies
"""
import csv
import httpx
import time
from pathlib import Path
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

OUTPUT_DIR = Path("/home/drewp/main-projects/realpage/raw/research-01")

# PMS vendor patterns
PMS_PATTERNS = {
    "RealPage": {
        "domains": ["loftliving.com", "realpage.com", "activebuilding.com", "onlineleasing.realpage"],
        "keywords": ["realpage", "onlineleasing", "loftliving", "activebuilding"],
    },
    "Yardi": {
        "domains": ["rentcafe.com", "yardi.com", "securecafe.com"],
        "keywords": ["rentcafe", "yardi", "securecafe"],
    },
    "Entrata": {
        "domains": ["entrata.com", "residentportal.com", "prospectportal.com"],
        "keywords": ["entrata", "residentportal", "prospectportal"],
    },
    "AppFolio": {
        "domains": ["appfolio.com"],
        "keywords": ["appfolio"],
    },
    "Buildium": {
        "domains": ["managebuilding.com"],
        "keywords": ["buildium", "managebuilding"],
    },
    "ResMan": {
        "domains": ["myresman.com", "resman"],
        "keywords": ["resman", "myresman"],
    },
    "MRI/Rent Manager": {
        "domains": ["mrisoftware.com", "rentmanager.com"],
        "keywords": ["mrisoftware", "rentmanager"],
    },
}

def extract_links(html, base_url):
    """Extract all links from HTML."""
    links = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            text = (a.get_text(strip=True) or "")[:100]
            url_href = a["href"]
            if not url_href.startswith("http"):
                if url_href.startswith("/"):
                    parsed = urlparse(base_url)
                    url_href = f"{parsed.scheme}://{parsed.netloc}{url_href}"
                else:
                    url_href = urljoin(base_url, url_href)
            links.append((text, url_href))
    except:
        pass
    return links

def detect_vendor(links_list, page_content):
    """Try to detect PMS vendor from links and page content."""
    vendor_signals = {}

    # Check links for vendor domains
    for text, url in links_list:
        url_lower = url.lower()
        for vendor, patterns in PMS_PATTERNS.items():
            for domain in patterns["domains"]:
                if domain in url_lower:
                    if vendor not in vendor_signals:
                        vendor_signals[vendor] = {"evidence": [], "type": "link"}
                    vendor_signals[vendor]["evidence"].append(url)

    # Check content for vendor keywords
    if page_content:
        content_lower = page_content.lower()
        for vendor, patterns in PMS_PATTERNS.items():
            for keyword in patterns["keywords"]:
                if keyword in content_lower:
                    if vendor not in vendor_signals:
                        vendor_signals[vendor] = {"evidence": [], "type": "keyword"}
                    vendor_signals[vendor]["evidence"].append(f"keyword:{keyword}")

    return vendor_signals

def fetch_and_analyze(url):
    """Fetch a community website and analyze for PMS vendor."""
    # Try multiple headers strategies for blocked sites
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        None,  # Default
    ]

    for ua in user_agents:
        try:
            headers = {}
            if ua:
                headers["User-Agent"] = ua

            response = httpx.get(
                url,
                timeout=15,
                follow_redirects=True,
                headers=headers,
            )

            # If we get 403, try next UA
            if response.status_code == 403:
                continue

            response.raise_for_status()

            links = extract_links(response.text, url)
            vendor_signals = detect_vendor(links, response.text)

            # Check for portal/apply links
            portal_keywords = {"resident", "portal", "pay", "rent", "apply", "leasing", "login", "online"}
            portal_links = []
            for text, link_url in links:
                text_lower = (text or "").lower()
                url_lower = (link_url or "").lower()
                if any(kw in text_lower for kw in portal_keywords) or any(kw in url_lower for kw in portal_keywords):
                    portal_links.append((text, link_url))

            return {
                "success": True,
                "links_count": len(links),
                "portal_links": portal_links,
                "vendor_signals": vendor_signals,
                "first_portal_url": portal_links[0][1] if portal_links else None,
                "blocked": False,
            }
        except Exception as e:
            # Try next UA if we got a specific error
            if "403" in str(e) or "Forbidden" in str(e):
                continue
            # If all UAs failed
            if ua == user_agents[-1]:
                return {
                    "success": False,
                    "error": str(e),
                    "links_count": 0,
                    "portal_links": [],
                    "vendor_signals": {},
                    "blocked": "403" in str(e),
                }

    # All UAs got 403
    return {
        "success": False,
        "error": "All requests blocked (403 Forbidden)",
        "links_count": 0,
        "portal_links": [],
        "vendor_signals": {},
        "blocked": True,
    }

def main():
    # Load communities
    communities = []
    csv_path = OUTPUT_DIR / "R2-communities.csv"
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        communities = list(reader)

    print(f"Analyzing {len(communities)} communities...\n")

    # Track vendor counts
    vendor_counts = {}
    identified_count = 0
    blocked_count = 0

    results = []

    for i, community in enumerate(communities, 1):
        name = community["name"]
        url = community["url"]
        print(f"{i:2}. {name[:50]:50} ", end="", flush=True)

        data = fetch_and_analyze(url)

        if data["success"]:
            print("✓", end="")

            # Determine vendor
            vendor = "unknown"
            evidence_url = None

            if data["vendor_signals"]:
                # Pick the vendor with the strongest signal (link > keyword)
                best_vendor = None
                best_type = None
                for v, signals in data["vendor_signals"].items():
                    if best_type is None or (signals["type"] == "link" and best_type == "keyword"):
                        best_vendor = v
                        best_type = signals["type"]
                        evidence_url = signals["evidence"][0] if signals["evidence"] else None

                if best_vendor:
                    vendor = best_vendor
                    identified_count += 1
                    print(f" → {vendor}")
                else:
                    print(" → unknown")
            else:
                print(" → unknown")

            # Count vendor
            if vendor not in vendor_counts:
                vendor_counts[vendor] = 0
            vendor_counts[vendor] += 1

            results.append({
                "name": name,
                "city": community["city"],
                "url": url,
                "vendor": vendor,
                "evidence_url": evidence_url or "",
                "tool": "httpx",
                "notes": f"{data['links_count']} links, {len(data['portal_links'])} portal links",
            })
        else:
            if data["blocked"]:
                print("B", end="")  # Blocked
                blocked_count += 1
            else:
                print("✗", end="")
            print()

            results.append({
                "name": name,
                "city": community["city"],
                "url": url,
                "vendor": "blocked" if data["blocked"] else "error",
                "evidence_url": "",
                "tool": "httpx",
                "notes": data.get("error", ""),
            })

        time.sleep(0.3)

    # Save results
    output_file = OUTPUT_DIR / "R2-results.csv"
    with open(output_file, "w") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "city", "url", "vendor", "evidence_url", "tool", "notes"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    # Summary
    print("\n\n=== SUMMARY ===")
    print(f"Total analyzed: {len(communities)}")
    print(f"Identified: {identified_count} ({100*identified_count/len(communities):.0f}%)")
    print(f"Blocked by bot protection: {blocked_count}")
    print(f"\nVendor breakdown (identified only):")
    for vendor, count in sorted(vendor_counts.items(), key=lambda x: -x[1]):
        if vendor not in ("blocked", "error"):
            print(f"  {vendor:20} {count:3}")

    print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    main()
