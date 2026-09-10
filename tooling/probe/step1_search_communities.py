#!/usr/bin/env python3
"""
STEP 1: Search for 50 apartment communities in Richardson TX and Plano TX
using Jina Search API. Extract official website URLs.
"""
import httpx
import json
import time
import os
from urllib.parse import urlparse
from pathlib import Path

# Load API key directly from .env file
env_path = Path("/home/drewp/main-projects/realpage/.env")
API_KEY = None
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.startswith("JINA_API_KEY="):
                API_KEY = line.split("=", 1)[1].strip()
                break

print(f"API Key loaded: {bool(API_KEY)}")
print(f"API Key: {API_KEY[:20]}..." if API_KEY else "NO KEY")

OUTPUT_DIR = Path("/home/drewp/main-projects/realpage/raw/research-01")

# Queries to search for apartments
RICHARDSON_QUERIES = [
    "apartments Richardson TX 75080 official website",
    "apartment homes Richardson TX 75081",
    "luxury apartments Richardson TX 75082",
    "residential apartments Richardson TX",
    "apartment communities Richardson Texas",
    "apartments for rent Richardson TX 75080",
    "apartments for rent Richardson TX 75081",
    "apartments for rent Richardson TX 75082",
    "apartment complex Richardson TX",
    "multifamily Richardson TX",
]

PLANO_QUERIES = [
    "apartments Plano TX 75023 official website",
    "apartment homes Plano TX 75024",
    "luxury apartments Plano TX 75025",
    "residential apartments Plano TX 75074",
    "apartment communities Plano Texas 75075",
    "apartments for rent Plano TX 75023",
    "apartments for rent Plano TX 75024",
    "apartments for rent Plano TX 75025",
    "apartment complex Plano TX",
    "multifamily Plano TX",
]

# Aggregators to skip
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
    "greystar.com",
}

def is_valid_url(url, name=None):
    """Check if URL is an official community website (not an aggregator)."""
    if not url:
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
        print(f"    Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"    Error: {response.text[:200]}")
            return []

        data = response.json()

        results = []
        if "data" in data:
            # Data is a list of results
            data_results = data["data"]
            if isinstance(data_results, list):
                for result in data_results:
                    title = result.get("title", "")
                    result_url = result.get("url", "")
                    if result_url and is_valid_url(result_url, title):
                        results.append((title, result_url))

        return results
    except Exception as e:
        print(f"    Jina search error: {e}")
        return []

def main():
    print("STEP 1: Searching for apartment communities...")

    communities = {}  # URL -> (name, city)

    # Search Richardson
    print("\nSearching Richardson TX...")
    for query in RICHARDSON_QUERIES:
        print(f"  Query: {query}")
        results = search_jina(query)
        for title, url in results:
            if url not in communities:
                communities[url] = (title, "Richardson")
        time.sleep(1.1)  # Rate limit: max 1 req/sec

    # Search Plano
    print("\nSearching Plano TX...")
    for query in PLANO_QUERIES:
        print(f"  Query: {query}")
        results = search_jina(query)
        for title, url in results:
            if url not in communities:
                communities[url] = (title, "Plano")
        time.sleep(1.1)

    # Deduplicate and limit to 50
    richardson = [(name, city, url) for url, (name, city) in communities.items() if city == "Richardson"]
    plano = [(name, city, url) for url, (name, city) in communities.items() if city == "Plano"]

    print(f"\n\nSummary: Found {len(richardson)} Richardson + {len(plano)} Plano")

    # Limit to 25 each, prioritize by position
    richardson = richardson[:25]
    plano = plano[:25]

    # Write CSV
    output_file = OUTPUT_DIR / "R2-communities.csv"
    with open(output_file, "w") as f:
        f.write("name,city,url\n")
        for name, city, url in richardson + plano:
            f.write(f'"{name}",{city},{url}\n')

    print(f"\nSaved to {output_file}")
    print(f"Total communities: {len(richardson) + len(plano)}")
    return richardson + plano

if __name__ == "__main__":
    main()
