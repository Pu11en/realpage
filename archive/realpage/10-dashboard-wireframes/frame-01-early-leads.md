Status: GENERATED v1 (2026-09-10) — see images/frame-01-early-leads.jpg — 30 credits (Nano Banana 2, 16:9)

# Frame 1: Early Leads (home page)

Top bar: see `00-global-top-bar.md`.

What's on it, top to bottom:
1. Stat boxes (4): "Leads" · "New this week" · "Units in play" · "Opening in
   next 12 mo" — big bold number, small label under each.
2. Filter row: signal type (Upcoming / Recently sold) dropdown · city dropdown
   · stage dropdown · units range slider/inputs · current software dropdown ·
   a toggle switch "hide properties already on my software."
3. Ranked list below, one row per lead, columns left to right:
   Rank number · Score 0-100 (number + small horizontal bar) · Property/
   Project name · City · Units · Signal pill (e.g. "Upcoming · Permit
   issued" or "Sold · Mar 2026") · Current software pill (or "Not chosen
   yet" in gray) · Why line (one short sentence of body text with 2-3 tiny
   source chips after it, e.g. [county record] [permit] [website]) ·
   small "NEW" badge on some rows.

Placeholder sample rows (real data not ready yet):
- #1, Score 88, "Legacy North Tower — Phase II", Plano, 340 units,
  "Upcoming · Permit issued", "Not chosen yet",
  "New construction near Legacy West with no PMS signal yet — high-value target."
  [permit] [website], NEW badge
- #2, Score 74, "Cortland North Plano", Plano, 548 units, "Sold · Mar 2026",
  "RealPage", "Sold to a new owner three months ago; software not yet switched."
  [county record] [website]
- #3, Score 61, "Windsor Preston", Plano, 288 units, "Upcoming · Zoning filed",
  "Not chosen yet", "Early-stage zoning filing, long runway before a decision."
  [permit]

Row click → Property Detail (frame 4).

## Draft Blotato prompt (two-stage plan)

**Stage 1 — grayscale structure pass:**
> Monochrome UX wireframe of a web app dashboard screen, top navigation bar
> with a wordmark on the left and four tab labels centered and a dropdown
> plus a toggle switch on the right, below it a row of four stat cards with
> large numbers and small labels, below that a horizontal filter bar with
> four dropdowns and one toggle switch, below that a long ranked list table
> with seven columns including a small score bar per row and short pill
> shapes in two of the columns, hand-drawn wireframe sketch aesthetic, white
> background, no color, Balsamiq style, desktop web layout, wide aspect ratio.

**Stage 2 — styled pass (image-edit model, using stage 1 as input):**
> Apply a clean enterprise SaaS visual style to this dashboard wireframe:
> navy blue top bar and top-bar text, white page background, light gray
> stat cards with bold navy numbers, teal accent color for the active tab
> underline and the toggle switch, small colored status pills (signal pill
> and software pill) in muted pastel colors per vendor, thin score bars in
> teal, modern bold sans-serif for headers and stat numbers, lighter
> sans-serif for table rows and the "why" sentence text, small gray source
> chip tags, generous whitespace between rows, corporate and data-confident
> tone, high-fidelity UI mockup, not photorealistic, legible-looking (but
> not necessarily perfectly readable) text in every label.

## Model choice
- Stage 1: cheap model (Flux Schnell, 1 credit) — generate 2 for layout
  options, pick the best structure before spending on stage 2.
- Stage 2: edit-capable model (Nano Banana Edit or similar), applied once
  to the chosen stage-1 layout.
