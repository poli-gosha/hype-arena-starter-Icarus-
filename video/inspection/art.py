"""The pixel art of "The Inspection": palette, fonts, paper, stamps, the booth and the cast.

Everything is drawn in code on a 480x270 canvas with Pillow's aliased shapes, so it reads as
pixel art once scaled x4 with nearest-neighbour. No asset is downloaded but the open fonts.
"""
from __future__ import annotations

import math
import random
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 480, 270
FONTS = Path(__file__).resolve().parent.parent / "fonts"

# ---- palette (docs/PITCH_PAPERS.md, Part 1) ----------------------------------------------
NIGHT = (20, 21, 24)
WALL, WALL_LT, WALL_DK = (43, 45, 42), (52, 55, 51), (33, 35, 32)
WOOD, WOOD_HI, WOOD_DK = (74, 63, 53), (94, 80, 67), (58, 49, 41)
PAPER, PAPER_SH, PAPER_DK = (232, 224, 201), (201, 191, 163), (168, 158, 132)
INK, INK_LT = (42, 38, 34), (96, 88, 78)
ARCH, ARCH_DK, ARCH_LT = (76, 90, 99), (52, 63, 70), (98, 114, 124)
RED, RED_DK = (184, 50, 47), (130, 34, 32)
GREEN, GREEN_DK = (79, 138, 60), (54, 98, 41)
AMBER = (201, 147, 47)
LIME = (215, 241, 59)
LAMP = (242, 213, 138)
BLUE_PEN = (59, 111, 182)
CORK, CORK_DK, CORK_LT = (139, 107, 69), (114, 88, 56), (160, 125, 82)
SKY_TOP, SKY_LOW = (29, 35, 64), (74, 53, 80)
CITY = (24, 26, 36)
# the cast
MOUSE, MOUSE_DK, MOUSE_LT = (138, 143, 150), (92, 97, 104), (164, 168, 174)
PINK = (217, 154, 160)
VISOR, VISOR_LT = (62, 125, 74), (84, 156, 96)
VEST = (107, 78, 58)
SKIN, SKIN_DK = (224, 180, 143), (190, 146, 110)
SUIT, SUIT_LT = (46, 58, 92), (74, 90, 134)
HAIR, SILVER = (58, 42, 32), (190, 192, 196)
JACKET = (30, 30, 34)
TEAL = (52, 120, 128)


@lru_cache(maxsize=None)
def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    files = {"sign": "Silkscreen-Regular.ttf", "signb": "Silkscreen-Bold.ttf", "type": "VT323-Regular.ttf",
             "cap": "PixelifySans[wght].ttf"}
    if name == "type" and size == 16:
        size = 17  # VT323 renders cleanly at 17 px; 16 smears a few glyphs
    return ImageFont.truetype(str(FONTS / files[name]), size)


def draw(img: Image.Image) -> ImageDraw.ImageDraw:
    d = ImageDraw.Draw(img)
    d.fontmode = "1"  # no anti-aliasing: pixel text
    return d


def text(d, xy, s, f="type", size=16, fill=INK, anchor="la"):
    d.text((round(xy[0]), round(xy[1])), s, font=font(f, size), fill=fill, anchor=anchor)


def text_w(s, f="type", size=16) -> int:
    b = font(f, size).getbbox(s)
    return b[2] - b[0]


