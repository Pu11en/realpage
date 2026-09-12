Status: GENERATED v1 (2026-09-10) — see images/frame-05-under-the-hood.jpg — 30 credits (Nano Banana 2, 16:9)

# Frame 5: Under the Hood (shows how the agent works)

Top bar: see `00-global-top-bar.md`.

What's on it, top to bottom:
1. Pipeline diagram: 5 boxes in a horizontal flow connected by arrows —
   find-apartments (195) → find-website → detect-software (34 identified)
   → build-table → leads, each box showing its step name and a live count
   underneath.
2. Run history table below: columns date · area · skills run · properties
   processed · % identified · cost ($) · duration · models used (cheap vs.
   expensive) — a small handful of rows.
3. Two cards side by side under the table:
   - **Accuracy card:** latest hand-check result (e.g. "27/30 correct")
     plus a small trend line/sparkline over past runs.
   - **Cost card:** cost per area, split by model, shown as a small
     stacked bar or a couple of line items.
4. Review queue below the two cards: a read-only table of unknown/
   low-confidence rows, columns property · reason · suggested answer, with
   a small note "fixed in a local session, not on the site."

Sample numbers to use (real, from the brief): pipeline counts 195 → (blank/
in-progress) → 34 identified → (blank) → (blank); accuracy "27/30 correct."
Cost and run-history rows can be placeholder since no real run log exists yet.

## Draft Blotato prompt (two-stage plan)

**Stage 1 — grayscale structure pass:**
> Monochrome UX wireframe of a web app dashboard screen, top navigation bar
> with wordmark, four tabs, and right-side dropdown plus toggle, below it a
> horizontal pipeline diagram of five connected boxes with arrows between
> them and a small number under each box, below that a table with eight
> columns and four rows, below that two rectangular cards side by side —
> one with a small trend line and a large fraction number, one with a
> small stacked bar chart — and at the bottom a simple table with three
> columns, hand-drawn wireframe sketch aesthetic, white background, no
> color, Balsamiq style, desktop web layout, wide aspect ratio.

**Stage 2 — styled pass (image-edit model, using stage 1 as input):**
> Apply a clean enterprise SaaS visual style to this dashboard wireframe:
> navy blue top bar, white background, the pipeline boxes as light gray
> rounded rectangles connected by teal arrows with bold navy counts, the
> run history table with clean alternating row shading, the accuracy card
> showing a bold navy fraction and a small teal sparkline trending upward,
> the cost card as a small teal-and-gray stacked bar with a dollar value
> label, the review queue table below in a slightly muted gray tone to
> read as "reference only," modern bold sans-serif headers, lighter
> sans-serif table and card text, corporate and data-confident tone,
> high-fidelity UI mockup, not photorealistic.

## Model choice
- Stage 1: cheap model (Flux Schnell, 1 credit) — generate 2 layout options.
- Stage 2: edit-capable model (Nano Banana Edit or similar) on the chosen one.
