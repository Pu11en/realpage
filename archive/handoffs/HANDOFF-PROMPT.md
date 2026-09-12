# Handoff prompt -- paste this to a session once the data side is done

Copy everything in the box below and paste it to any Claude Code session
working in the `realpage` repo, once the PMS-detection / leads / run-logging
skills have produced real output files.

---

```
The site/ folder in this repo is a finished static-HTML wireframe scaffold
for PropertyStack (5 pages: Early Leads, Master Table, Software Share,
Property Detail, Under the Hood). It's plain HTML/CSS/JS -- no build step,
no framework. It currently runs on real Master Table + Software Share data
(built from raw/research-01/area-table-richardson-plano.csv via
site/data/build_data.py) and placeholder data for Early Leads and Under the
Hood (clearly marked with a "status" field in each JSON file).

Read site/DATA-CONTRACT.md first -- it documents the exact JSON shape each
page expects from site/data/*.json.

Your job: wire in whatever real data now exists (leads/signals data,
run-history/cost logs, a refreshed PMS-detection CSV, etc) by either:
1. Extending site/data/build_data.py so it also emits leads.json and/or
   pipeline.json in the documented shape, reading from wherever that real
   data now lives, or
2. Writing the JSON files directly if a one-off script isn't worth it.

Rules:
- Do not edit the HTML/CSS/JS files unless the data now has a shape the
  current contract genuinely can't express -- if so, update
  DATA-CONTRACT.md in the same change so it stays the source of truth.
- Once a data file stops being a placeholder, remove its "status" key (the
  site shows a yellow banner whenever "status" is present).
- Verify by serving the folder locally (e.g. `python3 -m http.server` from
  inside site/) and opening each of the 5 pages in a browser -- don't just
  eyeball the JSON.
- Keep site/data/*.json as the only thing that changes for a routine data
  refresh; that's the whole point of this scaffold.
```

---

Everything above is self-contained -- the target session doesn't need this
conversation's history, just this repo.
