# PropertyStack: map markers for researched states + "PropertyStack Agent" name

Written 2026-09-14 with Drew (answers: `/home/drewp/main-projects/handoffs/2026-09-14-map-dots-answers.md`,
look: `/home/drewp/main-projects/handoffs/2026-09-14-map-how-it-looks.md`). **Starts only when Drew says
"go work".** Localhost only, never push. Minimal styling (Drew does design himself). Area-agnostic: markers
come from whatever areas exist under `propertystack/data/`, never a hard-coded state list.

Run with: `Do the next unticked task in PLAN-map-markers.md, then tick it and stop.`
Check: `bash tooling/qa/check-panel.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765/map.html

## How to try it (30 seconds)
1. Map: states still shaded blue by RealPage clients; orange markers like "AZ · 94 leads" on states we researched; a legend explains both.
2. Click the Arizona marker: Early Leads opens straight on Arizona's table.
3. Open the chat: answers are labeled "PropertyStack Agent", never "hermes-agent".

## Tasks

- [ ] **M1 Marker data.** `site/data/build_data.py` also writes `site/data/map-markers.json`: one entry per
  state that has an area (state code from the area's leads; an area inside a state, like Plano-Richardson
  in Texas, rolls up to that state): state, label ("AZ · 94 leads"), lead count, top 3 cities, and the link
  to open (`index.html?area=<slug>` -- the statewide area if one exists, else the only area). Tests. Commit.
- [ ] **M2 Orange markers on the map.** `site/map.html`: keep the blue RealPage shading and its hover; add an
  orange marker at each state's center from `map-markers.json` with its label; hover shows lead count, top
  cities and "click to open the table"; one click goes to the link. Legend: blue shading = RealPage already
  has clients here; orange marker = our leads here. Works on phone size. Commit.
- [ ] **M3 Texas: link to Plano-Richardson.** When a state has more than one area (Texas: `tx` +
  Plano-Richardson), the state's table shows a small link at the top to the other area(s). Commit.
- [ ] **M4 "PropertyStack Agent" name.** The chat shows "PropertyStack Agent" instead of "hermes-agent":
  `chatbot/proxy.py` lists the model as id `propertystack-agent`, name "PropertyStack Agent" and maps it to
  the engine's real model name when forwarding; `DEFAULT_MODELS` in `chatbot/docker-compose.local.yml` (and
  any Railway/compose copy) uses the new id; `SOUL.md` says the assistant is the PropertyStack Agent. Rebuild
  with `bash tooling/dev.sh`; run `tooling/qa/check-answers.sh`; confirm no user-visible "Hermes". Commit.
  Recap in plain words for Drew what changed.
