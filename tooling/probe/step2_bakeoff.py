#!/usr/bin/env python3
"""
STEP 2: Tool bake-off on first 10 communities.
Compare: plain httpx+BeautifulSoup, Jina Reader, crawl4ai AsyncWebCrawler
"""
import csv
import httpx
import asyncio
import time
import json
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler

# Load API key
env_path = Path("/home/drewp/main-projects/realpage/.env")
API_KEY = None
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.startswith("JINA_API_KEY="):
                API_KEY = line.split("=", 1)[1].strip()
                break

OUTPUT_DIR = Path("/home/drewp/main-projects/realpage/raw/research-01")

# Load communities
communities = []
csv_path = OUTPUT_DIR / "R2-communities.csv"
with open(csv_path) as f:
    reader = csv.DictReader(f)
    communities = list(reader)[:10]  # First 10

print(f"Testing {len(communities)} communities\n")

# Keywords for portal/apply links
PORTAL_KEYWORDS = {"resident", "portal", "pay", "rent", "apply", "leasing", "login", "online"}

def find_portal_links(links_list, base_url):
    """Check if any link matches portal/apply keywords."""
    portal_links = []
    for link_text, link_url in links_list:
        text_lower = (link_text or "").lower()
        url_lower = (link_url or "").lower()

        # Check for resident portal / pay rent / current residents
        if any(kw in text_lower for kw in PORTAL_KEYWORDS):
            portal_links.append((link_text, link_url))
        if any(kw in url_lower for kw in PORTAL_KEYWORDS):
            portal_links.append((link_text, link_url))

    return list(set(portal_links))

# TOOL A: httpx + BeautifulSoup
async def tool_httpx(url):
    """Plain httpx GET + BeautifulSoup"""
    try:
        start = time.time()
        response = httpx.get(url, timeout=15, follow_redirects=True, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        elapsed = time.time() - start

        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            text = (a.get_text(strip=True) or "")[:100]
            url_href = a["href"]
            if not url_href.startswith("http"):
                if url_href.startswith("/"):
                    base_parsed = urlparse(url)
                    url_href = f"{base_parsed.scheme}://{base_parsed.netloc}{url_href}"
            links.append((text, url_href))

        portal = find_portal_links(links, url)
        return {"success": True, "seconds": elapsed, "links_count": len(links), "portal_found": bool(portal), "portal_links": portal}
    except Exception as e:
        return {"success": False, "seconds": 0, "error": str(e)}

# TOOL B: Jina Reader
async def tool_jina(url):
    """Jina Reader API"""
    try:
        start = time.time()
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "X-With-Links-Summary": "true",
            "X-Retain-Images": "none",
            "Accept": "application/json",
        }
        response = httpx.get(f"https://r.jina.ai/{url}", headers=headers, timeout=15)
        elapsed = time.time() - start

        data = response.json()
        links = []
        if "data" in data and "links" in data["data"]:
            for link in data["data"]["links"]:
                text = (link.get("title", "") or "")[:100]
                link_url = link.get("url", "")
                links.append((text, link_url))

        portal = find_portal_links(links, url)
        return {"success": True, "seconds": elapsed, "links_count": len(links), "portal_found": bool(portal), "portal_links": portal}
    except Exception as e:
        return {"success": False, "seconds": 0, "error": str(e)}

# TOOL C: crawl4ai
async def tool_crawl4ai(url):
    """crawl4ai AsyncWebCrawler"""
    try:
        start = time.time()
        async with AsyncWebCrawler(headless=True) as crawler:
            result = await crawler.arun(url=url, timeout=15)
        elapsed = time.time() - start

        links = result.links or []
        portal = find_portal_links(links, url)
        return {"success": True, "seconds": elapsed, "links_count": len(links), "portal_found": bool(portal), "portal_links": portal}
    except Exception as e:
        return {"success": False, "seconds": 0, "error": str(e)}

async def test_all():
    """Run all three tools on all 10 sites."""
    results = []

    for i, community in enumerate(communities, 1):
        name = community["name"]
        url = community["url"]
        print(f"{i}. {name[:50]}")
        print(f"   URL: {url}")

        # Test httpx
        print("   Testing httpx...", end=" ", flush=True)
        httpx_result = await tool_httpx(url)
        print(f"OK ({httpx_result['seconds']:.1f}s)" if httpx_result["success"] else "FAIL")

        # Test Jina
        print("   Testing Jina...", end=" ", flush=True)
        jina_result = await tool_jina(url)
        print(f"OK ({jina_result['seconds']:.1f}s)" if jina_result["success"] else "FAIL")

        # Test crawl4ai
        print("   Testing crawl4ai...", end=" ", flush=True)
        crawl4ai_result = await tool_crawl4ai(url)
        print(f"OK ({crawl4ai_result['seconds']:.1f}s)" if crawl4ai_result["success"] else "FAIL")

        results.append({
            "name": name,
            "url": url,
            "httpx": httpx_result,
            "jina": jina_result,
            "crawl4ai": crawl4ai_result,
        })
        print()

    return results

# Run the bake-off
results = asyncio.run(test_all())

# Save results
output_file = OUTPUT_DIR / "R2-bakeoff.csv"
with open(output_file, "w") as f:
    f.write("name,url,tool,success,seconds,links_count,portal_found\n")
    for r in results:
        for tool_name in ["httpx", "jina", "crawl4ai"]:
            tool_data = r[tool_name]
            f.write(f'"{r["name"]}",{r["url"]},{tool_name},{tool_data.get("success", False)},{tool_data.get("seconds", 0)},{tool_data.get("links_count", 0)},{tool_data.get("portal_found", False)}\n')

print(f"\nBake-off results saved to {output_file}")

# Summary
print("\n=== SUMMARY ===")
for tool_name in ["httpx", "jina", "crawl4ai"]:
    success_count = sum(1 for r in results if r[tool_name]["success"])
    portal_count = sum(1 for r in results if r[tool_name].get("portal_found", False))
    avg_time = sum(r[tool_name].get("seconds", 0) for r in results) / len(results)
    print(f"{tool_name.upper():12} Success: {success_count:2}/10  Portal found: {portal_count:2}/10  Avg time: {avg_time:.1f}s")
