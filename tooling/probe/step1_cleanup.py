#!/usr/bin/env python3
"""
Clean up the communities list to get 50 legitimate apartment communities.
Remove aggregators, review sites, LinkedIn, Wikipedia, etc.
"""
import csv
from pathlib import Path
from urllib.parse import urlparse

csv_path = Path("/home/drewp/main-projects/realpage/raw/research-01/R2-communities.csv")

# Patterns that indicate NOT a primary community website
INVALID_PATTERNS = {
    "student.com",
    "har.com",
    "apartmentratings.com",
    "youtube.com",
    "linkedin.com",
    "wikipedia.org",
    "homes.com",
    "rentcafe.com",
    "renthop.com",
    "mapquest.com",
    "indeed.com",
    "planochamber.org",
    "planotexas.org",
    "simpsonpropertygroup.com",
    "multifamilybiz.com",
    "cor.net",
    "hh-cp.com",
    "international-capital.com",
    # Real estate developers, not community sites
    "triconhomes.com",
    "lennar.com",
    "jome.com",
}

# Read current communities
with open(csv_path) as f:
    reader = csv.DictReader(f)
    communities = list(reader)

print(f"Starting with {len(communities)} communities")

# Filter to valid ones
valid_communities = []
for row in communities:
    url = row["url"]
    parsed = urlparse(url)
    domain = parsed.netloc.lower().lstrip("www.")

    # Check if it matches invalid patterns
    if any(pattern in domain for pattern in INVALID_PATTERNS):
        continue

    # Skip URLs that look like they have broken HTML
    if "&nbsp;" in url or "..." in url:
        continue

    valid_communities.append(row)

print(f"After filtering: {len(valid_communities)} communities")

# Limit to 50: try to balance between Richardson and Plano/Mixed
richardson = [c for c in valid_communities if c["city"] == "Richardson"]
plano_mixed = [c for c in valid_communities if c["city"] in ("Plano", "Mixed")]

print(f"Richardson: {len(richardson)}, Plano/Mixed: {len(plano_mixed)}")

# Keep up to 25 of each, prefer Richardson then Plano then Mixed
richardson = richardson[:25]
plano_mixed = plano_mixed[:25]

final_communities = richardson + plano_mixed
print(f"Final selection: {len(final_communities)}")

# Write cleaned CSV
with open(csv_path, "w") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "city", "url"])
    writer.writeheader()
    for row in final_communities:
        writer.writerow(row)

print(f"Saved {len(final_communities)} communities to {csv_path}")
