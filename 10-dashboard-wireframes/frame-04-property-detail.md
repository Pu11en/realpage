Status: GENERATED v1 (2026-09-10) — see images/frame-04-property-detail.jpg — 30 credits (Nano Banana 2, 16:9)

# Frame 4: Property Detail (reached by clicking any row)

Top bar: see `00-global-top-bar.md`.

What's on it, top to bottom:
1. Header block: property name, address, city, units, year built, owner
   name — as a title plus a small line of meta text under it.
2. Three cards in a row (or stacked, whichever reads cleaner at desktop
   width — let the model choose, we'll pick the better layout):
   - **Software card:** vendor pill, proof link, "checked <date>" line,
     confidence badge (High/Med/Low).
   - **Signals card:** for a sold property — sale date, new owner, previous
     owner listed as small label/value pairs; for an upcoming building — a
     small horizontal stage timeline (Zoning filed → Approved → Permit →
     Construction → Leasing) with dates under each stage.
   - **Lead score card:** the score number, a small breakdown (size ·
     freshness · stage · current software each as a mini bar), then the
     full "why" paragraph below.
3. Sources list: a simple bullet list of every link the data came from.
4. Bottom row: website link button, small static map pin/thumbnail.

Real sample property to use: **Dorian**, Plano, 398 units, built 2007,
software RealPage. Use this as the header/software-card example; use the
placeholder lead/signal example from frame-01 ("Cortland North Plano," sold
Mar 2026) for the Signals + Lead score cards since real lead data isn't
ready yet.

## Draft Blotato prompt (two-stage plan)

**Stage 1 — grayscale structure pass:**
> Monochrome UX wireframe of a web app detail page, top navigation bar with
> wordmark, four tabs, and right-side dropdown plus toggle, below it a
> header block with a large title and a line of smaller meta text, below
> that three rectangular cards side by side — one card containing a pill
> shape and small text lines, one card containing a small horizontal
> timeline with dots and labels, one card containing a large number, a set
> of small bars, and a paragraph of body text, below the three cards a
> simple bulleted list, and at the bottom a button and a small square map
> placeholder, hand-drawn wireframe sketch aesthetic, white background, no
> color, Balsamiq style, desktop web layout, wide aspect ratio.

**Stage 2 — styled pass (image-edit model, using stage 1 as input):**
> Apply a clean enterprise SaaS visual style to this dashboard wireframe:
> navy blue top bar, white background, light gray card backgrounds for the
> three cards, a teal timeline with filled and unfilled dots showing
> progress, a bold navy score number with small teal breakdown bars, a
> muted red "RealPage" software pill, a confidence badge in green for
> "High," modern bold sans-serif for the property title and card headers,
> lighter sans-serif for body text and the why-paragraph, a simple gray
> map placeholder with a small teal pin icon, corporate and data-confident
> tone, high-fidelity UI mockup, not photorealistic.

## Model choice
- Stage 1: cheap model (Flux Schnell, 1 credit) — generate 2 layout options
  (side-by-side cards vs. stacked cards) and pick the clearer one.
- Stage 2: edit-capable model (Nano Banana Edit or similar) on the chosen one.
