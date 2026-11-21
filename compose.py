#!/usr/bin/env python3
"""SALMIRA v3 — painterly salt-flat mirror town poster.

Fresh code, written in this session. Renders 1024x1024 at 2x supersample:
numpy gradients, blurred glow layers, layered grain, brush dabs,
wave-distorted mirror reflection, detailed town and robed travellers.
Deterministic (fixed seeds). Run: python3 compose.py -> entry.png
"""
import math
import random

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

random.seed(20261121)
rng = np.random.default_rng(20261121)

SS = 2  # supersample factor
W = H = 1024
SW, SH = W * SS, H * SS
M = 16  # cream margin, unit px
HY = 545  # horizon y, unit px
SUN = (560, 458)  # sun centre, unit px (open sky, clear of rooftops)

NAME_FONT = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Black.ttf"
SUB_FONT = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf"


def S(v):
    """Unit px (1024 space) -> supersampled px."""
    return int(round(v * SS))


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))


def vgrad(w, h, stops):
    """Vertical gradient. stops: list of (pos 0..1, (r,g,b))."""
    ys = np.linspace(0, 1, h)
    cols = np.zeros((h, 3))
    xs = [s[0] for s in stops]
    for c in range(3):
        cols[:, c] = np.interp(ys, xs, [s[1][c] for s in stops])
    arr = np.repeat(cols[:, None, :], w, axis=1)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def hgrad(w, h, stops):
    ys = np.linspace(0, 1, w)
    cols = np.zeros((w, 3))
    xs = [s[0] for s in stops]
    for c in range(3):
        cols[:, c] = np.interp(ys, xs, [s[1][c] for s in stops])
    arr = np.repeat(cols[None, :, :], h, axis=0)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def soft_blob_layer(size, blobs):
    """RGBA layer with soft radial blobs. blobs: (cx, cy, r, (r,g,b,a))."""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for cx, cy, r, col in blobs:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    return layer.filter(ImageFilter.GaussianBlur(S(18)))


def screen_glow(base, blobs, blur=S(26)):
    """Add warm light: blurred coloured blobs composited with screen."""
    glow = Image.new("RGB", base.size, (0, 0, 0))
    d = ImageDraw.Draw(glow)
    for cx, cy, r, col in blobs:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    glow = glow.filter(ImageFilter.GaussianBlur(blur))
    return ImageChops.screen(base, glow)


