#!/usr/bin/env python3
"""
Final cleanup: select 50 unique, valid apartment communities
"""
import csv
from pathlib import Path
from urllib.parse import urlparse

csv_path = Path("/home/drewp/main-projects/realpage/raw/research-01/R2-communities.csv")

# Read all
with open(csv_path) as f:
    reader = csv.DictReader(f)
    communities = list(reader)

print(f"Total communities before cleanup: {len(communities)}")

# Patterns that indicate NOT a primary community website
INVALID = {
    "student.com", "har.com", "apartmentratings.com", "youtube.com",
    "linkedin.com", "wikipedia.org", "homes.com", "rentcafe.com",
    "renthop.com", "mapquest.com", "indeed.com", "planochamber.org",
    "planotexas.org", "simpsonpropertygroup.com", "multifamilybiz.com",
    "cor.net", "hh-cp.com", "international-capital.com",
    "triconhomes.com", "lennar.com", "jome.com",
    "apartments.com", "zillow.com", "rent.com", "apartmentlist.com",
    "trulia.com", "redfin.com", "realtor.com", "yelp.com",
}

# Filter and deduplicate
seen_urls = set()
valid = []

for row in communities:
    url = row["url"]

    # Skip if already seen
    if url in seen_urls:
        continue
    seen_urls.add(url)

    # Skip if invalid
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if any(p in domain for p in INVALID):
        continue

    # Skip if malformed
    if "&nbsp;" in url or "..." in url or not url.startswith("http"):
        continue

    valid.append(row)

print(f"Valid communities: {len(valid)}")

# Limit to 50
valid = valid[:50]
print(f"Final selection: {len(valid)}")

# Write final CSV
with open(csv_path, "w") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "city", "url"])
    writer.writeheader()
    for row in valid:
        writer.writerow(row)

print("Done")
