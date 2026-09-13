#!/usr/bin/env python3
"""Map dots = apartment buildings we have PROVEN run RealPage (no offices, no press mentions).

Reads every propertystack/data/<area>/master.csv, keeps software == RealPage rows that have a
proof_url, places each at its street address with the free US Census batch geocoder (cached in
propertystack/data/raw/geocode-cache.json), and rewrites site/data/reach.json as:
  building dots  {kind:"building", name, city, state, lat, lon, units, area, links:[proof]}
  + any existing {kind:"scout"} markers (kept as they are).
Usage: python3 tooling/reach/build_buildings.py
"""
import csv, io, json, pathlib, urllib.request, uuid

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "propertystack" / "data"
REACH = ROOT / "site" / "data" / "reach.json"
CACHE = DATA / "raw" / "geocode-cache.json"
GEOCODER = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"


def realpage_buildings():
    for master in sorted(DATA.glob("*/master.csv")):
        for r in csv.DictReader(open(master, newline="")):
            if r.get("software") == "RealPage" and r.get("proof_url"):
                yield master.parent.name, r


def geocode(rows):
    """rows: {key: "street, city, state zip"} -> {key: (lat, lon)} via one Census batch call."""
    buf = io.StringIO()
    w = csv.writer(buf)
    for key, (street, city, state, zip_) in rows.items():
        w.writerow([key, street, city, state, zip_])
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"benchmark\"\r\n\r\nPublic_AR_Current\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"addressFile\"; filename=\"a.csv\"\r\n"
            f"Content-Type: text/csv\r\n\r\n{buf.getvalue()}\r\n--{boundary}--\r\n").encode()
    req = urllib.request.Request(GEOCODER, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    out = {}
    with urllib.request.urlopen(req, timeout=120) as resp:
        for line in csv.reader(io.StringIO(resp.read().decode())):
            if len(line) >= 6 and line[2] == "Match" and line[5]:
                lon, lat = map(float, line[5].split(","))
                out[line[0]] = (lat, lon)
    return out


def main():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    found = list(realpage_buildings())
    todo = {}
    for area, r in found:
        key = f"{area}:{r['apt_id']}"
        if key not in cache:
            todo[key] = (r["address"], r["city"], "TX" if r.get("county") in ("Collin", "Dallas") else "", r.get("zip", ""))
    if todo:
        cache.update({k: list(v) for k, v in geocode(todo).items()})
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache, indent=1))

    dots, missing = [], []
    for area, r in found:
        key = f"{area}:{r['apt_id']}"
        lat, lon = cache.get(key, (None, None))  # not geocoded: still listed, just no own spot
        if lat is None:
            missing.append(r["name"])
        dots.append({"kind": "building", "name": r["name"], "city": r["city"], "state": "TX",
                     "lat": lat, "lon": lon, "units": int(r["units"] or 0), "area": area,
                     "address": r["address"],
                     "links": [{"title": "Proof it runs RealPage", "url": r["proof_url"]}]})
    old = json.loads(REACH.read_text()) if REACH.exists() else []
    scouts = [d for d in old if d.get("kind") == "scout"]
    REACH.write_text(json.dumps(dots + scouts, indent=1))
    print(f"{len(dots)} RealPage buildings placed, {len(missing)} not geocoded {missing[:5]}, {len(scouts)} scout markers kept")


if __name__ == "__main__":
    main()
