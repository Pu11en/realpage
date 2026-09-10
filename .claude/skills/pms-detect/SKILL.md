---
name: pms-detect
description: Find out which property-management software (Yardi, RealPage, Entrata, AppFolio, ResMan, Yotta…) each apartment community in an area runs, using only its public website. Use when Drew asks to map an area/metro/city, run the PMS radar, detect software for a list of apartment sites, or repeat the Richardson/Plano probe somewhere else.
---

# PMS detect — the core process

This is the product: from the outside, with public websites only, label each
apartment community with the software it runs, and attach a link as proof.
Proven on Richardson/Plano TX, 2026-09-10: 34 of 41 valid sites identified
(83%). Details are in `raw/research-01/R2-probe-summary.md`.

## Why it works

Every community website has a "Resident Login" or "Pay Rent" link, and that
link lives on the software vendor's own domain. `securecafe.com` = Yardi,
`loftliving.com` / `activebuilding.com` = RealPage, `residentportal.com` =
Entrata. If the homepage doesn't show it, the link is one click deeper.

## Steps

1. **Get the community list** → a CSV with at least `name,city,url`, where
   `url` is the community's own site (or its page on the manager's site).
   - Cheapest route: paste the list-building prompt below into any
     web-browsing chatbot, or have a haiku subagent run it with Jina Search
     (`https://s.jina.ai/?q=...`).
   - **Clean it before running.** Drop listing sites (apartments.com, zillow,
     rent.com, apartmentlist…), Facebook pages, index pages ("all Dallas
     apartments"), contact/floorplan subpages, duplicates, and truncated URLs.
     Dirty rows were 9 of 50 in the first probe.
   - Save to `raw/<area-slug>/communities.csv`.
2. **Run the detector** (Jina key comes from gitignored `.env`; never print it):
   `python3 tooling/pms_detect.py raw/<area-slug>/communities.csv raw/<area-slug>/pms.csv`
   About 5 sites run in parallel; ~40 sites take a few minutes.
3. **Check the unknowns.** Open 2–3 of them. If you see a new vendor domain
   in their resident links, add it to `VENDORS` in `tooling/pms_detect.py`
   (with an example URL in the comment) and re-run.
4. **Spot-check the knowns:** open the `evidence` link for 5 random rows and
   confirm it's that community's portal.
5. **Operator fallback (optional, lower confidence):** for big landlords with
   in-house portals (UDR, Cortland…), see `raw/research-01/R2b-operator-pms.md`.
   Label those rows `operator-level`. Pricing-tool use (YieldStar in lawsuits)
   is **not** proof of which PMS they run.
6. **Report:** identified %, count per vendor, the unknowns and why. Write a
   short `raw/<area-slug>/summary.md` with the repo header block.

## Known limits

- The big REITs with their own branded portals (UDR, Cortland/Funnel) usually
  stay unknown from the website alone.
- `signal=asset` (vendor found only in an image or PDF host) is weaker than
  `portal` or `hop-portal`.
- Detection shows *today*. Dating switches needs Wayback snapshots (not built
  yet).

## List-building prompt (paste into a browsing chatbot; swap in the area)

```text
I need a complete list of apartment communities in <CITY, ST> (ZIPs <list>),
each with its own official website. Include every professionally managed
apartment community (~50+ units): market-rate, luxury, affordable, 55+.
Exclude single-family rentals, condos for sale, hotels, extended-stay,
assisted living. Give the community's own site, or its page on the management
company's site. Never listing sites (apartments.com, zillow, rent.com,
apartmentlist, trulia, redfin, realtor.com, hotpads, forrent, apartmentguide,
craigslist, yelp, facebook). One row per community, no duplicates, no index
or contact pages. Search Google Maps per ZIP, big managers' portfolio pages
(Greystar, Camden, UDR, Cortland, MAA, Bell, Lincoln, Knightvest, Kairoi,
Willow Bridge, CWS, Avenue5, Asset Living, RPM Living), city housing pages,
and the HUD LIHTC database.
Output CSV columns: name,address,city,zip,management_company,url,resident_portal_url,units
End with the count per city and any communities you couldn't find a site for.
```
