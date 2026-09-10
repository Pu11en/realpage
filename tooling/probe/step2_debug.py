#!/usr/bin/env python3
"""
Debug why Jina and crawl4ai are failing
"""
import httpx
import asyncio
from pathlib import Path
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

print(f"API Key: {API_KEY[:20]}...")

test_url = "https://www.fallsonclearwoodapts.com/"

# Test Jina
print("\n=== Testing Jina Reader ===")
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "X-With-Links-Summary": "true",
    "X-Retain-Images": "none",
    "Accept": "application/json",
}

try:
    response = httpx.get(f"https://r.jina.ai/{test_url}", headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test crawl4ai
print("\n=== Testing crawl4ai ===")

async def test_crawl4ai():
    try:
        async with AsyncWebCrawler(headless=True) as crawler:
            result = await crawler.arun(url=test_url, timeout=15)
            print(f"Success: {bool(result)}")
            if result:
                print(f"Links: {len(result.links)}")
                print(f"First 3 links: {result.links[:3]}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_crawl4ai())