def ease(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease_out(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def lerp(a, b, x):
    return a + (b - a) * x


def stepped(t: float, fps: int = 12) -> float:
    """Time quantised to the pixel-game frame rate, for characters and props."""
    return math.floor(t * fps) / fps


def darken(img: Image.Image, k: float) -> Image.Image:
    """k=0 unchanged, k=1 black."""
    if k <= 0:
        return img
    return Image.blend(img, Image.new("RGB", img.size, NIGHT), min(1.0, k))


# ---- paper, stamps, seals ----------------------------------------------------------------
def paper(d, box, fill=PAPER, shade=PAPER_SH, shadow=True):
    x0, y0, x1, y1 = [round(v) for v in box]
    if shadow:
        d.rectangle([x0 + 3, y0 + 3, x1 + 3, y1 + 3], fill=(0, 0, 0))
    d.rectangle([x0, y0, x1, y1], fill=fill)
    d.line([(x0, y1), (x1, y1)], fill=shade)
    d.line([(x1, y0), (x1, y1)], fill=shade)


def lines(d, x, y, w, n, gap=6, color=PAPER_SH):
    for i in range(n):
        d.line([(x, y + i * gap), (x + w, y + i * gap)], fill=color)


def scribble(d, x, y, w, seed, color=INK_LT, rows=2, gap=4):
    """Unreadable small handwriting: the texture of a document's text."""
    r = random.Random(seed)
    for k in range(rows):
        cx, end = x, x + w * (0.6 + 0.4 * r.random() if k == rows - 1 else 1)
        while cx < end:
            seg = r.randint(3, 9)
            d.line([(cx, y + k * gap), (min(end, cx + seg), y + k * gap)], fill=color)
            cx += seg + 2


def stamp_img(word: str, sub: str = "", color=RED, scale: int = 16) -> Image.Image:
    """An inked rubber-stamp imprint (RGBA), double border, worn edges."""
    ss = 8 if scale < 24 else 16
    f1, f2 = font("signb", scale), font("sign", ss)
    w = max(text_w(word, "signb", scale), text_w(sub, "sign", ss) if sub else 0) + 16
    h = scale + (ss + 6 if sub else 6) + 8
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=color + (255,), width=2)
    d.rectangle([3, 3, w - 4, h - 4], outline=color + (255,))
    d.text((w // 2, 6), word, font=f1, fill=color + (255,), anchor="mt")
    if sub:
        d.text((w // 2, 8 + scale + 3), sub, font=f2, fill=color + (255,), anchor="mt")
    r = random.Random(word + sub)
    px = im.load()
    for _ in range(w * h // 16):  # worn ink
        x, y = r.randrange(w), r.randrange(h)
        if px[x, y][3]:
            px[x, y] = (0, 0, 0, 0)
    return im


def paste_rot(img: Image.Image, sprite: Image.Image, center, angle=0.0, alpha=1.0):
    s = sprite.rotate(angle, resample=Image.NEAREST, expand=True) if angle else sprite
    if alpha < 1:
        a = s.getchannel("A").point(lambda v: int(v * alpha))
        s = s.copy()
        s.putalpha(a)
    img.paste(s, (round(center[0] - s.width / 2), round(center[1] - s.height / 2)), s)


def seal(d, c, r=6, color=GREEN, seed=0):
    """A wax seal: a lumpy disc with a darker rim and a pressed mark."""
    rr = random.Random(seed)
    pts = [(c[0] + (r + rr.choice((-1, 0, 0, 1))) * math.cos(a), c[1] + (r + rr.choice((-1, 0, 0, 1))) * math.sin(a))
           for a in [i * math.pi / 8 for i in range(16)]]
    dark = GREEN_DK if color == GREEN else RED_DK if color == RED else tuple(int(v * 0.7) for v in color)
    d.polygon(pts, fill=dark)
    d.ellipse([c[0] - r + 2, c[1] - r + 2, c[0] + r - 2, c[1] + r - 2], fill=color)
    d.ellipse([c[0] - 2, c[1] - 2, c[0] + 2, c[1] + 2], outline=dark)


def check(d, x, y, color=GREEN, s=1):
    d.line([(x, y + 3 * s), (x + 2 * s, y + 5 * s), (x + 7 * s, y)], fill=color, width=max(1, s + 1))


def arrow(d, x0, y, x1, color=INK):
    d.line([(x0, y), (x1, y)], fill=color)
    d.line([(x1 - 3, y - 3), (x1, y), (x1 - 3, y + 3)], fill=color)


# ---- screen furniture: caption bar, step tab ---------------------------------------------------
def caption(img: Image.Image, s: str, t: float, speed: float = 55.0, top: bool = False):
    """The caption bar, typed in at `speed` characters a second from t=0."""
    if t < 0 or not s:
        return
    shown = s[: int(t * speed) + 1]
    rows = wrap_px(s, W - 24, "cap", 13)
    h = 16 * len(rows) + 10
    y0 = 6 if top else H - h - 4
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = draw(over)
    od.rectangle([0, y0, W, y0 + h], fill=NIGHT + (225,))
    img.paste(over, (0, 0), over)
    d = draw(img)
    used = 0
    for i, row in enumerate(rows):
        part = shown[used: used + len(row)]
        used += len(row) + 1
        if part:
            x = (W - text_w(row, "cap", 13)) // 2
            text(d, (x, y0 + 4 + 16 * i), part, "cap", 13, PAPER)


def wrap_px(s: str, width: int, f="cap", size=13) -> list[str]:
    """Words into rows no wider than `width` pixels."""
    out, cur = [], ""
    for w in s.split(" "):
        cand = f"{cur} {w}" if cur else w
        if cur and text_w(cand, f, size) > width:
            out.append(cur)
            cur = w
        else:
            cur = cand
    return out + ([cur] if cur else [])


def wrap(s: str, n: int) -> list[str]:
    out, cur = [], ""
    for w in s.split(" "):
        if cur and len(cur) + 1 + len(w) > n:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    return out + ([cur] if cur else [])


def tab(img: Image.Image, step: int, title: str, module: str, t: float):
    """The step tab that slides down at the top left: STEP 2 · WHO / linker."""
    if t < 0:
        return
    y = round(lerp(-34, 6, ease_out(t / 0.35)))
    d = draw(img)
    w = max(text_w(f"STEP {step} · {title}", "signb", 8), text_w(module, "type", 16)) + 16
    d.rectangle([7, y + 2, 7 + w + 2, y + 32], fill=(0, 0, 0))
    d.rectangle([6, y, 6 + w, y + 29], fill=PAPER)
    d.rectangle([6, y, 6 + 3, y + 29], fill=LIME)
    text(d, (14, y + 5), f"STEP {step} · {title}", "signb", 8, INK)
    text(d, (14, y + 12), module, "type", 16, INK_LT)


# ---- the cast ------------------------------------------------------------------------------
def mouse(d, x, y, t=0.0, arm=None, nod=0.0, walk=None, lamp=False, blink=True, facing=-1, arm2=None):
    """The Clerk, side view. (x, y): the seat (bottom of the body). facing -1: left."""
    f = facing
    X = lambda dx: x + f * -dx  # noqa: E731  (dx measured facing left)
    st = stepped(t)
    by = 1 if (walk is None and int(st * 1.5) % 2) else 0  # breathing
    # tail
    tail = [(X(8), y - 3), (X(15), y - 1), (X(20), y - 5), (X(21), y - 11), (X(18), y - 14)]
    d.line(tail, fill=PINK, width=2)
    # legs when walking
    if walk is not None:
        ph = int(walk * 8) % 2
        for k, dx in enumerate((-3, 3)):
            lift = 2 if (k == ph) else 0
            d.rectangle([min(X(dx - 1), X(dx + 2)), y - 1 - lift, max(X(dx - 1), X(dx + 2)), y + 5 - lift], fill=MOUSE_DK)
            d.rectangle([min(X(dx - 3), X(dx + 2)), y + 4 - lift, max(X(dx - 3), X(dx + 2)), y + 6 - lift], fill=PINK)
    # body and vest
    d.ellipse([min(X(-9), X(9)), y - 24 + by, max(X(-9), X(9)), y], fill=MOUSE, outline=MOUSE_DK)
    d.polygon([(X(7), y - 15 + by), (X(1), y - 20 + by), (X(-7), y - 17 + by), (X(-8), y - 6), (X(5), y - 3)], fill=VEST)
    d.line([(X(1), y - 19 + by), (X(2), y - 4)], fill=(80, 58, 43))
    # head
    hx, hy = X(3), y - 31 + round(nod) + by
    HX = lambda dx: hx + f * -dx  # noqa: E731
    d.ellipse([min(HX(-2), HX(14)), hy - 18, max(HX(-2), HX(14)), hy - 6], fill=MOUSE_DK)  # far ear
    d.ellipse([min(HX(-9), HX(9)), hy - 8, max(HX(-9), HX(9)), hy + 7], fill=MOUSE, outline=MOUSE_DK)
    d.ellipse([min(HX(5), HX(17)), hy - 3, max(HX(5), HX(17)), hy + 5], fill=MOUSE, outline=MOUSE_DK)  # snout
    d.rectangle([min(HX(17), HX(19)), hy - 1, max(HX(17), HX(19)), hy + 1], fill=PINK)  # nose
    d.ellipse([min(HX(-8), HX(4)), hy - 19, max(HX(-8), HX(4)), hy - 7], fill=MOUSE, outline=MOUSE_DK)  # near ear
    d.ellipse([min(HX(-5), HX(1)), hy - 16, max(HX(-5), HX(1)), hy - 10], fill=PINK)
    # visor: band over the brow, brim forward
    d.polygon([(HX(8), hy - 6), (HX(-7), hy - 8), (HX(-8), hy - 5), (HX(7), hy - 3)], fill=VISOR)
    d.polygon([(HX(7), hy - 5), (HX(18), hy - 3), (HX(17), hy - 1), (HX(7), hy - 2)], fill=VISOR_LT)
    # eye behind round glasses
    closed = blink and (st % 3.4) < 0.09
    if closed:
        d.line([(HX(8), hy), (HX(6), hy)], fill=INK)
    else:
        d.rectangle([min(HX(8), HX(7)), hy - 1, max(HX(8), HX(7)), hy], fill=INK)
    d.ellipse([min(HX(11), HX(4)), hy - 3, max(HX(11), HX(4)), hy + 3], outline=INK)
    d.point((HX(10), hy - 2), fill=PAPER)
    for k, (a, b) in enumerate(((2, 1), (3, 5))):
        d.line([(HX(15), hy + a), (HX(23), hy + b - k)], fill=MOUSE_DK)
    # arms
    sx, sy = X(2), y - 18 + by
    ax, ay = arm if arm else (X(11), y - 11)
    d.line([(sx, sy), (ax, ay)], fill=MOUSE_DK, width=3)
    d.ellipse([ax - 2, ay - 2, ax + 2, ay + 2], fill=PINK)
    if arm2:
        d.line([(X(-1), sy + 1), arm2], fill=MOUSE_DK, width=3)
        d.ellipse([arm2[0] - 2, arm2[1] - 2, arm2[0] + 2, arm2[1] + 2], fill=PINK)
    if lamp:
        lx, ly = ax, ay
        d.line([(lx, ly - 1), (lx, ly + 3)], fill=INK)
        d.rectangle([lx - 3, ly + 3, lx + 3, ly + 10], fill=LAMP, outline=INK)
        d.rectangle([lx - 4, ly + 10, lx + 4, ly + 11], fill=INK)


def stool(d, x, y):
    d.rectangle([x - 9, y, x + 9, y + 3], fill=WOOD_HI)
    for dx in (-7, 6):
        d.line([(x + dx, y + 3), (x + dx + (-2 if dx < 0 else 2), 232)], fill=WOOD_DK, width=2)
    d.line([(x - 8, y + 20), (x + 8, y + 20)], fill=WOOD_DK)


def person(d, x, y, kind: str, t=0.0, lean=0, talk=False, arm=None):
    """An applicant behind the window, facing right. (x, y): the bottom of the torso.
    kind: salesman, gavin, host."""
    x += lean
    st = stepped(t)
    mouth_open = talk and int(st * 6) % 2
    coat = {"salesman": SUIT, "gavin": JACKET, "host": TEAL}[kind]
    coat_lt = {"salesman": SUIT_LT, "gavin": (56, 56, 62), "host": (72, 150, 158)}[kind]
    d.polygon([(x - 17, y), (x + 17, y), (x + 13, y - 30), (x - 13, y - 30)], fill=coat)
    d.line([(x + 12, y - 28), (x + 15, y - 2)], fill=coat_lt)
    if kind == "salesman":
        d.polygon([(x - 4, y - 30), (x + 4, y - 30), (x, y - 18)], fill=PAPER)
        d.polygon([(x - 1, y - 27), (x + 1, y - 27), (x + 2, y - 14), (x, y - 11), (x - 2, y - 14)], fill=RED)
    elif kind == "gavin":
        d.rectangle([x - 5, y - 31, x + 5, y - 26], fill=(16, 16, 18))  # turtleneck
    else:
        d.line([(x - 6, y - 30), (x, y - 14), (x + 6, y - 30)], fill=AMBER)  # lanyard
        d.rectangle([x - 3, y - 15, x + 3, y - 9], fill=PAPER)
    # head
    hx, hy = x + 2, y - 42
    d.rectangle([hx - 3, y - 33, hx + 3, y - 29], fill=SKIN_DK)
    d.ellipse([hx - 10, hy - 12, hx + 10, hy + 11], fill=SKIN)
    d.ellipse([hx + 7, hy - 2, hx + 11, hy + 3], fill=SKIN)  # nose
    if kind == "salesman":
        d.polygon([(hx - 11, hy - 2), (hx - 9, hy - 13), (hx + 2, hy - 15), (hx + 11, hy - 10), (hx + 8, hy - 8), (hx - 6, hy - 8)], fill=HAIR)
        d.line([(hx - 4, hy - 12), (hx + 5, hy - 12)], fill=(110, 90, 70))  # gel shine
    elif kind == "gavin":
        d.polygon([(hx - 11, hy + 1), (hx - 10, hy - 11), (hx, hy - 15), (hx + 9, hy - 12), (hx + 6, hy - 9), (hx - 5, hy - 9), (hx - 7, hy + 1)], fill=SILVER)
        d.rectangle([hx + 2, hy - 3, hx + 9, hy - 1], outline=INK)  # glasses
    else:
        d.polygon([(hx - 11, hy + 4), (hx - 10, hy - 11), (hx + 1, hy - 15), (hx + 10, hy - 10), (hx - 4, hy - 8), (hx - 6, hy + 2)], fill=(120, 72, 40))
        d.ellipse([hx - 17, hy - 6, hx - 9, hy + 4], fill=(120, 72, 40))  # ponytail
        d.line([(hx - 2, hy + 1), (hx + 6, hy + 7)], fill=INK)  # headset mic
    d.rectangle([hx + 5, hy - 2, hx + 6, hy - 1], fill=INK)  # eye
    if mouth_open:
        d.rectangle([hx + 2, hy + 5, hx + 8, hy + 8], fill=INK)
        d.line([(hx + 3, hy + 5), (hx + 7, hy + 5)], fill=PAPER)
    else:
        d.line([(hx + 1, hy + 5), (hx + 4, hy + 7), (hx + 8, hy + 6)], fill=INK)  # grin
        d.line([(hx + 3, hy + 6), (hx + 7, hy + 6)], fill=PAPER)
    if arm:
        d.line([(x + 10, y - 24), arm], fill=coat, width=4)
        d.ellipse([arm[0] - 3, arm[1] - 3, arm[0] + 3, arm[1] + 3], fill=SKIN)


# ---- the booth (side view) -----------------------------------------------------------------------
WINDOW = (28, 66, 146, 150)  # the glass inside the frame
DESK_TOP = 170
MONITOR = (288, 138, 322, 166)  # the CRT's outer box
SCREEN = (292, 142, 318, 160)  # its glass


@lru_cache(maxsize=4)
def booth_base(lit: bool = True) -> Image.Image:
    img = Image.new("RGB", (W, H), WALL)
    d = draw(img)
    for x in range(0, W, 60):  # wall panels
        d.line([(x, 0), (x, 226)], fill=WALL_DK)
        d.line([(x + 1, 0), (x + 1, 226)], fill=WALL_LT)
    d.rectangle([0, 226, W, 232], fill=WOOD_DK)
    d.rectangle([0, 232, W, H], fill=(46, 40, 34))
    for y in (240, 252, 264):
        d.line([(0, y), (W, y)], fill=(38, 33, 28))
    # window frame and outside
    x0, y0, x1, y1 = WINDOW
    d.rectangle([x0 - 5, y0 - 5, x1 + 5, y1 + 2], fill=WOOD)
    for i in range(y1 - y0):
        c = tuple(round(lerp(a, b, i / (y1 - y0))) for a, b in zip(SKY_TOP, SKY_LOW))
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c)
    r = random.Random(4)
    cx = x0
    while cx < x1:  # the city at dusk
        w, h = r.randint(8, 18), r.randint(14, 40)
        d.rectangle([cx, y1 - h, min(x1, cx + w), y1], fill=CITY)
        for _ in range(2):
            if r.random() < 0.7:
                wx, wy = r.randint(cx + 2, max(cx + 2, cx + w - 3)), r.randint(y1 - h + 3, y1 - 6)
                if wx < x1 - 2:
                    d.rectangle([wx, wy, wx + 1, wy + 1], fill=LAMP)
        cx += w + 1
    d.line([(x1 - 22, y0 + 18), (x1 - 22, y1)], fill=(60, 60, 64), width=2)  # a street lamp
    d.ellipse([x1 - 27, y0 + 13, x1 - 17, y0 + 21], fill=(180, 160, 110))
    # ledge with the slot
    d.rectangle([18, 150, 162, 158], fill=WOOD_HI)
    d.line([(18, 158), (162, 158)], fill=WOOD_DK)
    d.line([(40, 150), (140, 150)], fill=NIGHT)
    # the sign
    d.rectangle([20, 30, 154, 56], fill=(47, 59, 51))
    d.rectangle([20, 30, 154, 56], outline=(30, 38, 33))
    text(d, (87, 36), "MINISTRY OF STATEMENTS", "signb", 8, PAPER, "mt")
    text(d, (87, 46), "POLYGRAPH DESK", "sign", 8, LIME, "mt")
    # notice board
    d.rectangle([386, 56, 468, 128], fill=CORK)
    d.rectangle([386, 56, 468, 128], outline=WOOD_DK)
    paper(d, (392, 62, 462, 122), shadow=False)
    text(d, (427, 66), "NOTICE", "signb", 8, RED, "mt")
    for i, s in enumerate(["NO GUESSING.", "NO LLMS.", "NO INTERNET.", "30 MINUTES."]):
        text(d, (397, 79 + i * 10), s, "sign", 8, INK)
    d.ellipse([425, 59, 429, 63], fill=RED)  # pin
    # calendar
    paper(d, (392, 140, 424, 172), shadow=False)
    d.rectangle([392, 140, 424, 148], fill=RED)
    text(d, (408, 141), "OCT", "sign", 8, PAPER, "mt")
    text(d, (408, 149), "29", "type", 16, INK, "mt")
    text(d, (408, 162), "2026", "sign", 8, INK_LT, "mt")
    # archive door
    d.rectangle([432, 134, 476, 226], fill=WOOD_DK)
    d.rectangle([436, 138, 472, 226], fill=(26, 28, 30))
    d.rectangle([430, 122, 478, 132], fill=ARCH)
    text(d, (454, 124), "ARCHIVE", "sign", 8, PAPER, "mt")
    # desk (side view) and what stands on it
    d.rectangle([206, DESK_TOP, 374, DESK_TOP + 6], fill=WOOD_HI)
    d.rectangle([210, DESK_TOP + 6, 370, 228], fill=WOOD)
    d.line([(210, 200), (370, 200)], fill=WOOD_DK)
    d.rectangle([280, 186, 300, 189], fill=WOOD_DK)  # drawer handle
    # typewriter
    d.polygon([(214, 170), (250, 170), (246, 154), (218, 154)], fill=(54, 58, 62))
    d.rectangle([220, 148, 244, 154], fill=(40, 42, 46))
    paper(d, (224, 136, 240, 150), shadow=False)
    # polygraph box
    d.rectangle([254, 152, 284, 170], fill=(88, 72, 56))
    d.pieslice([258, 146, 280, 168], 180, 360, fill=PAPER)
    d.line([(269, 157), (276, 151)], fill=RED)
    # monitor (CRT)
    x0, y0, x1, y1 = MONITOR
    d.rectangle([x0, y0, x1, y1], fill=(70, 72, 68))
    d.rectangle([x0 + 4, y1, x1 - 4, y1 + 4], fill=(56, 58, 54))
    d.rectangle(SCREEN, fill=(26, 34, 30))
    # outbox
    d.rectangle([330, 162, 352, 170], fill=WOOD_DK)
    paper(d, (333, 159, 349, 163), shadow=False)
    text(d, (341, 172), "OUT", "sign", 8, PAPER_DK, "mt")
    # lamp
    d.rectangle([356, 166, 370, 170], fill=(40, 42, 40))
    d.line([(363, 166), (356, 128)], fill=(40, 42, 40), width=2)
    d.line([(356, 128), (336, 124)], fill=(40, 42, 40), width=2)
    d.polygon([(326, 120), (342, 118), (346, 130), (322, 132)], fill=(62, 96, 70))
    if lit:
        over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(over)
        od.polygon([(324, 131), (345, 129), (372, 170), (212, 170)], fill=LAMP + (38,))
        img.paste(over, (0, 0), over)
        d = draw(img)
        d.line([(324, 132), (345, 130)], fill=LAMP)
    return img


def shutter(d, open_: float):
    """The window's metal shutter, rolled up by `open_` (0 closed, 1 open)."""
    x0, y0, x1, y1 = WINDOW
    bottom = round(y0 + (1 - open_) * (y1 - y0))
    if bottom > y0:
        d.rectangle([x0, y0, x1, bottom], fill=ARCH_DK)
        for y in range(y0 + 3, bottom, 5):
            d.line([(x0, y), (x1, y)], fill=ARCH)
        d.line([(x0, bottom), (x1, bottom)], fill=ARCH_LT)
    d.rectangle([x0 - 5, y0 - 8, x1 + 5, y0 - 1], fill=ARCH_DK)  # the roll box


def in_window(img: Image.Image, fn):
    """Draw `fn(d)` clipped to the window glass (an applicant outside)."""
    layer = img.copy()
    fn(draw(layer))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rectangle(WINDOW, fill=255)
    img.paste(layer, (0, 0), mask)


# ---- the desk (top-down close-ups) ------------------------------------------------------------
@lru_cache(maxsize=2)
def desk_base(dim: bool = False) -> Image.Image:
    img = Image.new("RGB", (W, H), WOOD)
    d = draw(img)
    r = random.Random(7)
    for y in range(0, H, 3):
        if r.random() < 0.55:
            x = r.randint(-40, W)
            d.line([(x, y), (x + r.randint(40, 220), y)], fill=WOOD_DK if r.random() < 0.6 else WOOD_HI)
    for y in (62, 146, 220):
        d.line([(0, y), (W, y)], fill=(66, 56, 47))  # plank seams
    # vignette: the lamp lights the middle
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    for k in range(6):
        a = 22 + k * 12
        od.rectangle([0, 0, W, H], outline=(0, 0, 0, a), width=6 + k * 2)
    img.paste(over, (0, 0), over)
    return darken(img, 0.35) if dim else img


# ---- the slip: today's statement -------------------------------------------------------------
STATEMENT = "The Hooly Pixel 10 costs €799."
STATEMENT_DATE = "05 OCT 2026"


def slip(d, x, y, text_=STATEMENT, date=STATEMENT_DATE, w=236, who=None, h=46):
    """The statement slip, top-left at (x, y). Returns the text's top-left for marks."""
    paper(d, (x, y, x + w, y + h))
    text(d, (x + 6, y + 4), "STATEMENT", "sign", 8, INK_LT)
    d.rectangle([x + w - 74, y + 3, x + w - 6, y + 13], outline=(110, 70, 120))
    text(d, (x + w - 40, y + 5), date, "sign", 8, (110, 70, 120), "mt")
    tx, ty = x + 8, y + 18
    rows = wrap(text_, max(10, (w - 16) // 7))
    for i, row in enumerate(rows):
        text(d, (tx, ty + i * 13), row, "type", 16, INK)
    if who:
        text(d, (x + 6, y + 36), who, "sign", 8, INK_LT)
    return tx, ty


def span_x(s: str, start: int, end: int, x0: float, size=16) -> tuple[float, float]:
    """Pixel x-range of s[start:end] when s is drawn at x0 in the typewriter font."""
    return x0 + text_w(s[:start], "type", size) + (1 if start else 0), x0 + text_w(s[:end], "type", size) + 1
