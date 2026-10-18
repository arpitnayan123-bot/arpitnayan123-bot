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
- Backgrounds : deep aubergine-charcoal #110D1A
- Accents     : signature gold #FFC93C / #FFE29A, amber #FFB454, warm orange #FF8C42
- Text        : #F5EDDC (title band), #E8DCC4 (subtitle), #9A8C74 (faint)
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
BG_DEEP = (17, 13, 26)        # deep aubergine-charcoal #110D1A
GOLD = (255, 201, 60)         # signature gold  #FFC93C
GOLD_LT = (255, 226, 154)     # light gold      #FFE29A
GOLD_DEEP = (232, 160, 32)    # deep gold       #E8A020
AMBER = (255, 180, 84)        # amber           #FFB454
ORANGE = (255, 140, 66)       # warm orange     #FF8C42
CREAM = (245, 237, 220)       # warm white      #F5EDDC
WARM_SOFT = (232, 220, 196)   # warm cream      #E8DCC4
WARM_FAINT = (154, 140, 116)  # warm gray       #9A8C74
GLOW_BODY = (32, 23, 46)      # footer body top #20172E
BLUE = (31, 111, 235)         # (legacy) electric blue   #1F6FEB
BLUE_LT = (88, 166, 255)      # (legacy) light blue      #58A6FF
BLUE_MID = (76, 111, 255)     # (legacy) gradient mid    #4C6FFF
VIOLET = (139, 92, 246)       # (legacy) violet          #8B5CF6
VIOLET_MID = (90, 124, 255)   # (legacy) gradient mid    #5A7CFF
VIOLET_LT = (163, 113, 247)   # (legacy) light violet    #A371F7
TITLE = (240, 246, 252)       # (legacy) headline        #F0F6FC
SUBTITLE = (165, 180, 214)    # (legacy) subtitle        #A5B4D6
FAINT = (110, 118, 129)       # (legacy) faint text      #6E7681

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


def build_stars(n, W, y_max, rng):
    stars = []
    for _ in range(n):
        stars.append({
            "x": rng.uniform(10, W - 10),
            "y": rng.uniform(6, y_max),
            "r": rng.uniform(0.8, 1.9) * SS,
            "m": rng.choice((1, 2, 3)),
            "ph": rng.uniform(0, 2 * math.pi),
            "a": rng.uniform(36, 110),
            "col": rng.choice((TITLE, BLUE_LT, VIOLET_LT)),
        })
    return stars


def draw_stars(layer, stars, t, F):
    d = ImageDraw.Draw(layer)
    for s in stars:
        a = s["a"] * (0.35 + 0.65 * (0.5 + 0.5 * math.sin(2 * math.pi * s["m"] * t / F + s["ph"])))
        d.ellipse([s["x"] - s["r"], s["y"] - s["r"], s["x"] + s["r"], s["y"] + s["r"]],
                  fill=s["col"] + (int(a),))


