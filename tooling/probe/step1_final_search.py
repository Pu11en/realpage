#!/usr/bin/env python3
"""
Final targeted searches for communities to reach 50 target
"""
import httpx
import csv
import time
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

# Load existing
existing_urls = set()
csv_path = OUTPUT_DIR / "R2-communities.csv"
with open(csv_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        existing_urls.add(row["url"])

print(f"Existing: {len(existing_urls)}")

SKIP_PATTERNS = {
    "student.com", "har.com", "apartmentratings.com", "youtube.com",
    "linkedin.com", "wikipedia.org", "homes.com", "rentcafe.com",
    "renthop.com", "mapquest.com", "indeed.com", "planochamber.org",
    "planotexas.org", "simpsonpropertygroup.com", "multifamilybiz.com",
    "cor.net", "hh-cp.com", "international-capital.com",
    "triconhomes.com", "lennar.com", "jome.com",
    "apartments.com", "zillow.com", "rent.com", "apartmentlist.com",
    "trulia.com", "redfin.com", "realtor.com", "yelp.com",
}

def is_valid(url):
    if url in existing_urls:
        return False
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if any(p in domain for p in SKIP_PATTERNS):
        return False
    if "&nbsp;" in url or "..." in url:
        return False
    return True

def search_jina(query):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
        "X-Respond-With": "no-content",
    }
    try:
        response = httpx.get(
            "https://s.jina.ai/",
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
                url = result.get("url", "")
                if is_valid(url):
                    results.append((result.get("title", ""), url))
        return results
    except:
        return []

# Try specific community names and locations
QUERIES = [
    "apartments downtown Richardson TX",
    "apartments downtown Plano TX",
    "Cortland apartments Plano",
    "UDR apartments Plano Richardson",
    "AvalonBay apartments Plano",
    "Camden apartments Plano Richardson",
    "Bluerock apartments Dallas Plano",
    "Avanath apartments Dallas",
    "Highpoint apartments Richardson Plano",
    "Palladium apartments Dallas",
    "Ramco apartments Dallas area",
    "AIMCO apartments Plano Richardson",
]

new = {}
for query in QUERIES:
    print(f"Query: {query}")
    results = search_jina(query)
    for title, url in results:
        if url not in existing_urls and url not in new:
            new[url] = (title, "Found")
            print(f"  {title[:40]}")
    time.sleep(1.1)

print(f"\nNew: {len(new)}")

# Append if we found any
if new:
    with open(csv_path, "a") as f:
        for url, (name, _) in new.items():
            f.write(f'"{name}","New",{url}\n')

# Count final
with open(csv_path) as f:
    count = sum(1 for _ in f) - 1
print(f"Total now: {count}")
