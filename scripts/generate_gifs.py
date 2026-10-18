#!/usr/bin/env python3
"""
Generate the live animated GIF assets used by the GitHub profile README.

The hero header and the footer banner are rendered as looping GIFs so they
can carry richer, layered motion (aurora ribbons, drifting particles,
twinkling stars, pulsing glow) than SMIL allows inside GitHub's sanitised
<img> pipeline. The text-critical animations (typing strip, developer
terminal, section divider) stay as vector SMIL SVGs — see
scripts/generate_assets.py — because crisp text needs vectors.

Design tokens
-------------
Kept in sync with scripts/generate_assets.py (documented in ASSETS.md):
- Backgrounds : deep midnight navy #0A0E1A
- Accents     : electric blue #1F6FEB / #58A6FF, restrained violet #8B5CF6 / #A371F7
- Text        : #F0F6FC (title), #A5B4D6 (subtitle), #6E7681 (faint)
- Typography  : DejaVu Sans Mono (rendered at 2x and downscaled for clean edges)

Every loop is mathematically seamless: wave phases advance by whole periods
per loop, particles travel whole screen-heights per loop, and glow/star
pulses run on integer sine cycles.

Usage
-----
    python3 scripts/generate_gifs.py        (requires Pillow)

Outputs are written to assets/ . Edit the constants below and re-run to
refresh the visuals.
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

# ----------------------------------------------------------------------------
# Design tokens (keep in sync with scripts/generate_assets.py)
# ----------------------------------------------------------------------------
BG_DEEP = (10, 14, 26)        # midnight navy   #0A0E1A
BLUE = (31, 111, 235)         # electric blue   #1F6FEB
BLUE_LT = (88, 166, 255)      # light blue      #58A6FF
BLUE_MID = (76, 111, 255)     # gradient mid    #4C6FFF
VIOLET = (139, 92, 246)       # violet          #8B5CF6
VIOLET_MID = (90, 124, 255)   # gradient mid    #5A7CFF
VIOLET_LT = (163, 113, 247)   # light violet    #A371F7
TITLE = (240, 246, 252)       # headline        #F0F6FC
SUBTITLE = (165, 180, 214)    # header subtitle #A5B4D6
FAINT = (110, 118, 129)       # faint text      #6E7681
GLOW_BODY = (16, 26, 51)      # footer body top #101A33

SS = 2                        # supersampling factor (render 2x, downscale 1x)
FRAMES = 48                   # frames per loop
FRAME_MS = 55                 # ~2.6s loop

SEED = 20261018

NAME = "ARPIT NAYAN"
TAGLINE = "AI Builder \u00b7 Aspiring Founder"
EYEBROW = "// building in public"
FOOTER_MAIN = "Learn. Build. Iterate."
FOOTER_SUB = "AI products \u00b7 healthcare technology \u00b7 software systems"


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------

def lerp(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def gradient(stops, t):
    """Sample a multi-stop colour gradient at t in [0, 1]."""
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if t <= p1:
            return lerp(c0, c1, (t - p0) / (p1 - p0))
    return stops[-1][1]


def scale_alpha(layer, k):
    """Return a copy of an RGBA layer with its alpha scaled by k."""
    alpha = layer.getchannel("A").point(lambda v: int(v * k))
    out = layer.copy()
    out.putalpha(alpha)
    return out


def font(size_px, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, int(size_px * SS))


def spaced_text(draw, cx, baseline_y, s, fnt, fill, spacing=0):
    """Draw letter-spaced text centered on cx with a baseline anchor."""
    widths = [draw.textlength(ch, font=fnt) for ch in s]
    total = sum(widths) + spacing * SS * (len(s) - 1)
    x = cx - total / 2
    for ch, w in zip(s, widths):
        draw.text((x, baseline_y), ch, font=fnt, fill=fill, anchor="ls")
        x += w + spacing * SS
    return total


def text_layer(size, cx, baseline_y, s, fnt, fill, spacing=0, glow=0):
    """Render text on a transparent layer, optionally with a blurred glow."""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    spaced_text(ImageDraw.Draw(layer), cx, baseline_y, s, fnt, fill, spacing)
    if not glow:
        return layer, None
    glow_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    spaced_text(ImageDraw.Draw(glow_layer), cx, baseline_y, s, fnt, fill, spacing)
    return layer, glow_layer.filter(ImageFilter.GaussianBlur(radius=glow))


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

FILES = {
}


def main():
    ASSETS.mkdir(exist_ok=True)
    for name, fn in FILES.items():
        out = fn()
        print(f"wrote  assets/{name:26} {out.stat().st_size:8d} bytes")


if __name__ == "__main__":
    main()
