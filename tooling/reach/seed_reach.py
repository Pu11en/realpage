"""Seed site/data/reach.json with the RealPage buildings we proved in Plano/Richardson.

Reads site/data/properties.json (software == "RealPage", proof URL present) and
writes one "reach" dot per city. Other dots (build_reach.py, scout) are kept.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CITY_LATLON = {("Plano", "TX"): (33.0198, -96.6989), ("Richardson", "TX"): (32.9483, -96.7299)}

props = json.loads((ROOT / "site/data/properties.json").read_text())["properties"]
out_path = ROOT / "site/data/reach.json"
existing = json.loads(out_path.read_text()) if out_path.exists() else []
ours = {(c, s) for c, s in CITY_LATLON}
dots = [d for d in existing if not (d.get("kind") == "reach" and (d["city"], d["state"]) in ours
                                    and d.get("source") == "our-data")]
for (city, state), (lat, lon) in CITY_LATLON.items():
    rp = [p for p in props if p["software"] == "RealPage" and p["city"] == city and p.get("proof")]
    if not rp:
        continue
    dots.append({
        "city": city, "state": state, "lat": lat, "lon": lon, "signs": len(rp),
        "kind": "reach", "source": "our-data",
        "note": f"{len(rp)} apartment buildings we proved run RealPage",
        "links": [{"title": p["community"], "url": p["proof"]}
                  for p in sorted(rp, key=lambda p: p["community"])],
    })
out_path.write_text(json.dumps(dots, indent=1) + "\n")
print(f"reach.json: {len(dots)} dots")
