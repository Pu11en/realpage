#!/usr/bin/env python3
import httpx
import json
from pathlib import Path

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

# Test a simple query
url = "https://s.jina.ai/"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "X-Respond-With": "no-content",
}

query = "apartments Richardson TX"
response = httpx.get(
    url,
    params={"q": query},
    headers=headers,
    timeout=30,
)

print(f"Status: {response.status_code}")
data = response.json()
print(f"Full response:\n{json.dumps(data, indent=2)[:1000]}")
