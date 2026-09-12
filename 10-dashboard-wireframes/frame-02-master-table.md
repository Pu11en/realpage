Status: GENERATED v1 (2026-09-10) — see images/frame-02-master-table.jpg — 30 credits (Nano Banana 2, 16:9)

# Frame 2: Master Table (every apartment in the area)

Top bar: see `00-global-top-bar.md`.

What's on it, top to bottom:
1. Stat boxes (4): "Apartments" · "Total units" · "Software identified
   (% + count)" · "Top software."
2. Filter row: search box · city dropdown · software dropdown · year-built
   range · units range.
3. Table, columns: Community · City · Units · Year built · Owner ·
   Software (colored pill) · Proof (small link icon) · NEW badge (only on
   some rows).
4. Footer coverage funnel strip under the table: "In area 195 → Website
   found → Checked → Identified → Unknown" with a count under each step
   and small connecting arrows.
5. "Export CSV" button, top-right of the table area.

Real sample rows (from `raw/research-01/area-table-richardson-plano.csv`):
- Legends at Chase Oaks · Plano · 346 units · 1996 · Yardi
- Dorian · Plano · 398 units · 2007 · RealPage
- The Emory · Plano · 270 units · 2023 · Entrata
- Northside at Legacy I Apartments · Plano · 793 units · 2007 · (unknown, dash)
- Legacy Village Phase III · Plano · 720 units · 2005 · (unknown, dash)

Stat totals for the boxes: 195 apartments, 51,701 units, "26 identified
(13%)", top software "Yardi (14)".

Row click → Property Detail (frame 4).

## Draft Blotato prompt (two-stage plan)

**Stage 1 — grayscale structure pass:**
> Monochrome UX wireframe of a web app dashboard screen, top navigation bar
> with wordmark, four tabs, and right-side dropdown plus toggle, below it a
> row of four stat cards, below that a filter bar with a search box and
> four dropdowns, below that a wide data table with seven columns, small
> pill shapes in one column and a small icon in another, a horizontal
> funnel diagram strip below the table showing five steps connected by
> arrows with a number under each step, an export button in the top-right
> corner of the table area, hand-drawn wireframe sketch aesthetic, white
> background, no color, Balsamiq style, desktop web layout, wide aspect ratio.

**Stage 2 — styled pass (image-edit model, using stage 1 as input):**
> Apply a clean enterprise SaaS visual style to this dashboard wireframe:
> navy blue top bar, white background, light gray stat cards with bold
> navy numbers, teal accent for the active tab and the export button, small
> colored software pills per vendor (e.g. muted red for RealPage, muted
> blue for Yardi, muted green for Entrata, gray dash for unknown), a subtle
> gray funnel diagram with teal arrows and bold counts, modern bold
> sans-serif headers, lighter sans-serif table text, generous row spacing,
> corporate and data-confident tone, high-fidelity UI mockup, not
> photorealistic, legible-looking text in every label.

## Model choice
- Stage 1: cheap model (Flux Schnell, 1 credit) — generate 2 layout options.
- Stage 2: edit-capable model (Nano Banana Edit or similar) on the chosen one.
