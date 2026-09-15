#!/usr/bin/env python3
"""Street Talk build: raw collector files -> the saved tab data and the chat CSV.

Reads the newest `propertystack/data/street-talk/raw/<date>/<part>.json` for each part (so a failed
weekly run keeps last week's data), labels every post with plain word lists (no paid AI) and writes:
  site/data/street-talk.json                    -- what the Street Talk tab shows
  propertystack/data/street-talk/street_talk.csv -- what the chat loads
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "propertystack" / "data" / "street-talk" / "raw"
JSON_OUT = ROOT / "site" / "data" / "street-talk.json"
CSV_OUT = ROOT / "propertystack" / "data" / "street-talk" / "street_talk.csv"
PARTS = ["rivals", "buildings", "unhappy"]

_spec = importlib.util.spec_from_file_location("collect", pathlib.Path(__file__).resolve().parent / "collect.py")
collect = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(collect)
COMPANIES = list(collect.COMPANIES)

ANGRY_RE = re.compile(
    r"\b(hate[sd]?|awful|terrible|horrible|worst|nightmare|scam\w*|frustrat\w*|angry|annoy\w*|"
    r"ridiculous|useless|garbage|trash|sucks?|broken|buggy|glitch\w*|overcharg\w*|price[- ]?fixing|"
    r"collu\w*|lawsuits?|sued|su(e|ing)|antitrust|den(y|ied|ial)|evict\w*|problems?|issues?|"
    r"complain\w*|unfair|goug\w*|rip(-| )?off|disappoint\w*|leaving|switching away|"
    r"no response|never (answer|respond)\w*|can'?t (get|reach))\b", re.I)
HAPPY_RE = re.compile(
    r"\b(love[sd]?|great|excellent|amazing|awesome|recommend\w*|happy|easy|helpful|best|"
    r"smooth(ly)?|fantastic|perfect|pleased|satisfied|works well|good experience|beautiful|nice)\b", re.I)
CITY_RE = re.compile(
    r"\b(Dallas|Houston|Austin|San Antonio|Fort Worth|Plano|Richardson|Frisco|McKinney|Allen|Irving|"
    r"Arlington|Garland|Grapevine|Carrollton|Lewisville|Denton|Round Rock|Cedar Park|Pflugerville|"
    r"Georgetown|Sugar Land|Katy|The Woodlands|Pearland|El Paso|Lubbock|Corpus Christi|Waco|"
    r"College Station|Addison|Mesquite|Grand Prairie|Euless|Bedford|Keller|Southlake)\b", re.I)
SUB_CITY = {"dallas": "Dallas", "houston": "Houston", "austin": "Austin", "askaustin": "Austin",
            "sanantonio": "San Antonio", "fortworth": "Fort Worth", "plano": "Plano", "dfw": "Dallas"}
# Part 3: sounds like someone who runs rentals (a software buyer), not a renter.
MANAGER_RE = re.compile(
    r"\b(i manage|we manage|managing \d+|our (company|portfolio|properties|units|team|office|residents|"
    r"tenants|owners)|my (portfolio|properties|units|tenants|company)|property manager|pm company|"
    r"\d+ (doors|units)|as a landlord|i'?m a landlord|owner here|our pm software|we (use|switched|moved|"
    r"are switching|are moving|are migrating))\b", re.I)
RENTER_RE = re.compile(r"\b(i'?m renting|renting a room|my (landlord|apartment|lease)|as a (tenant|renter)|"
                       r"move in|moving in)\b", re.I)


def text_of(post: dict) -> str:
    return " ".join([post.get("title", ""), post.get("excerpt", "")] + list(post.get("comments", [])))


def sentiment(text: str) -> str:
    angry, happy = len(ANGRY_RE.findall(text)), len(HAPPY_RE.findall(text))
    if angry and happy:
        return "angry" if angry >= 2 * happy else "happy" if happy >= 2 * angry else "mixed"
    return "angry" if angry else "happy" if happy else "neutral"


def city_of(post: dict, text: str) -> str:
    if post.get("city"):
        return post["city"]
    found = CITY_RE.search(text)
    if found:
        return found.group(1).title()
    return SUB_CITY.get(post.get("subreddit", "").lower(), "")


def is_warm_lead(post: dict, text: str) -> bool:
    return bool(MANAGER_RE.search(text)) and not RENTER_RE.search(text)


def label(post: dict, part: str) -> dict:
    text = text_of(post)
    companies = [c for c in COMPANIES if c in set(post.get("companies", [])) | set(collect.companies_in(text))]
    quote = (post.get("excerpt") or "").strip() or post.get("title", "")
    return {
        "part": part,
        "url": post["url"],
        "source": post.get("source", "reddit"),
        "subreddit": post.get("subreddit", ""),
        "channel": post.get("channel", ""),
        "title": post.get("title", ""),
        "quote": quote,
        "comments": list(post.get("comments", []))[:2],
        "date": post.get("date", ""),
        "score": post.get("score", 0),
        "companies": companies,
        "sentiment": sentiment(text),
        "city": city_of(post, text),
        "buildingId": post.get("buildingId", ""),
        "building": post.get("building", ""),
        "warmLead": part == "unhappy" and is_warm_lead(post, text),
    }


def latest_raw(raw_dir: pathlib.Path, part: str) -> tuple[str, dict] | None:
    """Newest dated folder holding this part's file (an older one stays if a newer run failed)."""
    for day in sorted((p for p in raw_dir.iterdir() if p.is_dir()), reverse=True) if raw_dir.exists() else []:
        f = day / f"{part}.json"
        if f.exists():
            return day.name, json.loads(f.read_text())
    return None


