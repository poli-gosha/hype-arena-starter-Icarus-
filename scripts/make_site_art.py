"""Render the main page's pixel art from the film's own drawing code (video/inspection/art.py).

    video\\.venv\\Scripts\\python.exe scripts\\make_site_art.py

Writes server/static/assets/: Caesar's sprite sheet (sprites/caesar.png + .json), the props,
the desk scenes as frame atlases (scenes/*.png + scenes.json), the backgrounds of the hands-on
desks and of the cheese game, the stamps, and the sounds (sounds/*.wav).
"""
from __future__ import annotations

import json
import math
import random
import shutil
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "video" / "inspection"))

from PIL import Image, ImageDraw  # noqa: E402

import art  # noqa: E402
from art import (GREEN, GREEN_DK, INK, LAMP, MOUSE, MOUSE_DK, PAPER, PAPER_SH, PINK, RED, VEST, VISOR,  # noqa: E402
                 VISOR_LT, WOOD, WOOD_DK, WOOD_HI, WALL, WALL_DK, WALL_LT, NIGHT, draw, stamp_img, text)
import story  # noqa: E402
import sound  # noqa: E402

OUT = ROOT / "server" / "static" / "assets"
FW, FH, BX, BY = 72, 72, 36, 64  # a sprite frame, and Caesar's feet in it


