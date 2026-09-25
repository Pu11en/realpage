#!/usr/bin/env python3
"""Render the CraneSignal mark to site/img/logo.png. Run by hand, not by the builders.

Why this exists: the Organization JSON-LD declared `logo` pointing at og-default.png, which
is the 1200x630 share card. schema.org `logo` means an actual logo -- Google uses it in
knowledge panels and search results -- so a wide marketing banner there is structured data
misdescribing its own image. Small, but the whole plan rests on the schema being literally
true, and this was the one place it was not.

The shape is the same mark the site already uses as its favicon, declared inline in the
landing page's `<link rel="icon">` as an SVG data URI. It is all rectangles, two lines and
one triangle on a 44x44 grid, so it is reproduced here exactly rather than approximated --
cairosvg would have been simpler but needs a native cairo DLL that is not on this machine.

    python3 tooling/seo/make_logo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover - only bites when someone regenerates the logo
    print("needs Pillow: python3 -m pip install pillow", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "site" / "img" / "logo.png"

SIZE = 512          # square, which is what a logo slot expects
GRID = 44.0         # the source SVG's viewBox
S = SIZE / GRID     # scale factor

BLUEPRINT = (26, 61, 143)
AMBER = (245, 183, 0)
WHITE = (255, 255, 255)


def px(*values: float) -> list[float]:
    return [v * S for v in values]


def main() -> int:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # rect width=44 height=44 rx=9 fill=#1a3d8f
    draw.rounded_rectangle(px(0, 0, 44, 44), radius=9 * S, fill=BLUEPRINT)

    # The jib cables: M13.5 3 5 10  and  M13.5 3 38 10, stroke-width 1.6
    width = max(1, round(1.6 * S))
    draw.line(px(13.5, 3, 5, 10), fill=WHITE, width=width)
    draw.line(px(13.5, 3, 38, 10), fill=WHITE, width=width)

    # The mast: M11 10h5v26h-5z
    draw.rectangle(px(11, 10, 16, 36), fill=WHITE)
    # Its cap: M11 10l2.5-7 2.5 7z
    draw.polygon([*px(11, 10), *px(13.5, 3), *px(16, 10)], fill=WHITE)
    # The base: M5 36h17v4H5z
    draw.rectangle(px(5, 36, 22, 40), fill=WHITE)
    # The jib: M4 10h36v4H4z
    draw.rectangle(px(4, 10, 40, 14), fill=AMBER)
    # Counterweight: M5 14h5v4H5z
    draw.rectangle(px(5, 14, 10, 18), fill=WHITE)
    # Hoist line: M31 14h1.6v8H31z
    draw.rectangle(px(31, 14, 32.6, 22), fill=WHITE)
    # The load: M27.8 22h8v7h-8z
    draw.rectangle(px(27.8, 22, 35.8, 29), fill=AMBER)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, optimize=True)
    print(f"wrote {OUT.relative_to(ROOT).as_posix()} ({OUT.stat().st_size:,} bytes, {SIZE}x{SIZE})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