def finalize(frames, out_path, duration=FRAME_MS):
    """Downscale, quantize to one shared palette, save as looping GIF."""
    W, H = frames[0].size
    picks = [frames[i] for i in (0, FRAMES // 4, FRAMES // 2, 3 * FRAMES // 4)]
    sheet = Image.new("RGB", (W, H * len(picks)))
    for i, fr in enumerate(picks):
        sheet.paste(fr.convert("RGB"), (0, i * H))
    palette = sheet.quantize(colors=256, method=Image.MEDIANCUT)
    q = [fr.convert("RGB").quantize(palette=palette, dither=Image.NONE)
         for fr in frames]
    small = [f.resize((W // SS, H // SS), Image.LANCZOS) for f in q]
    small[0].save(out_path, save_all=True, append_images=small[1:],
                  duration=duration, loop=0, optimize=True)


# ----------------------------------------------------------------------------
# 1. Aurora hero
# ----------------------------------------------------------------------------

def compose_hero(width=896, height=260, name_fs=46, tag_fs=15, eye_fs=11.5):
    rng = random.Random(SEED)
    W, H = width * SS, height * SS
    cx = W / 2
    name_y = int(H * 0.485)
    bar_y = name_y + 14 * SS
    tag_y = bar_y + 28 * SS
    eye_y = name_y - 50 * SS

    base = Image.new("RGBA", (W, H), BG_DEEP + (255,))
    base.alpha_composite(dot_grid((W, H)))
    glow = radial_glow((W, H), cx, int(H * 0.42), int(W * 0.42), int(H * 0.46),
                       VIOLET, 58, blur=18)

    title_l, title_glow = text_layer((W, H), cx, name_y, NAME,
                                     font(name_fs), TITLE, spacing=6, glow=11)
    eye_l, _ = text_layer((W, H), cx, eye_y, EYEBROW,
                          font(eye_fs, bold=False), FAINT, spacing=2.5)
    tag_l, _ = text_layer((W, H), cx, tag_y, TAGLINE,
                          font(tag_fs, bold=False), SUBTITLE, spacing=2)
    bar = gradient_bar((W, H), cx, bar_y, 120, 2.6)

    parts = build_particles(max(10, width // 56), W, H, rng)

    frames = []
    for f in range(FRAMES):
        fr = base.copy()
        fr.alpha_composite(scale_alpha(glow, 0.86 + 0.14 * math.sin(2 * math.pi * f / FRAMES)))
        fr.alpha_composite(aurora_wave((W, H), H - 78 * SS, 12 * SS, W, 1.0 * W * f / FRAMES,
                                       [(0, BLUE), (1, VIOLET)], 40))
        fr.alpha_composite(aurora_wave((W, H), H - 64 * SS, 20 * SS, W // 2, 2.0 * (W // 2) * f / FRAMES,
                                       [(0, BLUE), (0.5, BLUE_MID), (1, VIOLET)], 84))
        fr.alpha_composite(aurora_wave((W, H), H - 46 * SS, 16 * SS, W // 4, 4.0 * (W // 4) * f / FRAMES,
                                       [(0, VIOLET), (0.55, VIOLET_MID), (1, BLUE)], 140))
        fr.alpha_composite(scale_alpha(title_glow, 0.8 + 0.2 * math.sin(2 * math.pi * f / FRAMES + 1.2)))
        fr.alpha_composite(title_l)
        fr.alpha_composite(eye_l)
        fr.alpha_composite(bar)
        fr.alpha_composite(tag_l)
        draw_particles(fr, parts, f, FRAMES, W, H)
        frames.append(fr)

    out = ASSETS / ("hero-aurora.gif" if width >= 800 else "hero-aurora-mobile.gif")
    finalize(frames, out)
    return out


# ----------------------------------------------------------------------------
# 2. Nebula footer
# ----------------------------------------------------------------------------

def compose_footer(width=896, height=150, main_fs=25, sub_fs=11.5):
    rng = random.Random(SEED + 7)
    W, H = width * SS, height * SS
    cx = W / 2
    body_y = int(H * 0.40)
    main_y = int(H * 0.68)
    sub_y = int(H * 0.85)

    base = Image.new("RGBA", (W, H), BG_DEEP + (255,))
    base.alpha_composite(v_gradient_rect((W, H), body_y, GLOW_BODY, BG_DEEP))

    main_l, main_glow = text_layer((W, H), cx, main_y, FOOTER_MAIN,
                                   font(main_fs), TITLE, spacing=3.5, glow=9)
    sub_l, _ = text_layer((W, H), cx, sub_y, FOOTER_SUB,
                          font(sub_fs, bold=False), SUBTITLE, spacing=1.5)

    stars = build_stars(max(12, width // 46), W, int(H * 0.42), rng)

    frames = []
    for f in range(FRAMES):
        fr = base.copy()
        fr.alpha_composite(aurora_wave((W, H), int(H * 0.29), 10 * SS, W // 4, 4.0 * (W // 4) * f / FRAMES,
                                       [(0, VIOLET), (1, BLUE)], 92))
        fr.alpha_composite(aurora_wave((W, H), int(H * 0.35), 14 * SS, W // 2, 2.0 * (W // 2) * f / FRAMES,
                                       [(0, BLUE), (1, VIOLET)], 150))
        draw_stars(fr, stars, f, FRAMES)
        fr.alpha_composite(scale_alpha(main_glow, 0.82 + 0.18 * math.sin(2 * math.pi * f / FRAMES)))
        fr.alpha_composite(main_l)
        fr.alpha_composite(sub_l)
        frames.append(fr)

    out = ASSETS / ("footer-nebula.gif" if width >= 800 else "footer-nebula-mobile.gif")
    finalize(frames, out)
    return out


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

FILES = {
    "hero-aurora.gif": lambda: compose_hero(),
    "hero-aurora-mobile.gif": lambda: compose_hero(width=620, height=216, name_fs=31, tag_fs=13, eye_fs=10.5),
    "footer-nebula.gif": lambda: compose_footer(),
    "footer-nebula-mobile.gif": lambda: compose_footer(width=620, height=124, main_fs=20, sub_fs=10),
}


def main():
    ASSETS.mkdir(exist_ok=True)
    for name, fn in FILES.items():
        out = fn()
        print(f"wrote  assets/{name:26} {out.stat().st_size:8d} bytes")


if __name__ == "__main__":
    main()