# =====================================================================================
# CAESAR
# =====================================================================================
def caesar(d, x, y, *, arm=None, arm2=None, nod=0, legs="stand", step=0, eyes="open", mouth=None, laurel=False,
           wings=None, halo=False, body=MOUSE, body_dk=MOUSE_DK, vest=VEST, lamp=False, prop=None, breathe=0,
           tail=0, collar=None):
    """The film's Clerk, snout to the right, with what the site needs on top: eyes and mouth for
    every mood, a laurel, wings and a halo, props in hand."""
    X = lambda dx: x + dx  # noqa: E731
    if wings is not None:  # behind everything
        up = 5 if wings % 2 else -2
        for k, off in ((0, 2), (1, 0)):
            d.polygon([(X(-3 + off), y - 19), (X(-13 + off), y - 33 - up), (X(-21 + off), y - 28 - up),
                       (X(-18 + off), y - 19), (X(-9 + off), y - 13)],
                      fill=(214, 218, 226) if k == 0 else (244, 244, 238), outline=(160, 166, 178))
    t = [(X(-8), y - 3), (X(-15), y - 1 - tail), (X(-20), y - 5 - tail), (X(-21), y - 11 - tail), (X(-18), y - 14 - tail)]
    d.line(t, fill=PINK, width=2)
    # feet
    if legs == "walk":
        for k, dx in enumerate((-4, 3)):
            lift = 2 if k == step % 2 else 0
            d.rectangle([X(dx - 1), y - 1 - lift, X(dx + 2), y + 4 - lift], fill=body_dk)
            d.rectangle([X(dx), y + 3 - lift, X(dx + 3), y + 5 - lift], fill=PINK)
    elif legs == "dangle":
        for dx in (-4, 3):
            d.line([(X(dx), y - 1), (X(dx), y + 5)], fill=body_dk, width=2)
            d.rectangle([X(dx), y + 5, X(dx + 2), y + 6], fill=PINK)
    else:
        for dx in (-5, 2):
            d.rectangle([X(dx), y - 1, X(dx + 3), y + 3], fill=body_dk)
            d.rectangle([X(dx + 1), y + 3, X(dx + 4), y + 4], fill=PINK)
    by = breathe
    d.ellipse([X(-9), y - 24 + by, X(9), y], fill=body, outline=body_dk)
    d.polygon([(X(7), y - 15 + by), (X(1), y - 20 + by), (X(-7), y - 17 + by), (X(-8), y - 6), (X(5), y - 3)], fill=vest)
    d.line([(X(1), y - 19 + by), (X(2), y - 4)], fill=tuple(max(0, v - 27) for v in vest))
    if collar:
        d.rectangle([X(-3), y - 23 + by, X(5), y - 20 + by], fill=collar)
    # head
    hx, hy = X(3), y - 31 + round(nod) + by
    Hh = lambda dx: hx + dx  # noqa: E731
    d.ellipse([Hh(-2), hy - 18, Hh(14), hy - 6], fill=body_dk)  # far ear
    d.ellipse([Hh(-9), hy - 8, Hh(9), hy + 7], fill=body, outline=body_dk)
    d.ellipse([Hh(5), hy - 3, Hh(17), hy + 5], fill=body, outline=body_dk)  # snout
    d.rectangle([Hh(17), hy - 1, Hh(19), hy + 1], fill=PINK)  # nose
    d.ellipse([Hh(-8), hy - 19, Hh(4), hy - 7], fill=body, outline=body_dk)  # near ear
    d.ellipse([Hh(-5), hy - 16, Hh(1), hy - 10], fill=PINK)
    d.polygon([(Hh(8), hy - 6), (Hh(-7), hy - 8), (Hh(-8), hy - 5), (Hh(7), hy - 3)], fill=VISOR)
    d.polygon([(Hh(7), hy - 5), (Hh(18), hy - 3), (Hh(17), hy - 1), (Hh(7), hy - 2)], fill=VISOR_LT)
    if laurel:  # the emperor's wreath, round the back of the head
        for k in range(7):
            a = math.radians(205 + k * 22)
            lx, ly = hx - 1 + 11 * math.cos(a), hy - 4 + 10 * math.sin(a)
            d.ellipse([lx - 2, ly - 1, lx + 2, ly + 2], fill=GREEN, outline=GREEN_DK)
    if halo:
        d.ellipse([hx - 8, hy - 27, hx + 8, hy - 22], outline=LAMP, width=2)
    # eyes behind the round glasses
    if eyes == "x":
        d.line([(Hh(5), hy - 3), (Hh(9), hy + 1)], fill=INK)
        d.line([(Hh(5), hy + 1), (Hh(9), hy - 3)], fill=INK)
    elif eyes == "closed":
        d.line([(Hh(6), hy), (Hh(8), hy)], fill=INK)
    elif eyes == "happy":
        d.line([(Hh(5), hy + 1), (Hh(7), hy - 1), (Hh(9), hy + 1)], fill=INK)
    elif eyes == "wide":
        d.rectangle([Hh(6), hy - 2, Hh(9), hy + 1], fill=PAPER)
        d.rectangle([Hh(7), hy - 1, Hh(8), hy], fill=INK)
    else:
        d.rectangle([Hh(7), hy - 1, Hh(8), hy], fill=INK)
    if eyes != "x":
        d.ellipse([Hh(4), hy - 3, Hh(11), hy + 3], outline=INK)
        d.point((Hh(10), hy - 2), fill=PAPER)
    for k, (a, b) in enumerate(((2, 1), (3, 5))):
        d.line([(Hh(15), hy + a), (Hh(23), hy + b - k)], fill=body_dk)
    if mouth in ("open", "tongue"):
        d.ellipse([Hh(9), hy + 2, Hh(15), hy + 7], fill=INK)
        if mouth == "tongue":
            d.rectangle([Hh(11), hy + 6, Hh(14), hy + 10], fill=(220, 90, 110))
    elif mouth == "chomp":
        d.line([(Hh(9), hy + 4), (Hh(16), hy + 4)], fill=INK)
    # arms and what they hold
    sx, sy = X(2), y - 18 + by
    ax, ay = arm if arm else (X(11), y - 11)
    if prop == "stamp":  # a rubber stamp in hand, held up or slammed down
        d.rectangle([ax - 2, ay - 9, ax + 2, ay - 1], fill=WOOD_HI)
        d.ellipse([ax - 4, ay - 13, ax + 4, ay - 7], fill=WOOD_HI, outline=WOOD_DK)
        d.rectangle([ax - 6, ay, ax + 6, ay + 4], fill=WOOD)
        d.rectangle([ax - 6, ay + 4, ax + 6, ay + 6], fill=RED)
    d.line([(sx, sy), (ax, ay)], fill=body_dk, width=3)
    d.ellipse([ax - 2, ay - 2, ax + 2, ay + 2], fill=PINK)
    if prop == "thumbs_up":
        d.line([(ax, ay - 2), (ax, ay - 6)], fill=PINK, width=2)
    elif prop == "thumbs_down":
        d.line([(ax, ay + 2), (ax, ay + 6)], fill=PINK, width=2)
    elif prop == "pencil":
        d.line([(ax + 1, ay + 1), (ax + 6, ay - 7)], fill=(59, 111, 182), width=2)
        d.point((ax + 1, ay + 2), fill=INK)
    if arm2:
        d.line([(X(-1), sy + 1), arm2], fill=body_dk, width=3)
        d.ellipse([arm2[0] - 2, arm2[1] - 2, arm2[0] + 2, arm2[1] + 2], fill=PINK)
    if lamp:
        d.line([(ax, ay - 1), (ax, ay + 3)], fill=INK)
        d.rectangle([ax - 3, ay + 3, ax + 3, ay + 10], fill=LAMP, outline=INK)
        d.rectangle([ax - 4, ay + 10, ax + 4, ay + 11], fill=INK)