def totals(posts: list[dict]) -> dict:
    out = {}
    for company in COMPANIES:
        mine = [p for p in posts if company in p["companies"]]
        n = len(mine)
        pct = lambda s: round(100 * sum(p["sentiment"] == s for p in mine) / n) if n else 0
        out[company] = {"posts": n, "angryPct": pct("angry"), "happyPct": pct("happy"),
                        "mixedPct": pct("mixed"), "neutralPct": pct("neutral")}
    return out


def build(raw_dir: pathlib.Path = RAW_DIR, today: str | None = None) -> dict:
    parts, dates, seen = {}, {}, set()
    for part in PARTS:
        found = latest_raw(raw_dir, part)
        rows = []
        if found:
            dates[part], raw = found
            for post in raw.get("posts", []):
                if not post.get("url") or not post.get("date") or post["url"] in seen:
                    continue
                seen.add(post["url"])
                row = label(post, part)
                if part != "buildings" and not row["companies"]:
                    continue
                rows.append(row)
        rows.sort(key=lambda r: r["date"], reverse=True)
        parts[part] = rows
    everything = [p for rows in parts.values() for p in rows]
    return {
        "updated": max(dates.values()) if dates else "",
        "builtAt": today or dt.date.today().isoformat(),
        "sourceDates": dates,
        "totals": totals(everything),
        "counts": {part: len(rows) for part, rows in parts.items()},
        "warmLeads": sum(p["warmLead"] for p in parts["unhappy"]),
        "parts": parts,
    }


CSV_FIELDS = ["part", "date", "source", "subreddit", "title", "quote", "url", "companies", "sentiment",
              "city", "building_id", "building", "warm_lead", "score"]


def write(data: dict, json_out: pathlib.Path = JSON_OUT, csv_out: pathlib.Path = CSV_OUT) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    with csv_out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        for rows in data["parts"].values():
            for p in rows:
                w.writerow({"part": p["part"], "date": p["date"], "source": p["source"],
                            "subreddit": p["subreddit"], "title": p["title"], "quote": p["quote"],
                            "url": p["url"], "companies": ";".join(p["companies"]), "sentiment": p["sentiment"],
                            "city": p["city"], "building_id": p["buildingId"], "building": p["building"],
                            "warm_lead": "yes" if p["warmLead"] else "", "score": p["score"]})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=pathlib.Path, default=RAW_DIR)
    args = ap.parse_args()
    data = build(args.raw)
    write(data)
    print(f"Street Talk built from {data['sourceDates']}: {data['counts']}, warm leads {data['warmLeads']}")
    for company, t in data["totals"].items():
        print(f"  {company}: {t['posts']} posts, {t['angryPct']}% angry, {t['happyPct']}% happy")


if __name__ == "__main__":
    main()
