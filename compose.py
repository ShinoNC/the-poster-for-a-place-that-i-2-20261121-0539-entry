#!/usr/bin/env python3
"""SALMIRA v2 — a rich, painterly travel poster of a salt-flat mirror town.

Fresh build for the-poster-for-a-place-that-i-2-20261121-0539 (v2).
Renders at 2x (2048) and downscales to the 1024x1024 gate size.
Deterministic: fixed seed, no network, no time input.
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SEED = 20261121
rng = random.Random(SEED)
np_rng = np.random.default_rng(SEED)

S = 2                      # supersample factor
W = H = 1024 * S
FRAME = 26 * S             # cream frame width
INNER = 30 * S             # inner rule offset
HORIZON = 548 * S          # horizon line (mirror below)

CREAM = (244, 236, 214)
NAME_COLOR = (250, 242, 222)
SUB_COLOR = (255, 216, 150)
INK = (58, 38, 66)

FONT_NAME = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Black.ttf"
FONT_SUB = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"


def x(v):
    """1024-space coordinate -> work coordinate."""
    return int(round(v * S))


def pts(points):
    return [(x(px), x(py)) for px, py in points]


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def vgrad(width, height, stops):
    """Vertical gradient image from a list of (pos0to1, rgb) stops."""
    ys = np.linspace(0.0, 1.0, height)
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    pos = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], dtype=np.float64)
    for ch in range(3):
        arr[:, :, ch] = np.interp(ys, pos, cols[:, ch])[:, None]
    return Image.fromarray(arr, "RGB")


def soft_ellipse(layer, cx, cy, rx, ry, color, blur):
    """Draw a blurred filled ellipse onto an RGBA layer (1024-space coords)."""
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    d.ellipse([x(cx - rx), x(cy - ry), x(cx + rx), x(cy + ry)], fill=color)
    tmp = tmp.filter(ImageFilter.GaussianBlur(x(blur)))
    layer.alpha_composite(tmp)


def glow_dot(layer, cx, cy, r, color, blur):
    soft_ellipse(layer, cx, cy, r, r, color, blur)


def person(draw, bx, by, h, color, rim, staff=False, lantern=False):
    """A small walking silhouette. (bx, by) = feet, h = height (1024-space)."""
    head_r = h * 0.11
    hip = by - h * 0.48
    shoulder = by - h * 0.78
    head_cy = by - h * 0.90
    # long shadow toward the viewer-left (sun sits right)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    ds.ellipse([x(bx - h * 0.85), x(by - h * 0.06), x(bx + h * 0.25),
                x(by + h * 0.10)], fill=(30, 20, 55, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(x(3)))
    draw._image.alpha_composite(sh)
    # legs
    draw.line([x(bx), x(hip), x(bx - h * 0.10), x(by)], fill=color, width=x(4))
    draw.line([x(bx), x(hip), x(bx + h * 0.13), x(by)], fill=color, width=x(4))
    # robe / torso (slightly tapered)
    draw.polygon(pts([(bx - h * 0.10, shoulder), (bx + h * 0.10, shoulder),
                      (bx + h * 0.13, hip), (bx - h * 0.11, hip)]), fill=color)
    # head
    draw.ellipse([x(bx - head_r), x(head_cy - head_r),
                  x(bx + head_r), x(head_cy + head_r)], fill=color)
    # warm rim light on the sun side (right edge)
    draw.arc([x(bx - head_r), x(head_cy - head_r),
              x(bx + head_r), x(head_cy + head_r)],
             start=-70, end=70, fill=rim, width=x(2))
    draw.line([x(bx + h * 0.10), x(shoulder), x(bx + h * 0.12), x(hip)],
              fill=rim, width=x(2))
    if staff:
        draw.line([x(bx + h * 0.22), x(by - h * 1.05), x(bx + h * 0.16), x(by)],
                  fill=color, width=x(3))
    if lantern:
        lx, ly = bx - h * 0.20, by - h * 0.55
        draw.line([x(bx - h * 0.08), x(shoulder + h * 0.10), x(lx), x(ly)],
                  fill=color, width=x(3))
        draw.ellipse([x(lx - 3), x(ly - 4), x(lx + 3), x(ly + 4)],
                     fill=(255, 200, 110))


def main():
    # ---------- base: sky gradient over the whole canvas ----------
    sky = vgrad(W, H, [
        (0.00, (28, 16, 58)),
        (0.16, (56, 26, 86)),
        (0.32, (108, 46, 104)),
        (0.45, (176, 82, 104)),
        (0.52, (228, 136, 96)),
        (0.56, (252, 190, 120)),
        (0.62, (255, 210, 150)),
        (0.72, (216, 132, 108)),
        (0.82, (140, 74, 108)),
        (0.92, (72, 40, 96)),
        (1.00, (36, 22, 66)),
    ])
    img = sky.convert("RGBA")
    draw = ImageDraw.Draw(img)

    # ---------- stars (upper sky only) ----------
    stars = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(stars)
    for _ in range(260):
        sx = rng.uniform(0, 1024)
        sy = rng.uniform(0, 300) * (1.0 - rng.random() ** 2 * 0.4)
        r = rng.choice([0.7, 0.9, 1.2, 1.6])
        a = rng.randint(90, 230)
        ds.ellipse([x(sx - r), x(sy - r), x(sx + r), x(sy + r)],
                   fill=(255, 244, 220, a))
    # a few bright stars with a cross sparkle
    for _ in range(8):
        sx = rng.uniform(40, 980)
        sy = rng.uniform(20, 240)
        r = rng.uniform(1.6, 2.4)
        ds.ellipse([x(sx - r), x(sy - r), x(sx + r), x(sy + r)],
                   fill=(255, 250, 235, 255))
        ds.line([x(sx - r * 3), x(sy), x(sx + r * 3), x(sy)],
                fill=(255, 250, 235, 160), width=x(1))
        ds.line([x(sx), x(sy - r * 3), x(sx), x(sy + r * 3)],
                fill=(255, 250, 235, 160), width=x(1))
    img.alpha_composite(stars)

    # ---------- clouds: soft painterly bands ----------
    clouds = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for (cx, cy, rx, ry, col) in [
        (180, 300, 190, 26, (232, 140, 130, 70)),
        (420, 330, 240, 30, (240, 160, 130, 60)),
        (760, 285, 200, 24, (226, 130, 140, 65)),
        (880, 380, 150, 20, (255, 190, 140, 55)),
        (120, 430, 170, 22, (250, 180, 140, 50)),
        (560, 420, 260, 26, (244, 170, 140, 55)),
        (300, 250, 130, 16, (200, 120, 150, 50)),
        (940, 240, 110, 15, (210, 130, 150, 50)),
    ]:
        soft_ellipse(clouds, cx, cy, rx, ry, col, 14)
    img.alpha_composite(clouds)

    # ---------- sun + glow ----------
    sun_cx, sun_cy, sun_r = 610, 468, 56
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_dot(halo, sun_cx, sun_cy, 190, (255, 190, 120, 90), 60)
    glow_dot(halo, sun_cx, sun_cy, 110, (255, 215, 150, 110), 40)
    img.alpha_composite(halo)
    draw = ImageDraw.Draw(img)
    draw.ellipse([x(sun_cx - sun_r), x(sun_cy - sun_r),
                  x(sun_cx + sun_r), x(sun_cy + sun_r)],
                 fill=(255, 238, 190, 255))
    draw.ellipse([x(sun_cx - sun_r), x(sun_cy - sun_r),
                  x(sun_cx + sun_r), x(sun_cy + sun_r)],
                 outline=(255, 210, 140, 255), width=x(3))

    # ---------- birds ----------
    draw = ImageDraw.Draw(img)
    for (bx, by, s) in [(150, 300, 9), (185, 318, 7), (210, 292, 8),
                        (850, 330, 8), (885, 312, 10), (915, 335, 7),
                        (480, 260, 7), (520, 278, 6), (95, 360, 8)]:
        draw.arc([x(bx - s), x(by - s * 0.6), x(bx), x(by + s * 0.6)],
                 start=200, end=330, fill=(40, 26, 60, 220), width=x(2))
        draw.arc([x(bx), x(by - s * 0.6), x(bx + s), x(by + s * 0.6)],
                 start=210, end=340, fill=(40, 26, 60, 220), width=x(2))

    # ---------- mountains: two layers ----------
    draw = ImageDraw.Draw(img)
    far = [(0, 548), (0, 505), (90, 478), (180, 500), (280, 470),
           (380, 498), (470, 482), (560, 505), (700, 490), (820, 508),
           (940, 484), (1024, 500), (1024, 548)]
    draw.polygon(pts(far), fill=(150, 104, 138, 255))
    near = [(0, 548), (0, 522), (120, 512), (240, 530), (360, 514),
            (520, 532), (660, 516), (800, 530), (920, 518), (1024, 528),
            (1024, 548)]
    draw.polygon(pts(near), fill=(74, 48, 88, 255))

    # ---------- town: domed buildings with lit windows ----------
    town = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dt = ImageDraw.Draw(town)
    buildings = [
        # (x0, width, height, dome?)
        (52, 46, 34, True), (104, 34, 24, True), (144, 40, 30, True),
        (190, 30, 20, False), (226, 52, 40, True), (284, 36, 26, True),
        (326, 28, 18, False), (360, 60, 46, True), (426, 38, 28, True),
        (470, 30, 22, False), (506, 44, 34, True),
    ]
    for (bx, bw, bh, dome) in buildings:
        top = 548 - bh
        dt.rectangle([x(bx), x(top), x(bx + bw), x(548)],
                     fill=(238, 226, 204, 255))
        if dome:
            dt.pieslice([x(bx + bw * 0.12), x(top - bw * 0.42),
                         x(bx + bw * 0.88), x(top + bw * 0.42)],
                        start=180, end=360, fill=(244, 232, 210, 255))
        # lit windows
        for wx in range(bx + 8, bx + bw - 6, 12):
            wy = top + rng.randint(8, max(9, bh - 12))
            dt.rectangle([x(wx), x(wy), x(wx + 5), x(wy + 7)],
                         fill=(255, 196, 110, 255))
    # two slender minarets
    for mx in (170, 452):
        dt.rectangle([x(mx), x(548 - 62), x(mx + 9), x(548)],
                     fill=(232, 220, 198, 255))
        dt.polygon(pts([(mx - 2, 548 - 62), (mx + 11, 548 - 62),
                        (mx + 4.5, 548 - 78)]), fill=(214, 128, 84, 255))
        dt.rectangle([x(mx + 2), x(548 - 52), x(mx + 7), x(548 - 44)],
                     fill=(255, 200, 120, 255))
    # warm glow dots over the town windows
    for _ in range(40):
        gx = rng.uniform(55, 545)
        gy = rng.uniform(500, 542)
        glow_dot(town, gx, gy, rng.uniform(3, 6), (255, 200, 120, 60), 4)
    img.alpha_composite(town)

    # ---------- observatory tower (own layer, for a true reflection) ----------
    tower = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dt = ImageDraw.Draw(tower)
    tx = 758                      # tower centre x
    base_y = 548
    # stepped platform
    for i, (w, h) in enumerate([(120, 8), (100, 8), (80, 8)]):
        dt.rectangle([x(tx - w / 2), x(base_y - 24 + i * 8),
                      x(tx + w / 2), x(base_y - 16 + i * 8)],
                     fill=lerp((226, 214, 188), (170, 158, 140), i / 2))
    # shaft (slightly tapered, stone bands)
    dt.polygon(pts([(tx - 30, 524), (tx - 24, 404),
                    (tx + 24, 404), (tx + 30, 524)]),
               fill=(233, 223, 201, 255))
    for by in range(424, 520, 24):
        t = (by - 404) / (524 - 404)
        half = 24 + (30 - 24) * t
        dt.line([x(tx - half), x(by), x(tx + half), x(by)],
                fill=(198, 186, 164, 255), width=x(2))
    # shaded left edge of the shaft
    dt.polygon(pts([(tx - 30, 524), (tx - 24, 404),
                    (tx - 18, 404), (tx - 22, 524)]),
               fill=(196, 184, 162, 255))
    # lit arched windows up the shaft
    for wy in (418, 446, 474, 500):
        dt.rounded_rectangle([x(tx - 7), x(wy), x(tx + 7), x(wy + 22)],
                             radius=x(6), fill=(255, 198, 112, 255))
        glow_dot(tower, tx, wy + 11, 12, (255, 200, 120, 70), 6)
    # balcony ring
    dt.rectangle([x(tx - 40), x(392), x(tx + 40), x(404)],
                 fill=(214, 200, 176, 255))
    for rx in range(tx - 36, tx + 37, 8):
        dt.line([x(rx), x(384), x(rx), x(392)], fill=(150, 138, 118, 255),
                width=x(2))
    dt.rectangle([x(tx - 40), x(382), x(tx + 40), x(385)],
                 fill=(150, 138, 118, 255))
    # copper dome: smooth vertical gradient clipped to the dome shape
    dw, dh = x(104), x(104)
    dgrad = vgrad(dw, dh, [(0.0, (240, 150, 84)), (0.45, (208, 114, 62)),
                           (1.0, (162, 80, 46))]).convert("RGBA")
    dmask = Image.new("L", (dw, dh), 0)
    ImageDraw.Draw(dmask).pieslice([0, 0, dw - 1, dh - 1], 180, 360,
                                   fill=255)
    dome_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dome_layer.paste(dgrad, (x(tx - 52), x(300)), dmask)
    tower.alpha_composite(dome_layer)
    dt = ImageDraw.Draw(tower)
    # sun-side highlight on the dome
    hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    soft_ellipse(hl, tx + 22, 330, 26, 34, (255, 196, 130, 120), 12)
    tower.alpha_composite(hl)
    dt = ImageDraw.Draw(tower)
    dt.arc([x(tx - 52), x(300), x(tx + 52), x(404)], start=200, end=340,
           fill=(255, 186, 118, 255), width=x(4))
    # dome window (dark slit with warm glass)
    dt.rounded_rectangle([x(tx - 6), x(326), x(tx + 6), x(370)],
                         radius=x(5), fill=(52, 30, 66, 255))
    dt.rounded_rectangle([x(tx - 3), x(330), x(tx + 3), x(366)],
                         radius=x(3), fill=(255, 190, 110, 255))
    # finial + beacon orb (sits just above the dome, clear of the subtitle)
    dt.line([x(tx), x(300), x(tx), x(286)], fill=(120, 84, 60, 255),
            width=x(4))
    dt.ellipse([x(tx - 6), x(282), x(tx + 6), x(294)],
               fill=(255, 214, 140, 255))
    img.alpha_composite(tower)

    # beacon glow + star rays (above everything local)
    beacon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_dot(beacon, tx, 288, 30, (255, 210, 130, 110), 16)
    glow_dot(beacon, tx, 288, 14, (255, 235, 190, 150), 7)
    db = ImageDraw.Draw(beacon)
    for (dx, dy) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        db.polygon(pts([(tx, 288), (tx + dx * 24, 288 + dy * 24 + 2),
                        (tx + dx * 24, 288 + dy * 24 - 2)]),
                   fill=(255, 240, 200, 160))
    img.alpha_composite(beacon)

    # ---------- mirror: reflection of tower + town ----------
    # flip the tower layer around the horizon line
    crop = tower.crop((0, 0, W, HORIZON))
    refl = crop.transpose(Image.FLIP_TOP_BOTTOM)
    refl_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    refl_layer.paste(refl, (0, HORIZON))
    # ripple: shift each row of the reflection band by a gentle wobble
    arr = np.array(refl_layer)
    band = arr[HORIZON:HORIZON + x(320)]
    for j in range(band.shape[0]):
        shift = int(round(math.sin(j * 0.07) * 2.0 *
                          (1 + j / 320.0) + np_rng.normal(0, 0.8)))
        if shift:
            band[j] = np.roll(band[j], shift, axis=0)
    # water tints the reflection toward the mirror's mauve, then it
    # fades with depth
    rgb = band[:, :, :3].astype(np.float64)
    band[:, :, :3] = (rgb * 0.72 +
                      np.array([150.0, 90.0, 120.0]) * 0.28).astype(np.uint8)
    fade = np.linspace(0.88, 0.25, band.shape[0])[:, None]
    band[:, :, 3] = (band[:, :, 3].astype(np.float64) * fade).astype(np.uint8)
    arr[HORIZON:HORIZON + x(320)] = band
    refl_layer = Image.fromarray(arr, "RGBA")
    img.alpha_composite(refl_layer)

    # soft dark reflection of the town band
    town_refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dt = ImageDraw.Draw(town_refl)
    dt.rectangle([x(52), x(548), x(550), x(585)], fill=(90, 60, 100, 90))
    town_refl = town_refl.filter(ImageFilter.GaussianBlur(x(6)))
    img.alpha_composite(town_refl)

    # ---------- sun reflection column ----------
    draw = ImageDraw.Draw(img)
    for _ in range(150):
        cy = rng.uniform(550, 900)
        spread = 14 + (cy - 550) * 0.16
        cx = 610 + rng.gauss(0, spread)
        ln = rng.uniform(6, 34) * (1.0 - (cy - 550) / 700)
        a = int(rng.uniform(90, 220) * (1.0 - (cy - 550) / 800))
        draw.line([x(cx - ln / 2), x(cy), x(cx + ln / 2), x(cy)],
                  fill=(255, 216, 150, max(20, a)), width=x(2))

    # ---------- mirror streaks + salt cracks ----------
    draw = ImageDraw.Draw(img)
    for _ in range(170):
        cy = rng.uniform(560, 990)
        cx = rng.uniform(40, 990)
        ln = rng.uniform(12, 130)
        col = rng.choice([(255, 240, 220, 70), (255, 220, 180, 60),
                          (220, 200, 230, 55), (255, 200, 150, 50)])
        draw.line([x(cx - ln / 2), x(cy), x(cx + ln / 2), x(cy)],
                  fill=col, width=x(1))
    for _ in range(9):
        cx = rng.uniform(60, 960)
        cy = rng.uniform(620, 980)
        pts_c = [(cx, cy)]
        for _ in range(rng.randint(2, 3)):
            cx += rng.uniform(-30, 30)
            cy += rng.uniform(-10, 18)
            pts_c.append((cx, cy))
        draw.line(pts(pts_c), fill=(52, 32, 76, 70), width=x(1),
                  joint="curve")

    # ---------- people ----------
    people = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dp = ImageDraw.Draw(people)
    SIL = (38, 26, 58, 255)
    RIM = (255, 190, 130, 255)
    # a group crossing the flat, left to right
    group = [(196, 742, 62, False, False), (248, 762, 70, True, False),
             (302, 748, 58, False, True), (352, 778, 66, False, False),
             (404, 762, 60, True, False)]
    for (gx, gy, gh, staff, lant) in group:
        person(dp, gx, gy, gh, SIL, RIM, staff=staff, lantern=lant)
    # two figures near the tower base, one on the steps
    person(dp, 688, 648, 58, SIL, RIM)
    person(dp, 838, 668, 62, SIL, RIM, lantern=True)
    person(dp, 724, 528, 30, SIL, RIM)
    # two small figures on the horizon path
    person(dp, 596, 566, 26, SIL, RIM)
    person(dp, 628, 570, 24, SIL, RIM)
    img.alpha_composite(people)
    # lantern glows
    lan = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_dot(lan, 302 - 0.20 * 58, 748 - 0.55 * 58, 16,
             (255, 200, 120, 110), 8)
    glow_dot(lan, 838 - 0.20 * 62, 668 - 0.55 * 62, 16,
             (255, 200, 120, 110), 8)
    img.alpha_composite(lan)

    # ---------- winding path of flat stones ----------
    draw = ImageDraw.Draw(img)
    path = [(512, 998), (540, 940), (566, 880), (596, 824), (624, 772),
            (652, 724), (678, 680), (702, 640), (722, 606), (738, 578)]
    for i, (px, py) in enumerate(path):
        t = i / (len(path) - 1)
        rx = 22 - 15 * t
        ry = 5 - 3 * t
        stone = []
        for k in range(8):
            ang = 2 * math.pi * k / 8
            jit = 1.0 + rng.uniform(-0.18, 0.18)
            stone.append((px + math.cos(ang) * rx * jit,
                          py + math.sin(ang) * ry * jit))
        draw.polygon(pts(stone),
                     fill=lerp((226, 208, 196), (196, 172, 172), t))
        draw.polygon(pts(stone), outline=(140, 110, 130, 140))

    # ---------- foreground salt crystals ----------
    def crystal(cx, cy, s, flip=False):
        pts_c = [(cx, cy - s), (cx + s * 0.8, cy - s * 0.25),
                 (cx + s * 0.55, cy + s * 0.55), (cx - s * 0.45, cy + s * 0.6),
                 (cx - s * 0.85, cy - s * 0.1)]
        if flip:
            pts_c = [(cx - (px - cx), py) for px, py in pts_c]
        draw.polygon(pts(pts_c), fill=(246, 238, 226, 255))
        draw.polygon(pts([(cx, cy - s), (cx + s * 0.8, cy - s * 0.25),
                          (cx + s * 0.55, cy + s * 0.55), (cx, cy + s * 0.2)]),
                     fill=(214, 196, 214, 255))
        draw.line(pts([(cx, cy - s), (cx + s * 0.8, cy - s * 0.25)]),
                  fill=(255, 250, 240, 255), width=x(2))

    draw = ImageDraw.Draw(img)
    for (cx, cy, s) in [(110, 950, 44), (190, 972, 58), (268, 946, 36),
                        (70, 990, 30), (150, 912, 26), (240, 990, 28),
                        (860, 952, 48), (940, 974, 60), (800, 982, 32),
                        (990, 920, 26), (905, 910, 24)]:
        crystal(cx, cy, s, flip=rng.random() < 0.5)
    # scattered small crystals mid-flat
    for _ in range(16):
        crystal(rng.uniform(60, 960), rng.uniform(600, 860),
                rng.uniform(6, 14), flip=rng.random() < 0.5)

    # ---------- painterly dabs + grain + vignette ----------
    dabs = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for _ in range(60):
        cx = rng.uniform(0, 1024)
        cy = rng.uniform(0, 1024)
        r = rng.uniform(14, 60)
        col = rng.choice([(255, 200, 150, 16), (200, 140, 180, 14),
                          (255, 230, 190, 14), (140, 100, 160, 14)])
        soft_ellipse(dabs, cx, cy, r, r * 0.55, col, 10)
    img.alpha_composite(dabs)

    arr = np.array(img.convert("RGB")).astype(np.int16)
    noise = np_rng.normal(0, 2.5, arr.shape[:2])[..., None]
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "RGB").convert("RGBA")
    # vignette
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 +
                   ((yy - H / 2) / (H / 2)) ** 2)
    vig = np.clip(1.0 - 0.16 * np.clip(dist - 0.72, 0, None) ** 2 * 4,
                  0.82, 1.0)
    arr = np.array(img.convert("RGB")).astype(np.float64)
    arr = np.clip(arr * vig[..., None], 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "RGB").convert("RGBA")

    # ---------- frame ----------
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W - 1, H - 1], outline=CREAM + (255,),
                   width=FRAME)
    draw.rectangle([INNER, INNER, W - 1 - INNER, H - 1 - INNER],
                   outline=(90, 64, 84, 255), width=x(2))

    # ---------- name + subtitle ----------
    draw = ImageDraw.Draw(img)
    name = "SALMIRA"
    size = x(170)
    while True:
        font = ImageFont.truetype(FONT_NAME, size)
        bbox = draw.textbbox((0, 0), name, font=font)
        if bbox[2] - bbox[0] <= x(900) or size <= x(100):
            break
        size -= x(4)
    tw = bbox[2] - bbox[0]
    name_x = x(512) - tw / 2 - bbox[0]
    name_y = x(60)
    draw.text((name_x, name_y), name, font=font, fill=NAME_COLOR + (255,))
    # measure the name's real ink bottom so the subtitle never overlaps
    probe = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(probe).text((name_x, name_y), name, font=font,
                               fill=(255, 255, 255, 255))
    ink_bottom = probe.getbbox()[3] / S

    sub = "WHERE THE SKY LIVES TWICE"
    sub_size = x(30)
    sub_font = ImageFont.truetype(FONT_SUB, sub_size)
    tracking = x(9)
    widths = [draw.textbbox((0, 0), ch, font=sub_font)[2] for ch in sub]
    total = sum(widths) + tracking * (len(sub) - 1)
    sx = x(512) - total / 2
    sy = x(ink_bottom + 16)
    # rules flanking the subtitle
    rule_y = sy + x(15)
    draw.line([x(120), rule_y, sx - x(28), rule_y],
              fill=(255, 214, 150, 255), width=x(2))
    draw.line([sx + total + x(28), rule_y, x(904), rule_y],
              fill=(255, 214, 150, 255), width=x(2))
    for ch, wch in zip(sub, widths):
        draw.text((sx, sy), ch, font=sub_font, fill=SUB_COLOR + (255,))
        sx += wch + tracking

    # ---------- downscale + save ----------
    out = img.convert("RGB").resize((1024, 1024), Image.LANCZOS)
    out.save("entry.png", optimize=True)
    out.resize((480, 480), Image.LANCZOS).save("preview-480.png",
                                               optimize=True)
    print("saved entry.png + preview-480.png")


if __name__ == "__main__":
    main()