SICK, SICK_DK = (126, 168, 112), (84, 120, 74)
X0 = BX


def frame(**kw) -> Image.Image:
    im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    caesar(draw(im), BX, BY, **kw)
    return im


def sparkle(d, x, y, s=2, c=LAMP):
    d.line([(x - s - 1, y), (x + s + 1, y)], fill=c)
    d.line([(x, y - s - 1), (x, y + s + 1)], fill=c)
    d.point((x, y), fill=PAPER)


def anims() -> dict[str, list[Image.Image]]:
    A = {}
    A["idle"] = [frame(), frame(breathe=1), frame(breathe=1), frame(eyes="closed")]
    A["walk"] = [frame(legs="walk", step=k, breathe=k % 2, tail=k % 2) for k in range(4)]
    A["run"] = [frame(legs="walk", step=k, nod=1, tail=2 * (k % 2), arm=(X0 + 14, BY - 16)) for k in range(4)]
    A["wave"] = [frame(arm=(X0 + 10, BY - 37), mouth="open" if k == 0 else None) if k % 2 == 0 else frame(arm=(X0 + 15, BY - 34))
                 for k in range(4)]
    A["point"] = [frame(arm=(X0 + 17, BY - 22)), frame(arm=(X0 + 18, BY - 23))]
    A["glasses"] = [frame(arm=(X0 + 9, BY - 30)), frame(arm=(X0 + 9, BY - 31), eyes="closed")]
    A["write"] = [frame(arm=(X0 + 13 + (k % 2) * 2, BY - 8 - (k // 2)), prop="pencil", nod=2) for k in range(4)]
    A["lamp"] = [frame(legs="walk", step=k, lamp=True, arm=(X0 + 12, BY - 14)) for k in range(4)]
    A["stamp"] = [frame(arm=(X0 + 9, BY - 36), prop="stamp"), frame(arm=(X0 + 7, BY - 42), prop="stamp", eyes="closed"),
                  frame(arm=(X0 + 16, BY - 6), prop="stamp", nod=2, eyes="wide"), frame(arm=(X0 + 16, BY - 6), prop="stamp", nod=1)]
    A["thumbs_up"] = [frame(arm=(X0 + 12, BY - 28), prop="thumbs_up", laurel=True, eyes="happy"),
                      frame(arm=(X0 + 12, BY - 30), prop="thumbs_up", laurel=True, eyes="happy", breathe=1)]
    A["thumbs_down"] = [frame(arm=(X0 + 12, BY - 15), prop="thumbs_down", laurel=True),
                        frame(arm=(X0 + 12, BY - 13), prop="thumbs_down", laurel=True, breathe=1)]
    A["sniff"] = [frame(nod=3, arm=(X0 + 8, BY - 8)), frame(nod=4, arm=(X0 + 8, BY - 8)), frame(nod=3, arm=(X0 + 8, BY - 8), eyes="closed")]
    eat = []
    for k in range(4):
        im = frame(nod=3 + k % 2, mouth="chomp" if k % 2 else "open", arm=(X0 + 15, BY - 12), arm2=(X0 + 12, BY - 10))
        d = draw(im)
        r = random.Random(k)
        for _ in range(3):
            d.point((X0 + 20 + r.randint(0, 6), BY - 30 + r.randint(0, 8)), fill=(242, 193, 78))
        eat.append(im)
    A["eat"] = eat
    sick = []
    for k in range(4):
        im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
        caesar(draw(im), BX + (1 if k % 2 else -1), BY, body=SICK, body_dk=SICK_DK, eyes="x", mouth="tongue", nod=1,
               arm=(X0 + 6, BY - 20), arm2=(X0 + 2, BY - 18))
        if k >= 2:
            d = draw(im)
            for j in range(3):
                d.ellipse([X0 + 22 + j * 3, BY - 52 + j * 4 - k, X0 + 25 + j * 3, BY - 49 + j * 4 - k], outline=SICK)
        sick.append(im)
    A["sick"] = sick
    flop = []
    for k in range(2):
        im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
        caesar(draw(im), BX, BY - 8, body=SICK, body_dk=SICK_DK, eyes="x", mouth="tongue", legs="dangle" if k else "stand")
        flop.append(im.rotate(90, resample=Image.NEAREST, center=(BX, BY - 20)).transform(
            (FW, FH), Image.AFFINE, (1, 0, -12, 0, 1, -18), resample=Image.NEAREST))
    A["flop"] = flop
    A["revive"] = [frame(nod=4, eyes="closed", arm=(X0 + 9, BY - 30)), frame(nod=2, eyes="closed", arm=(X0 + 9, BY - 30)),
                   frame(eyes="wide", arm=(X0 + 14, BY - 20)), frame()]
    bless = []
    for k in range(4):
        im = frame(wings=k, halo=True, legs="dangle", eyes="happy", arm=(X0 + 12, BY - 26), breathe=k % 2)
        d = draw(im)
        r = random.Random(10 + k)
        for _ in range(3):
            sparkle(d, r.randint(6, 66), r.randint(4, 50), 1 + (k % 2))
        bless.append(im)
    A["bless"] = bless
    A["sleep"] = [frame(eyes="closed", nod=2, breathe=0), frame(eyes="closed", nod=2, breathe=1)]
    A["yawn"] = [frame(mouth="open", eyes="closed", arm=(X0 + 14, BY - 30)), frame(mouth="open", eyes="closed", arm=(X0 + 15, BY - 31))]
    A["startled"] = [frame(eyes="wide", mouth="open", arm=(X0 + 12, BY - 34), arm2=(X0 - 6, BY - 32))]
    A["happy"] = [frame(eyes="happy", tail=2), frame(eyes="happy", tail=0, breathe=1)]
    A["gavin"] = [frame(vest=(22, 22, 26), collar=(16, 16, 18), mouth="open", arm=(X0 + 16, BY - 26)),
                  frame(vest=(22, 22, 26), collar=(16, 16, 18), arm=(X0 + 17, BY - 27))]
    return A


FPS = {"idle": 3, "walk": 10, "run": 14, "wave": 6, "point": 3, "glasses": 3, "write": 8, "lamp": 10, "stamp": 6,
       "thumbs_up": 3, "thumbs_down": 3, "sniff": 5, "eat": 8, "sick": 6, "flop": 3, "revive": 4, "bless": 8, "sleep": 1.5,
       "yawn": 2, "startled": 1, "happy": 3, "gavin": 3}
LOOP = {"idle", "walk", "run", "wave", "write", "lamp", "thumbs_up", "thumbs_down", "sniff", "eat", "sick", "flop", "bless",
        "sleep", "happy", "gavin", "point"}


def sheet(frames: dict[str, list[Image.Image]], name: str):
    cols = max(len(v) for v in frames.values())
    im = Image.new("RGBA", (FW * cols, FH * len(frames)), (0, 0, 0, 0))
    meta = {"w": FW, "h": FH, "feet": [BX, BY], "anims": {}}
    for r, (k, fs) in enumerate(frames.items()):
        for c, f in enumerate(fs):
            im.paste(f, (c * FW, r * FH), f)
        meta["anims"][k] = {"row": r, "frames": len(fs), "fps": FPS.get(k, 6), "loop": k in LOOP}
    (OUT / "sprites").mkdir(parents=True, exist_ok=True)
    im.save(OUT / "sprites" / f"{name}.png", optimize=True)
    (OUT / "sprites" / f"{name}.json").write_text(json.dumps(meta, indent=1))


# =====================================================================================
# PROPS
# =====================================================================================
CHEESE, CHEESE_DK, CHEESE_HOLE = (242, 193, 78), (201, 146, 46), (222, 162, 58)


def cheese(bites=0) -> Image.Image:
    im = Image.new("RGBA", (48, 34), (0, 0, 0, 0))
    d = draw(im)
    d.polygon([(2, 30), (44, 30), (44, 12), (8, 22)], fill=CHEESE_DK)
    d.polygon([(2, 27), (44, 27), (44, 9), (8, 20)], fill=CHEESE, outline=CHEESE_DK)
    d.polygon([(8, 20), (44, 9), (44, 12), (8, 22)], fill=(250, 214, 110))
    for x, y, r in ((16, 23, 2), (28, 20, 3), (38, 23, 2), (34, 15, 2)):
        d.ellipse([x - r, y - r, x + r, y + r], fill=CHEESE_HOLE)
    for k in range(bites):  # bites taken from the thick end
        cx = 44 - k * 11
        d.ellipse([cx - 9, 4, cx + 7, 20], fill=(0, 0, 0, 0))
    if bites >= 3:
        im = Image.new("RGBA", (48, 34), (0, 0, 0, 0))
        d = draw(im)
        r = random.Random(3)
        for _ in range(7):
            x, y = r.randint(6, 40), r.randint(24, 29)
            d.rectangle([x, y, x + 1, y + 1], fill=CHEESE)
    return im


def plate() -> Image.Image:
    im = Image.new("RGBA", (64, 12), (0, 0, 0, 0))
    d = draw(im)
    d.ellipse([0, 2, 63, 11], fill=(150, 156, 160))
    d.ellipse([0, 0, 63, 9], fill=(236, 236, 230), outline=(180, 184, 186))
    d.ellipse([10, 2, 53, 7], outline=(210, 212, 210))
    return im


def ghost(k) -> Image.Image:
    im = Image.new("RGBA", (40, 44), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = (236, 240, 255, 170)
    d.ellipse([6, 2, 34, 30], fill=c)
    d.rectangle([6, 16, 34, 36], fill=c)
    for i in range(4):
        x = 6 + i * 7
        d.polygon([(x, 36), (x + 7, 36), (x + 3 + (1 if k else -1), 42)], fill=c)
    d.ellipse([6, -4, 14, 6], fill=c)
    d.ellipse([12, 11, 17, 17], fill=(42, 38, 34, 200))
    d.ellipse([23, 11, 28, 17], fill=(42, 38, 34, 200))
    d.ellipse([18, 21, 23, 26], fill=(42, 38, 34, 160))
    return im


def cloud() -> Image.Image:
    im = Image.new("RGBA", (72, 28), (0, 0, 0, 0))
    d = draw(im)
    for x, y, r in ((14, 18, 10), (30, 12, 13), (48, 14, 12), (60, 19, 9)):
        d.ellipse([x - r, y - r + 2, x + r, y + r + 2], fill=(200, 206, 220))
    for x, y, r in ((14, 16, 10), (30, 10, 13), (48, 12, 12), (60, 17, 9)):
        d.ellipse([x - r, y - r, x + r, y + r], fill=(246, 246, 250))
    return im


def stamp_tool() -> Image.Image:
    im = Image.new("RGBA", (76, 84), (0, 0, 0, 0))
    d = draw(im)
    sx, y = 38, 72
    d.rectangle([sx - 34, y - 16 + 22 - 10, sx + 34, y + 22 - 10], fill=(100, 30, 28))
    d.rectangle([sx - 30, y - 20 - 10, sx + 30, y + 6 - 10], fill=WOOD_HI)
    d.rectangle([sx - 8, y - 60 - 10, sx + 8, y - 20 - 10], fill=WOOD)
    d.ellipse([sx - 14, y - 76 - 6, sx + 14, y - 52 - 6], fill=WOOD_HI)
    return im


def props():
    (OUT / "sprites").mkdir(parents=True, exist_ok=True)
    for k in range(4):
        cheese(k).save(OUT / "sprites" / f"cheese{k}.png")
    plate().save(OUT / "sprites" / "plate.png")
    for k in range(2):
        ghost(k).save(OUT / "sprites" / f"ghost{k}.png")
    cloud().save(OUT / "sprites" / "cloud.png")
    stamp_tool().save(OUT / "sprites" / "stamp_tool.png")
    stamps = {"false_stale_98": ("FALSE", "STALE · 98% SURE", RED, 32), "invented": ("FALSE", "INVENTED", RED, 24),
              "stale": ("FALSE", "STALE", RED, 24), "premature": ("FALSE", "PREMATURE", RED, 24), "true": ("TRUE", "SEALED", GREEN, 24), "false": ("FALSE", "A LIE", RED, 24)}
    for name, (w, s, c, sc) in stamps.items():
        stamp_img(w, s, c, sc).save(OUT / "sprites" / f"stamp_{name}.png")
    for who in ("salesman", "gavin", "host"):
        im = Image.new("RGBA", (48, 64), (0, 0, 0, 0))
        art.person(draw(im), 22, 62, who)
        im.save(OUT / "sprites" / f"person_{who}.png")


# =====================================================================================
# SCENES: the film's shots as frame atlases, captions and tabs off
# =====================================================================================
story.caption = lambda *a, **k: None
story.tab = lambda *a, **k: None
SCENE_FPS = 8
SCENES = {  # name: (shot, from, to) in the shot's own time
    "booth": (story.s03_applicant, 0.0, 7.0),
    "input": (story.s04_input, 0.2, 6.5),
    "linker": (story.s05_linker, 0.2, 7.0),
    "reader": (story.s06_reader, 0.2, 7.0),
    "attributor": (story.s07_attributor, 0.2, 10.0),
    "kb": (story.s08_kb, 0.2, 3.6),
    "board": (story.s09c_board, 0.0, 5.8),
    "same": (story.s09d_same, 0.0, 4.2),
    "polygraph": (story.s10a_polygraph, 0.0, 5.2),
    "writer": (story.s11_writer, 0.0, 2.6),
}


def atlas(name, fn, a, b):
    n = int((b - a) * SCENE_FPS) + 1
    cols = 6
    rows = math.ceil(n / cols)
    big = Image.new("RGB", (art.W * cols, art.H * rows), NIGHT)
    for i in range(n):
        f = fn(a + i / SCENE_FPS).convert("RGB")
        big.paste(f, ((i % cols) * art.W, (i // cols) * art.H))
    q = big.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    (OUT / "scenes").mkdir(parents=True, exist_ok=True)
    q.save(OUT / "scenes" / f"{name}.png", optimize=True)
    return {"frames": n, "cols": cols, "fps": SCENE_FPS, "w": art.W, "h": art.H}


def backgrounds():
    (OUT / "scenes").mkdir(parents=True, exist_ok=True)
    # the corkboard with every document pinned, for the date pin
    img = Image.new("RGB", (art.W, art.H), NIGHT)
    d = draw(img)
    story.board(d)
    for i, (day, v, s, rid) in enumerate(story.DOCS):
        x, y = story.pos(i)
        story.doc_card(d, x, y, s, i)
    img.save(OUT / "scenes" / "board_full.png")
    # the slip before the stamp
    story.s10b_stamp(0.0).convert("RGB").save(OUT / "scenes" / "stamp_desk.png")
    # the booth, empty, and the archive door, for the page's ends
    art.booth_base(True).convert("RGB").save(OUT / "scenes" / "booth_empty.png")
    # the tasting table of the cheese game: the booth's wall, a long table
    img = Image.new("RGB", (art.W, art.H), WALL)
    d = draw(img)
    for x in range(0, art.W, 60):
        d.line([(x, 0), (x, 200)], fill=WALL_DK)
        d.line([(x + 1, 0), (x + 1, 200)], fill=WALL_LT)
    d.rectangle([0, 196, art.W, 202], fill=WOOD_HI)
    d.rectangle([0, 202, art.W, art.H], fill=WOOD)
    for y in (216, 232, 248):
        d.line([(0, y), (art.W, y)], fill=WOOD_DK)
    d.rectangle([150, 22, 330, 50], fill=(47, 59, 51), outline=(30, 38, 33))
    text(d, (240, 27), "THE TASTING ROOM", "signb", 8, PAPER, "mt")
    text(d, (240, 38), "ONE CHEESE IS A LIE", "sign", 8, art.LIME, "mt")
    for x0 in (40, 380):  # two lamps on the wall
        d.line([(x0 + 30, 0), (x0 + 30, 34)], fill=(40, 42, 40), width=2)
        d.polygon([(x0 + 20, 34), (x0 + 40, 34), (x0 + 36, 44), (x0 + 24, 44)], fill=(62, 96, 70))
    img.save(OUT / "scenes" / "tasting.png")


# =====================================================================================
# SOUNDS: the film's, plus the game's own
# =====================================================================================
def chomp():
    x = np.zeros(int(0.5 * sound.SR))
    for k in range(3):
        c = sound._hp(sound._noise(0.07), 3) * sound._dec(0.07, 60) * 0.7 + sound.thud()[: int(0.07 * sound.SR)] * 0.25
        i = int(k * 0.15 * sound.SR)
        x[i: i + len(c)] += c[: len(x) - i]
    return x


def bleh():
    s = 0.9
    t = sound._t(s)
    pitch = 220 * np.exp(-1.1 * t) + 70 + 8 * np.sin(2 * math.pi * 9 * t)
    saw = 2 * ((np.cumsum(pitch) / sound.SR) % 1.0) - 1
    return sound._fade(sound._lp(saw, 10) * 0.5 * np.minimum(1, t * 20) * np.exp(-1.2 * t), 0.01, 0.15)


def harp():
    notes = [523.25, 659.25, 783.99, 1046.5, 1318.5]
    x = np.zeros(int(1.8 * sound.SR))
    for k, f in enumerate(notes):
        s = 1.2
        t = sound._t(s)
        n = (np.sin(2 * math.pi * f * t) + 0.3 * np.sin(4 * math.pi * f * t)) * np.exp(-3 * t) * 0.25
        i = int(k * 0.09 * sound.SR)
        x[i: i + len(n)] += n[: len(x) - i]
    return x


def poof():
    s = 0.5
    t = sound._t(s)
    return sound._fade(sound._lp(sound._noise(s), 6) * np.sin(math.pi * t / s) * 0.4)


def sounds():
    (OUT / "sounds").mkdir(parents=True, exist_ok=True)
    fx = {k: sound.EFFECTS[k] for k in ("thud", "seal", "paper", "pencil", "drawer", "step", "pin", "tick", "key", "bell",
                                       "blip", "page", "shutter", "mumble")}
    fx.update(chomp=chomp, bleh=bleh, harp=harp, poof=poof)
    for name, fn in fx.items():
        x = fn()
        x = x / (np.max(np.abs(x)) or 1) * 0.8
        data = (x * 32767).astype("<i2")
        with wave.open(str(OUT / "sounds" / f"{name}.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sound.SR)
            w.writeframes(data.tobytes())


def fonts():
    (OUT / "fonts").mkdir(parents=True, exist_ok=True)
    for f in (ROOT / "video" / "fonts").iterdir():
        if f.suffix in (".ttf", ".txt") and f.name != "Figtree.ttf":
            shutil.copy(f, OUT / "fonts" / f.name.replace("[wght]", ""))


if __name__ == "__main__":
    only = set(sys.argv[1:])
    if not only or "caesar" in only:
        sheet(anims(), "caesar")
        props()
        print("caesar + props")
    if not only or "scenes" in only:
        meta = {name: atlas(name, *spec) for name, spec in SCENES.items()}
        (OUT / "scenes" / "scenes.json").write_text(json.dumps(meta, indent=1))
        backgrounds()
        print("scenes", {k: v["frames"] for k, v in meta.items()})
    if not only or "sounds" in only:
        sounds()
        print("sounds")
    if not only or "fonts" in only:
        fonts()
        print("fonts")