def add_grain(img, sigma_fine=3.0, sigma_coarse=5.0):
    """Two-scale luminance grain (subtle; smoothed again by downscale)."""
    arr = np.asarray(img).astype(np.float32)
    h, w = arr.shape[:2]
    fine = rng.normal(0, sigma_fine, (h, w))[..., None]
    coarse_small = rng.normal(0, sigma_coarse, (h // 16, w // 16))
    coarse = np.asarray(
        Image.fromarray(((coarse_small + 128).clip(0, 255)).astype(np.uint8)).resize(
            (w, h), Image.BICUBIC
        )
    ).astype(np.float32)[..., None] - 128
    out = np.clip(arr + fine + coarse, 0, 255)
    return Image.fromarray(out.astype(np.uint8), "RGB")


def brush_dabs(size, regions, n=900):
    """Short directional strokes, painterly texture. regions: (box, colors, horiz)."""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for box, colors, horiz, alpha in regions:
        x0, y0, x1, y1 = box
        for _ in range(n // len(regions)):
            x = random.uniform(x0, x1)
            y = random.uniform(y0, y1)
            ln = random.uniform(S(6), S(26))
            ang = random.uniform(-0.14, 0.14) if horiz else random.uniform(1.2, 1.9)
            dx, dy = math.cos(ang) * ln / 2, math.sin(ang) * ln / 2
            col = random.choice(colors)
            a = random.randint(max(6, alpha - 18), alpha + 14)
            d.line([(x - dx, y - dy), (x + dx, y + dy)],
                   fill=col + (a,), width=random.randint(S(1), S(3)))
    return layer.filter(ImageFilter.GaussianBlur(S(1)))


def wave_reflect(img, squish=0.52, amp=7, wavelength=110):
    """Flip vertically, squash, sine-shift each row: rippled mirror."""
    w, h = img.size
    flipped = img.transpose(Image.FLIP_TOP_BOTTOM).resize((w, int(h * squish)))
    arr = np.asarray(flipped).astype(np.float32)
    hh = arr.shape[0]
    out = np.zeros_like(arr)
    for y in range(hh):
        shift = int(amp * math.sin(2 * math.pi * y / wavelength + y * 0.015)
                    * (0.4 + 1.6 * y / hh))
        out[y] = np.roll(arr[y], shift, axis=0)
    return Image.fromarray(out.astype(np.uint8), "RGB")


def arch(d, x, y, w, h, fill):
    """Arched-top window/door: rect + semicircle top."""
    r = w / 2
    d.rectangle([x, y + r, x + w, y + h], fill=fill)
    d.pieslice([x, y, x + w, y + w], 180, 360, fill=fill)


# ---------------------------------------------------------------- canvas
canvas = Image.new("RGB", (SW, SH), (247, 242, 230))
art = Image.new("RGB", (SW, SH), (30, 20, 70))
ad = ImageDraw.Draw(art)

AX0, AY0, AX1, AY1 = S(M), S(M), S(W - M), S(H - M)
AW, AH = AX1 - AX0, AY1 - AY0

# ---------------------------------------------------------------- sky
sky = vgrad(AW, S(HY - M), [
    (0.00, (24, 14, 60)),
    (0.22, (52, 28, 98)),
    (0.45, (104, 48, 126)),
    (0.68, (166, 70, 112)),
    (0.86, (212, 116, 82)),
    (1.00, (236, 152, 92)),
])
art.paste(sky, (AX0, AY0))

# warm halo around the sun's side of the sky
art = screen_glow(art, [
    (S(SUN[0]), S(SUN[1]), S(220), (90, 50, 25)),
    (S(SUN[0]), S(SUN[1]), S(100), (115, 75, 32)),
], blur=S(40))
ad = ImageDraw.Draw(art)

# soft clouds: blurred ellipses, rose / violet / amber
cloud_layer = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
cd = ImageDraw.Draw(cloud_layer)
for _ in range(26):
    cx = random.uniform(AX0, AX1)
    cy = random.uniform(S(300), S(520))
    rw = random.uniform(S(60), S(190))
    rh = random.uniform(S(6), S(16))
    tone = random.choice([(226, 150, 140, 46), (170, 110, 160, 40),
                          (240, 180, 120, 42), (140, 90, 150, 36)])
    cd.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=tone)
cloud_layer = cloud_layer.filter(ImageFilter.GaussianBlur(S(7)))
art = Image.alpha_composite(art.convert("RGBA"), cloud_layer).convert("RGB")
ad = ImageDraw.Draw(art)

# stars (upper sky) + sparkles
for _ in range(150):
    x = random.uniform(AX0, AX1)
    y = random.uniform(AY0, S(330))
    r = random.uniform(S(0.6), S(1.8))
    a = random.randint(120, 255)
    ad.ellipse([x - r, y - r, x + r, y + r],
               fill=(255, 244, 214) if random.random() < 0.7 else (255, 255, 255))
for _ in range(12):
    x = random.uniform(AX0 + S(40), AX1 - S(40))
    y = random.uniform(AY0 + S(20), S(280))
    ln = random.uniform(S(4), S(9))
    wdt = max(1, S(1))
    ad.line([(x - ln, y), (x + ln, y)], fill=(255, 250, 230), width=wdt)
    ad.line([(x, y - ln), (x, y + ln)], fill=(255, 250, 230), width=wdt)

# birds
for _ in range(8):
    x = random.uniform(AX0 + S(60), AX1 - S(120))
    y = random.uniform(S(240), S(420))
    s = random.uniform(S(5), S(10))
    ad.arc([x - s, y - s * 0.6, x, y + s * 0.6], 200, 340,
           fill=(40, 26, 60), width=max(1, S(1)))
    ad.arc([x, y - s * 0.6, x + s, y + s * 0.6], 200, 340,
           fill=(40, 26, 60), width=max(1, S(1)))

# ---------------------------------------------------------------- sun
sun_r = S(54)
art = screen_glow(art, [
    (S(SUN[0]), S(SUN[1]), S(110), (255, 190, 90)),
    (S(SUN[0]), S(SUN[1]), S(55), (255, 220, 140)),
], blur=S(30))
ad = ImageDraw.Draw(art)
# sun disc with a gradient (pale top -> amber bottom) so it reads as a disc
disc = vgrad(S(108), S(108),
             [(0.0, (255, 246, 208)), (0.55, (255, 228, 150)),
              (1.0, (244, 192, 100))])
dmask = Image.new("L", (S(108), S(108)), 0)
ddm = ImageDraw.Draw(dmask)
ddm.ellipse([0, 0, S(108), S(108)], fill=255)
art.paste(disc, (S(SUN[0]) - S(54), S(SUN[1]) - S(54)), dmask)
ad = ImageDraw.Draw(art)
ad.ellipse([S(SUN[0]) - sun_r, S(SUN[1]) - sun_r,
            S(SUN[0]) + sun_r, S(SUN[1]) + sun_r],
           outline=(232, 176, 96), width=S(2))
# one thin cloud band crossing the low sun
ad.ellipse([S(SUN[0] - 130), S(SUN[1] + 8),
            S(SUN[0] + 130), S(SUN[1] + 16)], fill=(232, 150, 110))

# ---------------------------------------------------------------- mountains
def ridge(base_y, peaks, color):
    pts = [(AX0, S(base_y))]
    xs = np.linspace(AX0, AX1, len(peaks))
    for x, p in zip(xs, peaks):
        pts.append((x, S(base_y) - S(p)))
    pts += [(AX1, S(base_y))]
    ad.polygon(pts, fill=color)

ridge(HY, [26, 44, 30, 58, 40, 66, 34, 48, 28, 52, 30],
      (128, 92, 142))  # far, hazy
ridge(HY, [14, 22, 10, 30, 18, 26, 12, 20, 16, 24, 12],
      (76, 52, 98))  # near, darker
# haze band over the far ridge
haze = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
hd = ImageDraw.Draw(haze)
for i in range(30):
    y = S(HY - 70) + i * S(70) // 30
    hd.line([(AX0, y), (AX1, y)], fill=(196, 150, 178, 26 - i // 2))
art = Image.alpha_composite(art.convert("RGBA"), haze).convert("RGB")
ad = ImageDraw.Draw(art)

# ---------------------------------------------------------------- town
TOWN_Y = HY
lit_windows = []  # (x, y) for glow dots


def building(x, w, h, dome=True, tone=None):
    base = tone or (random.randint(208, 232), random.randint(186, 210),
                    random.randint(168, 190))
    dark = mix(base, (90, 60, 100), 0.35)
    d = ad
    d.rectangle([S(x), S(TOWN_Y - h), S(x + w), S(TOWN_Y)], fill=base)
    # shaded right side (sun is to the right of most of the town)
    d.rectangle([S(x + w * 0.72), S(TOWN_Y - h), S(x + w), S(TOWN_Y)],
                fill=mix(base, dark, 0.5))
    if dome:
        dw = w * random.uniform(0.55, 0.8)
        dx = x + (w - dw) / 2
        d.pieslice([S(dx), S(TOWN_Y - h - dw * 0.55), S(dx + dw),
                    S(TOWN_Y - h + dw * 0.45)], 180, 360, fill=mix(base, (255, 240, 210), 0.25))
        d.ellipse([S(dx + dw / 2) - S(1.5), S(TOWN_Y - h - dw * 0.55) - S(4),
                   S(dx + dw / 2) + S(1.5), S(TOWN_Y - h - dw * 0.55)], fill=(200, 140, 70))
    else:
        d.rectangle([S(x - 2), S(TOWN_Y - h - 4), S(x + w + 2), S(TOWN_Y - h)],
                    fill=mix(base, (120, 90, 110), 0.3))
    # arched windows
    n = max(1, int(w // 16))
    for i in range(n):
        wx = x + 5 + i * (w - 10) / max(1, n) + random.uniform(-1, 1)
        wy = TOWN_Y - h + 8 + random.uniform(0, max(0, h - 26))
        lit = random.random() < 0.55
        col = (255, 186, 92) if lit else (64, 44, 88)
        arch(d, S(wx), S(wy), S(6), S(10), col)
        if lit:
            lit_windows.append((S(wx + 3), S(wy + 5)))


def minaret(x, h):
    w = 11
    base = (222, 200, 178)
    ad.rectangle([S(x), S(TOWN_Y - h), S(x + w), S(TOWN_Y)], fill=base)
    ad.rectangle([S(x + w * 0.6), S(TOWN_Y - h), S(x + w), S(TOWN_Y)],
                 fill=mix(base, (90, 60, 100), 0.4))
    ad.polygon([(S(x - 2), S(TOWN_Y - h)), (S(x + w + 2), S(TOWN_Y - h)),
                (S(x + w / 2), S(TOWN_Y - h - 16))], fill=(190, 110, 70))
    ad.ellipse([S(x + w / 2) - S(1.5), S(TOWN_Y - h - 22),
                S(x + w / 2) + S(1.5), S(TOWN_Y - h - 16)], fill=(230, 180, 90))
    arch(ad, S(x + 2), S(TOWN_Y - h + 12), S(5), S(9), (255, 186, 92))
    lit_windows.append((S(x + 4.5), S(TOWN_Y - h + 16)))


x = 34
while x < 700:
    w = random.uniform(30, 66)
    h = random.uniform(20, 52)
    building(x, w, h, dome=random.random() < 0.7)
    x += w + random.uniform(2, 10)
minaret(150, 78)
minaret(486, 88)
minaret(640, 66)
# a couple of striped awnings
for ax, ay, awd in [(210, TOWN_Y - 34, 26), (420, TOWN_Y - 28, 22)]:
    for i in range(5):
        col = (196, 90, 70) if i % 2 == 0 else (244, 230, 210)
        ad.polygon([(S(ax + i * awd / 5), S(ay)),
                    (S(ax + (i + 1) * awd / 5), S(ay)),
                    (S(ax + (i + 1) * awd / 5 - 2), S(ay + 9)),
                    (S(ax + i * awd / 5 + 2), S(ay + 9))], fill=col)
# lantern dots along the waterfront
for lx in range(60, 700, 34):
    if random.random() < 0.8:
        ly = TOWN_Y - random.uniform(2, 8)
        ad.ellipse([S(lx) - S(2), S(ly) - S(2), S(lx) + S(2), S(ly) + S(2)],
                   fill=(255, 200, 110))
        lit_windows.append((S(lx), S(ly)))

# ---------------------------------------------------------------- tower
TX = 800  # tower centre x, unit px
TBASE = HY
SHAFT_TOP = 338
SHAFT_W_TOP, SHAFT_W_BOT = 44, 58

# steps
for i, (sw, sh) in enumerate([(96, 10), (82, 10), (68, 8)]):
    y0 = TBASE - (28 - i * 10)
    ad.rectangle([S(TX - sw / 2), S(y0), S(TX + sw / 2), S(y0 + 10)],
                 fill=mix((216, 202, 180), (120, 95, 110), i * 0.18))
# shaft with vertical shading (sun left -> left face lit)
shaft = Image.new("RGB", (S(SHAFT_W_BOT + 8), S(TBASE - SHAFT_TOP)), (0, 0, 0))
sg = hgrad(S(SHAFT_W_BOT + 8), S(TBASE - SHAFT_TOP),
           [(0.0, (238, 226, 200)), (0.45, (226, 212, 186)),
            (0.8, (196, 178, 158)), (1.0, (168, 148, 132))])
shaft.paste(sg, (0, 0))
sd = ImageDraw.Draw(shaft)
# taper: keep as rect, the eye reads the dome + base as taper; add banding
for yy in range(0, S(TBASE - SHAFT_TOP), S(13)):
    sd.line([(0, yy), (S(SHAFT_W_BOT + 8), yy)], fill=(170, 150, 128), width=S(1))
art.paste(shaft, (S(TX - SHAFT_W_BOT / 2 - 4), S(SHAFT_TOP)))
ad = ImageDraw.Draw(art)
# arched lit windows on the shaft
for wy in [372, 410, 448, 486]:
    arch(ad, S(TX - 7), S(wy), S(14), S(22), (255, 190, 96))
    lit_windows.append((S(TX), S(wy + 11)))
# balcony ring with balusters
ad.rectangle([S(TX - 34), S(SHAFT_TOP - 12), S(TX + 34), S(SHAFT_TOP - 2)],
             fill=(206, 188, 164))
for bx in range(-30, 31, 6):
    ad.rectangle([S(TX + bx), S(SHAFT_TOP - 22), S(TX + bx + 3), S(SHAFT_TOP - 12)],
                 fill=(188, 168, 142))
ad.rectangle([S(TX - 36), S(SHAFT_TOP - 24), S(TX + 36), S(SHAFT_TOP - 20)],
             fill=(226, 208, 184))
# copper dome: vertical gradient masked to dome shape
dome_w, dome_h = 100, 56
dome_grad = vgrad(S(dome_w), S(dome_h),
                  [(0.0, (224, 138, 80)), (0.45, (196, 104, 56)),
                   (1.0, (138, 68, 42))])
mask = Image.new("L", (S(dome_w), S(dome_h)), 0)
md = ImageDraw.Draw(mask)
md.pieslice([0, 0, S(dome_w), S(dome_h * 2)], 180, 360, fill=255)
dome = Image.new("RGBA", (S(dome_w), S(dome_h)), (0, 0, 0, 0))
dome.paste(dome_grad.convert("RGBA"), (0, 0), mask)
dd = ImageDraw.Draw(dome)
# ribs
for rx in (-28, -14, 0, 14, 28):
    dd.arc([S(rx + dome_w / 2 - 30), S(-6), S(rx + dome_w / 2 + 30), S(dome_h * 2 - 6)],
           180, 360, fill=(120, 60, 36, 90), width=S(1))
# sun-side highlight
hl = Image.new("RGBA", (S(dome_w), S(dome_h)), (0, 0, 0, 0))
hd2 = ImageDraw.Draw(hl)
hd2.ellipse([S(10), S(2), S(38), S(26)], fill=(255, 210, 150, 130))
hl = hl.filter(ImageFilter.GaussianBlur(S(4)))
dome = Image.alpha_composite(dome, hl)
art.paste(dome, (S(TX - dome_w / 2), S(SHAFT_TOP - 24 - dome_h)),
          dome)
ad = ImageDraw.Draw(art)
# beacon orb + finial + rays
bx, by = S(TX), S(SHAFT_TOP - 24 - dome_h - 10)
ad.line([(bx, S(SHAFT_TOP - 24 - dome_h)), (bx, by + S(5))],
        fill=(120, 70, 40), width=S(2))
ad.ellipse([bx - S(6), by - S(6), bx + S(6), by + S(6)], fill=(255, 226, 150))
for ang in range(0, 360, 45):
    a = math.radians(ang)
    ln = S(16) if ang % 90 == 0 else S(9)
    ad.line([(bx, by), (bx + math.cos(a) * ln, by + math.sin(a) * ln)],
            fill=(255, 230, 160), width=S(1))
# pennant flags from the balcony
for fx, fcol in [(TX - 38, (198, 84, 66)), (TX + 38, (216, 150, 70))]:
    ad.line([(S(fx), S(SHAFT_TOP - 34)), (S(fx), S(SHAFT_TOP - 12))],
            fill=(90, 60, 50), width=S(1))
    ad.polygon([(S(fx), S(SHAFT_TOP - 34)), (S(fx + 16), S(SHAFT_TOP - 30)),
                (S(fx), S(SHAFT_TOP - 26))], fill=fcol)
# arched doorway, warm
arch(ad, S(TX - 11), S(TBASE - 34), S(22), S(34), (64, 40, 66))
arch(ad, S(TX - 7), S(TBASE - 28), S(14), S(28), (255, 176, 88))

# glow for all lit windows + beacon (screen blend)
glow_blobs = [(x, y, S(14), (255, 170, 70)) for x, y in lit_windows]
glow_blobs.append((bx, by, S(34), (255, 205, 110)))
art = screen_glow(art, glow_blobs, blur=S(8))
ad = ImageDraw.Draw(art)

# ---------------------------------------------------------------- salt flat
flat = vgrad(AW, S(H - M - HY), [
    (0.00, (238, 172, 112)),
    (0.14, (216, 142, 122)),
    (0.32, (176, 112, 142)),
    (0.55, (122, 82, 142)),
    (0.78, (82, 56, 120)),
    (1.00, (50, 32, 94)),
])
art.paste(flat, (AX0, S(HY)))
ad = ImageDraw.Draw(art)

# mirrored reflection of the horizon band (town + tower + sun glow)
band = art.crop((AX0, S(HY - 150), AX1, S(HY)))
refl = wave_reflect(band, squish=0.5, amp=S(3), wavelength=S(60))
refl = refl.filter(ImageFilter.GaussianBlur(S(1)))
# tint toward water violet + fade with depth
tint = Image.new("RGB", refl.size, (150, 110, 170))
refl = Image.blend(refl, tint, 0.15)
fade = vgrad(refl.size[0], refl.size[1],
             [(0.0, (255, 255, 255)), (0.4, (205, 205, 205)),
              (1.0, (0, 0, 0))]).convert("L")
art.paste(refl, (AX0, S(HY)), fade)
ad = ImageDraw.Draw(art)

# sun reflection column: bright dashes + soft vertical glow
art = screen_glow(art, [(S(SUN[0]), S(HY + 90), S(60), (255, 190, 100))],
                  blur=S(26))
ad = ImageDraw.Draw(art)
for _ in range(240):
    t = random.random() ** 1.6
    y = HY + 6 + t * 330
    spread = 26 + t * 90
    x = SUN[0] + random.gauss(0, spread * 0.45)
    ln = random.uniform(8, 44) * (1 - t * 0.6)
    a = int(200 * (1 - t))
    col = (255, 226, 160) if random.random() < 0.6 else (255, 200, 130)
    ad.line([(S(x - ln / 2), S(y)), (S(x + ln / 2), S(y))],
            fill=col, width=max(1, S(1)))
    if random.random() < 0.12:
        ad.ellipse([S(x - 2), S(y - 1), S(x + 2), S(y + 1)], fill=(255, 240, 200))

# mirror streaks across the flat
for _ in range(210):
    t = random.random()
    y = HY + 8 + t * (H - M - HY - 16)
    x = random.uniform(M + 10, W - M - 10)
    ln = random.uniform(14, 170) * (1 - t * 0.5)
    tone = random.choice([(255, 235, 210), (240, 200, 190), (200, 180, 230),
                          (255, 210, 150)])
    ad.line([(S(x - ln / 2), S(y)), (S(x + ln / 2), S(y))],
            fill=tone, width=max(1, S(1)))
# ripples: small concentric arcs
for _ in range(10):
    x = random.uniform(M + 60, W - M - 60)
    y = random.uniform(HY + 40, H - M - 60)
    for k in range(3):
        r = S(6 + k * 7)
        ad.arc([S(x) - r, S(y) - r // 3, S(x) + r, S(y) + r // 3], 0, 180,
               fill=(255, 230, 200), width=max(1, S(1)))

# ---------------------------------------------------------------- path stones
path_pts = []
for i in range(15):
    t = i / 14
    px = lerp(512, TX - 10, t ** 1.4) + math.sin(t * 9) * 26 * (1 - t)
    py = lerp(1000, HY + 26, t ** 1.15)
    path_pts.append((px, py, lerp(26, 7, t)))
for px, py, r in reversed(path_pts):
    ad.ellipse([S(px - r), S(py - r * 0.34), S(px + r), S(py + r * 0.34)],
               fill=(214, 204, 220), outline=(150, 132, 168))
    ad.ellipse([S(px - r * 0.6), S(py - r * 0.3), S(px + r * 0.4), S(py - r * 0.05)],
               fill=(238, 230, 240))

# ---------------------------------------------------------------- people
shadow_layer = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
shd = ImageDraw.Draw(shadow_layer)
fig_glow = []


def traveller(x, y, h, robe, scarf, staff=False, lantern=False, point=False):
    """Robed figure, feet at (x, y), height h (unit px). Sun upper-right:
    shadows fall down-left, rim light on right edges."""
    # soft long shadow
    shd.ellipse([S(x - h * 0.95), S(y - h * 0.03), S(x + h * 0.25), S(y + h * 0.16)],
                fill=(30, 16, 50, 90))
    dark = mix(robe, (40, 24, 60), 0.45)
    light = mix(robe, (255, 220, 160), 0.35)
    # robe: tapered, slightly billowed
    ad.polygon([
        (S(x - h * 0.13), S(y - h * 0.80)),
        (S(x + h * 0.13), S(y - h * 0.80)),
        (S(x + h * 0.30), S(y - h * 0.06)),
        (S(x + h * 0.34), S(y)),
        (S(x - h * 0.34), S(y)),
        (S(x - h * 0.28), S(y - h * 0.10)),
    ], fill=robe)
    # shaded left half + fold lines
    ad.polygon([
        (S(x - h * 0.13), S(y - h * 0.80)),
        (S(x - h * 0.02), S(y - h * 0.80)),
        (S(x - h * 0.10), S(y - h * 0.06)),
        (S(x - h * 0.34), S(y)),
        (S(x - h * 0.28), S(y - h * 0.10)),
    ], fill=dark)
    for fx in (-0.16, 0.02, 0.18):
        ad.line([(S(x + fx * h), S(y - h * 0.72)),
                 (S(x + fx * h * 1.5), S(y - h * 0.08))],
                fill=mix(dark, robe, 0.4), width=max(1, S(1)))
    # rim light on the sun side (right edge)
    ad.line([(S(x + h * 0.13), S(y - h * 0.78)), (S(x + h * 0.33), S(y - h * 0.04))],
            fill=light, width=max(1, S(2)))
    # head + headscarf
    hy = y - h * 0.90
    ad.ellipse([S(x - h * 0.085), S(hy - h * 0.075),
                S(x + h * 0.085), S(hy + h * 0.075)], fill=(222, 178, 140))
    ad.pieslice([S(x - h * 0.115), S(hy - h * 0.105),
                 S(x + h * 0.115), S(hy + h * 0.075)], 180, 360, fill=scarf)
    ad.polygon([(S(x - h * 0.10), S(hy - h * 0.02)),
                (S(x - h * 0.20), S(y - h * 0.52)),
                (S(x - h * 0.08), S(y - h * 0.55))], fill=scarf)
    # sash
    ad.line([(S(x - h * 0.17), S(y - h * 0.52)), (S(x + h * 0.17), S(y - h * 0.46))],
            fill=mix(scarf, (255, 220, 150), 0.4), width=max(1, S(2)))
    if staff:
        ad.line([(S(x + h * 0.24), S(y - h * 0.62)), (S(x + h * 0.34), S(y + h * 0.02))],
                fill=(90, 62, 40), width=max(1, S(2)))
        ad.ellipse([S(x + h * 0.24) - S(2), S(y - h * 0.62) - S(2),
                    S(x + h * 0.24) + S(2), S(y - h * 0.62) + S(2)],
                   fill=(220, 170, 90))
    if lantern:
        lx, ly = x + h * 0.30, y - h * 0.55
        ad.line([(S(x + h * 0.16), S(y - h * 0.66)), (S(lx), S(ly))],
                fill=(90, 62, 40), width=max(1, S(1)))
        ad.ellipse([S(lx) - S(4), S(ly) - S(5), S(lx) + S(4), S(ly) + S(5)],
                   fill=(255, 200, 110))
        fig_glow.append((S(lx), S(ly), S(16), (255, 180, 80)))
    if point:
        ad.line([(S(x + h * 0.12), S(y - h * 0.66)),
                 (S(x + h * 0.48), S(y - h * 0.86))],
                fill=robe, width=max(1, S(3)))
        ad.ellipse([S(x + h * 0.48) - S(2), S(y - h * 0.86) - S(2),
                    S(x + h * 0.48) + S(2), S(y - h * 0.86) + S(2)],
                   fill=(222, 178, 140))


# group of five crossing the flat
traveller(268, 742, 62, (176, 84, 52), (232, 190, 120), staff=True)
traveller(316, 762, 68, (196, 148, 66), (120, 70, 110), lantern=True)
traveller(362, 748, 60, (70, 122, 122), (232, 190, 120), point=True)
traveller(404, 770, 66, (124, 72, 112), (196, 148, 66), staff=True)
traveller(442, 752, 58, (202, 170, 120), (176, 84, 52))
# figures near the tower + on the steps
traveller(706, 566, 40, (150, 90, 60), (220, 180, 120))
traveller(742, 560, 36, (90, 110, 130), (220, 170, 90), lantern=True)
traveller(TX - 8, TBASE - 26, 30, (180, 120, 80), (200, 160, 100))
# tiny figures on the horizon path
for tx, ty, th in [(588, 552, 17), (614, 550, 15)]:
    shd.ellipse([S(tx - th), S(ty), S(tx + th * 0.3), S(ty + th * 0.18)],
                fill=(30, 16, 50, 90))
    ad.polygon([(S(tx - th * 0.14), S(ty - th * 0.8)),
                (S(tx + th * 0.14), S(ty - th * 0.8)),
                (S(tx + th * 0.3), S(ty)), (S(tx - th * 0.3), S(ty))],
               fill=(52, 32, 70))
    ad.ellipse([S(tx - th * 0.09), S(ty - th * 0.98),
                S(tx + th * 0.09), S(ty - th * 0.8)], fill=(52, 32, 70))

shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(S(3)))
art = Image.alpha_composite(art.convert("RGBA"), shadow_layer).convert("RGB")
ad = ImageDraw.Draw(art)
if fig_glow:
    art = screen_glow(art, fig_glow, blur=S(6))
    ad = ImageDraw.Draw(art)

# ---------------------------------------------------------------- salt crystals
def crystal(x, y, s):
    """Faceted salt crystal: three tones + sparkle."""
    top = (242, 236, 250)
    left = (198, 190, 222)
    right = (148, 140, 182)
    pts_top = [(x, y - s), (x + s * 0.62, y - s * 0.28), (x, y + s * 0.1),
               (x - s * 0.62, y - s * 0.28)]
    pts_left = [(x - s * 0.62, y - s * 0.28), (x, y + s * 0.1),
                (x, y + s * 0.72), (x - s * 0.62, y + s * 0.34)]
    pts_right = [(x, y + s * 0.1), (x + s * 0.62, y - s * 0.28),
                 (x + s * 0.62, y + s * 0.34), (x, y + s * 0.72)]
    ad.polygon([(S(px), S(py)) for px, py in pts_left], fill=left)
    ad.polygon([(S(px), S(py)) for px, py in pts_right], fill=right)
    ad.polygon([(S(px), S(py)) for px, py in pts_top], fill=top)
    ad.line([(S(x), S(y - s)), (S(x), S(y + s * 0.1))],
            fill=(255, 255, 255), width=max(1, S(1)))
    if random.random() < 0.7:
        ad.ellipse([S(x - 2), S(y - s * 0.5) - S(2), S(x + 2), S(y - s * 0.5) + S(2)],
                   fill=(255, 255, 255))


for cx, cy, cs in [(70, 950, 46), (130, 972, 58), (200, 952, 38), (36, 986, 30),
                   (900, 956, 52), (950, 980, 44), (842, 976, 34), (988, 946, 28)]:
    crystal(cx, cy, cs)
for _ in range(10):
    crystal(random.uniform(80, 940), random.uniform(620, 880),
            random.uniform(8, 18))

# ---------------------------------------------------------------- brush texture
dabs = brush_dabs((SW, SH), [
    ((AX0, AY0, AX1, S(540)),
     [(240, 200, 180), (170, 120, 190), (255, 220, 170), (120, 80, 160)],
     True, 20),
    ((AX0, S(545), AX1, AY1),
     [(255, 225, 190), (200, 160, 210), (150, 110, 180), (240, 180, 140)],
     True, 20),
    ((S(700), S(280), S(900), S(560)),
     [(240, 220, 190), (200, 170, 150), (230, 170, 110)],
     False, 18),
], n=900)
art = Image.alpha_composite(art.convert("RGBA"), dabs).convert("RGB")

# ---------------------------------------------------------------- grain + vignette
art = add_grain(art, sigma_fine=1.6, sigma_coarse=2.2)
vig = Image.new("L", (SW, SH), 0)
vd = ImageDraw.Draw(vig)
vd.ellipse([-SW * 0.25, -SH * 0.25, SW * 1.25, SH * 1.25], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(S(180)))
dark = Image.new("RGB", (SW, SH), (18, 10, 40))
art = Image.composite(art, Image.blend(art, dark, 0.22), vig)

# ---------------------------------------------------------------- frame + text
canvas.paste(art.crop((AX0, AY0, AX1, AY1)), (AX0, AY0))
cd = ImageDraw.Draw(canvas)
cd.rectangle([AX0 - S(2), AY0 - S(2), AX1 + S(2), AY1 + S(2)],
             outline=(74, 52, 84), width=S(2))

# name: fit to width
NAME = "SALMIRA"
target_w = S(880)
size = S(200)
font = ImageFont.truetype(NAME_FONT, size)
tw = cd.textlength(NAME, font=font)
font = ImageFont.truetype(NAME_FONT, int(size * target_w / tw))
name_w = cd.textlength(NAME, font=font)
nx = (SW - name_w) / 2
ny = S(58)
# soft dark shadow for legibility, then cream letters
cd.text((nx + S(3), ny + S(4)), NAME, font=font, fill=(30, 18, 56))
cd.text((nx, ny), NAME, font=font, fill=(250, 244, 224))
name_ink_bottom = cd.textbbox((nx, ny), NAME, font=font)[3]

# subtitle, letterspaced gold with flanking rules, below the name's ink
SUB = "WHERE THE SKY LIVES TWICE"
sub_size = S(27)
sfont = ImageFont.truetype(SUB_FONT, sub_size)
spacing = S(9)
widths = [cd.textlength(ch, font=sfont) for ch in SUB]
total = sum(widths) + spacing * (len(SUB) - 1)
sx = S(472) - total / 2  # centred left of the tower dome
sy = name_ink_bottom + S(14)
cd.line([(sx - S(64), sy + S(14)), (sx - S(14), sy + S(14))],
        fill=(233, 200, 122), width=S(2))
cd.line([(sx + total + S(14), sy + S(14)), (sx + total + S(40), sy + S(14))],
        fill=(233, 200, 122), width=S(2))
cx = sx
for ch, wch in zip(SUB, widths):
    cd.text((cx + S(1), sy + S(2)), ch, font=sfont, fill=(40, 24, 66))
    cd.text((cx, sy), ch, font=sfont, fill=(233, 200, 122))
    cx += wch + spacing

# ---------------------------------------------------------------- finish
final = canvas.resize((W, H), Image.LANCZOS)
final.save("entry.png", optimize=True)
print("saved entry.png")
