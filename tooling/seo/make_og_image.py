#!/usr/bin/env python3
"""Make the share card at site/img/og-default.png. Run by hand, not by the builders.

Every page points `og:image` at this one file. Per-page cards would be better -- the
checklist in .claude/skills/fire-your-seo-agency/references/en/seo.md calls dynamic
generation ideal -- but the only fonts in the repo are woff2, which Pillow cannot read, so
the card has to fall back to whatever system font exists. That makes the bytes differ
between this Windows machine and Drew's Linux box, which would fight the page builder's
--check mode on every run. One committed image avoids that; per-page cards can come back
when a TTF is vendored.

    python3 tooling/seo/make_og_image.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - only bites when someone regenerates the card
    print("needs Pillow: python3 -m pip install pillow", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
OUT = SITE / "img" / "og-default.png"

# From the site's own logo SVG in index.html.
BLUEPRINT = (26, 61, 143)
AMBER = (245, 183, 0)
WHITE = (255, 255, 255)
FAINT = (255, 255, 255, 38)

SIZE = (1200, 630)  # what every social and search preview expects

FONT_CANDIDATES = {
    "bold": [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ],
    "regular": [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ],
}


def font(kind: str, size: int):
    for path in FONT_CANDIDATES[kind]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    print(f"no {kind} system font found; falling back to Pillow's bitmap font",
          file=sys.stderr)
    return ImageFont.load_default()


def totals() -> tuple[int, int, int, str]:
    index = json.loads((SITE / "data" / "areas" / "index.json").read_text(encoding="utf-8"))
    buildings = units = 0
    states = 0
    for area in index["areas"]:
        if area.get("hidden"):
            continue
        states += 1
        buildings += int(area.get("leads") or 0)
        payload = json.loads(
            (SITE / "data" / "areas" / f"{area['slug']}.json").read_text(encoding="utf-8")
        )
        units += int(payload.get("stats", {}).get("unitsInPlay") or 0)
    return buildings, units, states, index.get("updated", "")


def main() -> int:
    buildings, units, states, updated = totals()

    card = Image.new("RGB", SIZE, BLUEPRINT)
    draw = ImageDraw.Draw(card, "RGBA")

    # A faint drafting grid, the same idea as the site's own background.
    for x in range(0, SIZE[0], 48):
        draw.line([(x, 0), (x, SIZE[1])], fill=FAINT, width=1)
    for y in range(0, SIZE[1], 48):
        draw.line([(0, y), (SIZE[0], y)], fill=FAINT, width=1)

    draw.rectangle([0, 0, SIZE[0], 10], fill=AMBER)

    draw.text((72, 74), "CraneSignal", font=font("bold", 40), fill=WHITE)

    headline = font("bold", 66)
    draw.text((72, 168), "Apartment buildings", font=headline, fill=WHITE)
    draw.text((72, 244), "about to need something", font=headline, fill=AMBER)

    body = font("regular", 30)
    draw.text(
        (72, 346),
        f"Newly permitted, under construction, or just sold.\n"
        f"Every building links its public record.",
        font=body,
        fill=WHITE,
        spacing=12,
    )

    # The numbers, which are the actual reason to click.
    num = font("bold", 52)
    label = font("regular", 24)
    for i, (value, text) in enumerate(
        [(f"{buildings:,}", "buildings"), (f"{units:,}", "units"), (f"{states}", "states")]
    ):
        x = 72 + i * 300
        draw.text((x, 470), value, font=num, fill=WHITE)
        draw.text((x, 534), text, font=label, fill=AMBER)

    draw.text((72, 578), f"app.cranesignal.com · updated {updated}", font=label, fill=WHITE)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    card.save(OUT, optimize=True)
    print(f"wrote {OUT.relative_to(ROOT).as_posix()} ({OUT.stat().st_size:,} bytes, {SIZE[0]}x{SIZE[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
