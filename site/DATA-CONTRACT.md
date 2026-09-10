# PropertyStack site -- data contract

The site (`site/*.html`) is a static, no-build, no-framework front end. Every
page loads on plain `<script>` tags and reads a JSON file from `site/data/`.
**To update what the site shows, only the JSON files need to change --
never the HTML/CSS/JS**, as long as the shape below is kept.

This is deliberately the simplest possible stack (no npm, no bundler, no
React) so a future session can regenerate the JSON files without needing to
touch or understand the front-end code at all.

## site/data/properties.json (Master Table + Property Detail)
```
{
  "generatedFrom": "<path to source CSV, for provenance>",
  "stats": { "apartments": int, "totalUnits": int, "softwareIdentified": int,
             "softwareIdentifiedPct": float, "topSoftware": string|null },
  "funnel": { "inArea": int, "websiteFound": int|null, "checked": int,
              "identified": int, "unknown": int },
  "vendorColors": { "<VendorName>": "#hex", ... },
  "properties": [
    { "id": string (unique, used in property.html?id=...), "community": string,
      "city": string, "address": string, "units": int|null,
      "yearBuilt": int|null, "owner": string, "software": string|null,
      "proof": string|null (a URL) }
  ]
}
```
Regenerate with `python3 site/data/build_data.py` once
`raw/research-01/area-table-richardson-plano.csv` has more rows filled in
(the `software`/`proof` columns from `tooling/pms_detect.py`).

## site/data/software-share.json (Software Share page)
```
{
  "generatedFrom": string, "note": string,
  "share": [
    { "vendor": string, "color": "#hex", "properties": int, "units": int,
      "pctOfIdentifiedProperties": float }
  ]
}
```
Also produced by `build_data.py` from the same CSV. `changeSinceLastRun` per
vendor isn't tracked yet -- needs a second run's `share` array diffed
against a saved prior one.

## site/data/leads.json (Early Leads / home page) -- REAL, built from leads.csv
```
{
  "stats": { "leads": int, "newThisWeek": int (count of leads flagged isNew),
             "unitsInPlay": int, "openingNext12mo": int (units in leasing/
             under-construction upcoming projects) },
  "leads": [
    { "id": string (lN, N = leads.csv rank), "propertyId": string|null
      (apt_id, set only for "sold" leads that exist in master.csv -- used
      for the property.html?id= click-through; null for "upcoming" leads,
      which have no building yet), "score": int (0-100), "property": string,
      "city": string, "units": int|null, "signalType": "Upcoming"|"Sold",
      "signal": string (short phrase, e.g. "Permit issued" or "Sold Mar
      2026"), "software": string|null, "why": string (ONE short sentence,
      not a paragraph), "sources": [string, ...] (short tags, e.g. "permit",
      "website", "county record"),
      "contact": { "phone": string|null, "email": string|null } | null
      (from contacts.csv, sold leads only, null if nothing was scraped),
      "isNew": bool (sale_date/stage_date within 30 days of TODAY in
      build_data.py) }
  ]
}
```
Regenerate with `python3 site/data/build_data.py` any time `leads.csv`,
`leads-facts.jsonl`, or `contacts.csv` change.

## site/data/pipeline.json (Under the Hood page) -- real data, cost is PLACEHOLDER
```
{
  "steps": [ { "name": skill, "label": string, "count": int|null } ] (6 items, pipeline order),
  "runs": [ { "runId": string, "started": iso, "skill": string, "area": string,
              "status": string, "counts": string, "errors": int,
              "durationSec": float|null } ] (every propertystack/runs/*.json, newest first),
  "accuracy": { "reviewDoc": url, "spotcheckDoc": url },
  "costPerArea": { "note": string },   // PLACEHOLDER until runs log dollars
  "reviewQueue": { "byReason": { reason: int }, "rows": [ { "id", "community", "city",
                   "units", "reason", "website" } ] }  // master.csv rows with software unknown
}
```

## Design tokens
All colors/fonts/spacing live in `site/css/styles.css` as CSS custom
properties (`:root { --bg: ...; --accent: ...; }`). This is the approved
"techie/dev-tool" dark style (dark zinc background, thin 1px borders, no
shadows/gradients, one green accent), inspired by shadcn/ui's `dashboard-01`
block and Vercel's Geist design system. Change tokens there, not per-page.

## What's intentionally NOT built yet
- No routing/build step -- multi-page static HTML on purpose (brief says
  static site on Vercel, no backend, no login).
- No real "View As" color-swap logic beyond dimming rows matching the
  selected vendor (`site/js/app.js` `isDimmedRow`) -- extend there if the
  brief's fuller behavior (highlight the vendor's color site-wide) is needed.
- Export CSV button, search/filter inputs are visual only (no JS wired) --
  intentionally out of scope for the wireframe-to-scaffold step.
