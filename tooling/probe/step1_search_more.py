#!/usr/bin/env python3
"""
Additional searches to get closer to 50 communities
"""
import httpx
import json
import time
import csv
from pathlib import Path
from urllib.parse import urlparse

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

# Load existing communities
existing_urls = set()
csv_path = OUTPUT_DIR / "R2-communities.csv"
if csv_path.exists():
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_urls.add(row["url"])

print(f"Existing communities: {len(existing_urls)}")

SKIP_DOMAINS = {
    "apartments.com",
    "zillow.com",
    "rent.com",
    "apartmentlist.com",
    "trulia.com",
    "redfin.com",
    "realtor.com",
    "yelp.com",
    "facebook.com",
    "forrent.com",
    "apartmentguide.com",
    "hotpads.com",
    "craigslist.org",
    "umovefree.com",
    "irtliving.com",
    "willowbridgepc.com",
}

def is_valid_url(url, name=None):
    """Check if URL is an official community website."""
    if not url or url in existing_urls:
        return False
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().lstrip("www.")

        # Skip aggregators
        if any(skip in domain for skip in SKIP_DOMAINS):
            return False

        # Only accept http/https
        if parsed.scheme not in ("http", "https"):
            return False

        return True
    except:
        return False

def search_jina(query):
    """Search using Jina Search API."""
    url = "https://s.jina.ai/"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
        "X-Respond-With": "no-content",
    }

    try:
        response = httpx.get(
            url,
            params={"q": query},
            headers=headers,
            timeout=30,
        )
        if response.status_code != 200:
            return []

        data = response.json()
        results = []
        if "data" in data and isinstance(data["data"], list):
            for result in data["data"]:
                title = result.get("title", "")
                result_url = result.get("url", "")
                if result_url and is_valid_url(result_url, title):
                    results.append((title, result_url))

        return results
    except:
        return []

# More targeted queries
EXTRA_QUERIES = [
    "MAA apartments Richardson Plano",
    "Tricon apartments Richardson TX",
    "Markel apartments Plano TX",
    "Camden apartments Richardson Plano",
    "Bluerock apartments Plano",
    "Preferred apartments Richardson TX",
    "Avanath apartments Plano TX",
    "Lennar apartments Richardson Plano",
]

new_communities = {}
for query in EXTRA_QUERIES:
    print(f"Query: {query}")
    results = search_jina(query)
    for title, url in results:
        if url not in existing_urls and url not in new_communities:
            new_communities[url] = (title, "Mixed")
            print(f"  Found: {title[:40]}")
    time.sleep(1.1)

print(f"\nNew communities found: {len(new_communities)}")

# Append to CSV
if new_communities:
    with open(csv_path, "a") as f:
        for url, (name, city) in new_communities.items():
            f.write(f'"{name}","Mixed",{url}\n')

total = len(existing_urls) + len(new_communities) - 1  # -1 for header
print(f"Total communities: {total}")
