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


def dot_grid(size, spacing=28, color=BLUE_LT, alpha=13):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    step = spacing * SS
    for y in range(0, size[1], step):
        for x in range(0, size[0], step):
            d.ellipse([x, y, x + 2 * SS, y + 2 * SS], fill=color + (alpha,))
    return layer


def radial_glow(size, cx, cy, rx, ry, color, core_alpha, blur=16):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    steps = 36
    for i in range(steps, 0, -1):
        t = i / steps
        a = int(core_alpha * (1 - t) ** 1.6)
        d.ellipse([cx - rx * t, cy - ry * t, cx + rx * t, cy + ry * t],
                  fill=color + (a,))
    return layer.filter(ImageFilter.GaussianBlur(radius=blur * SS))


def aurora_wave(size, baseline, amp, period, phase, stops, alpha):
    """One horizontal aurora ribbon: gradient fill below a sine crest."""
    W, H = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    step = 4 * SS
    for x in range(0, W + step, step):
        col = gradient(stops, x / W)
        y = baseline + amp * math.sin(2 * math.pi * (x + phase) / period)
        d.line([(x, y), (x, H)], fill=col + (alpha,), width=step)
    return layer


def v_gradient_rect(size, y0, top_color, bottom_color):
    """Vertical gradient rect from y0 to the bottom of the canvas."""
    W, H = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    span = max(1, H - y0)
    for y in range(y0, H):
        d.line([(0, y), (W, y)],
               fill=lerp(top_color, bottom_color, (y - y0) / span) + (255,))
    return layer


def gradient_bar(size, cx, cy, w, h):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, x1 = cx - w * SS / 2, cx + w * SS / 2
    for x in range(int(x0), int(x1)):
        d.line([(x, cy - h * SS / 2), (x, cy + h * SS / 2)],
               fill=gradient([(0, BLUE_LT), (1, VIOLET_LT)], (x - x0) / (x1 - x0)))
    return layer


# ----------------------------------------------------------------------------
# Motion element builders
# ----------------------------------------------------------------------------

def build_particles(n, W, H, rng):
    """Particles rising exactly k screen-heights per loop -> seamless."""
    parts = []
    palette = [BLUE_LT, VIOLET_LT, TITLE, BLUE_MID]
    for i in range(n):
        parts.append({
            "x0": rng.uniform(0, W),
            "y0": rng.uniform(0, H),
            "k": rng.choice((1, 1, 2)),
            "sway": rng.uniform(3, 8) * SS,
            "m_sway": rng.choice((1, 2)),
            "m_tw": rng.choice((1, 2, 3)),
            "ph": rng.uniform(0, 2 * math.pi),
            "r": rng.uniform(1.0, 2.4) * SS,
            "col": palette[i % len(palette)],
            "a": rng.uniform(26, 88),
        })
    return parts


def draw_particles(layer, parts, t, F, W, H):
    d = ImageDraw.Draw(layer)
    for p in parts:
        y = (p["y0"] - p["k"] * (t / F) * H) % H
        x = p["x0"] + p["sway"] * math.sin(2 * math.pi * p["m_sway"] * t / F + p["ph"])
        a = p["a"] * (0.72 + 0.28 * math.sin(2 * math.pi * p["m_tw"] * t / F + p["ph"]))
        d.ellipse([x - p["r"], y - p["r"], x + p["r"], y + p["r"]],
                  fill=p["col"] + (int(a),))


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
