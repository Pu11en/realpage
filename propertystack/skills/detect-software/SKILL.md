---
name: detect-software
description: Skill 3 of PropertyStack. Detect the property-management software vendor for each community from its website (portal/asset links, one-hop follow). Use after find-website, before build-table.
---

# detect-software

**Reads:** `data/<area>/2-websites.csv`
**Writes:** `data/<area>/3-software.csv` (columns in `CONTRACTS.md`) + a run log in `runs/`

## Run
`python3 skills/detect-software/run.py --area plano-richardson`

## What it does
Ports the proven logic from `tooling/pms_detect.py`. For each community with a
`high`/`medium` confidence website (rows with `low`/`none` are never fetched):
1. Jina Reader fetches the homepage.
2. Look for known vendor hosts (RealPage, Yardi, Entrata, AppFolio, Buildium,
   ResMan, Yotta, MRI/RentManager) inside resident/login/pay/apply-type links
   → `signal=portal`.
3. If none, follow up to 3 resident/login/pay links one hop and re-check →
   `signal=hop-portal`.
4. If still none, fall back to a vendor host found anywhere on the homepage
   (e.g. an asset CDN) → `signal=asset`.
5. If still none, check known in-house portals as a last resort:
   `residents.udr.com` → `in-house:UDR`, `mycamden.com` → `in-house:Camden`.
6. If a `funnelleasing.com` login link is present but no vendor matched,
   record `unknown` with `unknown_reason=in-house-portal`.
7. Otherwise `unknown` with `unknown_reason=no-portal-link` (page fetched fine,
   nothing matched) or `error: <msg>` (fetch failed).
Runs 5 fetches in parallel (`--workers`, default 5).

## Check after running
- `software` and `unknown_reason` counts are printed and logged.
- Spot-check a few `portal`/`hop-portal` rows by opening `proof_url` — confirm
  it's actually this community's login/pay link, not a false-positive string
  match (e.g. "yardi" appearing in an unrelated analytics script URL).
- `asset`-signal rows are the weakest evidence (vendor host present but not in
  a portal-type link) — worth a second look before trusting them.

## Limits
- Vendor fingerprints are string/regex matches on URLs, not a certified list —
  new vendor domains or renamed products will show as `unknown`.
- In-house detection only covers UDR and Camden; other self-hosted portals
  fall through to `no-portal-link`.
- JS-heavy sites that Jina Reader can't render fully may hide the real portal
  link and undercount `portal`/`hop-portal` hits.
