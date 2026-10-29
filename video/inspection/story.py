"""The shots of "The Inspection", on the 3:00 timeline of docs/PITCH_PAPERS.md (Part 3).

Each shot is a function of its local time that returns a 480x270 frame; CUES lists the sound
effects on the same clock. Every number, name, date and sentence comes from the case file
(docs/PITCH_PAPERS.md, Part 2): the system's own trace of the statement.
"""
from __future__ import annotations

import math
import random

from PIL import Image

from art import (AMBER, ARCH, ARCH_DK, ARCH_LT, BLUE_PEN, CORK, CORK_DK, CORK_LT, GREEN, H, INK, INK_LT, LAMP,
                 LIME, MONITOR, NIGHT, PAPER, PAPER_DK, PAPER_SH, RED, SCREEN, STATEMENT, STATEMENT_DATE, W,
                 WOOD, WOOD_DK, WOOD_HI, arrow, booth_base, caption, check, darken, desk_base, draw, ease,
                 ease_out, in_window, lerp, lines, mouse, paper, paste_rot, person, scribble, seal, shutter,
                 slip, span_x, stamp_img, stepped, stool, tab, text, text_w, wrap)

FPS = 30
CUES: list[tuple[float, str, float]] = []  # (time, sound, gain)


def cue(t: float, name: str, gain: float = 1.0):
    CUES.append((round(t, 3), name, gain))


def keys(t: float, n: int, rate: float, gain=0.6):
    for i in range(n):
        cue(t + i / rate, "key", gain)


# ---- the booth, as most side-view shots use it -------------------------------------------------
SEAT = (182, 198)


def booth(t, shut=0.0, who=None, who_t=0.0, lean=0, talk=False, who_arm=None, lit=True, clerk=None, extra=None):
    img = booth_base(lit).copy()
    d = draw(img)
    if who and shut > 0.02:
        in_window(img, lambda dd: person(dd, 82, 150, who, who_t, lean, talk, who_arm))
        d = draw(img)
    shutter(d, shut)
    stool(d, SEAT[0], SEAT[1])
    if clerk is not False:
        mouse(d, SEAT[0], SEAT[1], t, **(clerk or {}))
    if extra:
        extra(d)
    return img


# =====================================================================================
# ACT I · THE BOOTH
# =====================================================================================
def s01_title(t):
    img = Image.new("RGB", (W, H), NIGHT)
    d = draw(img)
    l1 = "HOOLY. ONE YEAR. 20,000 STATEMENTS."
    x1 = (W - text_w(l1, "type", 32)) // 2
    text(d, (x1, 96), l1[: max(0, int((t - 0.4) * 14))], "type", 32, PAPER)
    l2a, l2b = "SOME OF THEM ", "LIE."
    x2 = (W - text_w(l2a + l2b, "type", 32)) // 2
    if t > 3.9:
        text(d, (x2, 136), l2a[: int((t - 3.9) * 14)], "type", 32, PAPER)
    if t > 5.1:
        shake = 2 if t < 5.25 else 0
        text(d, (x2 + text_w(l2a, "type", 32) + 4 + shake, 136), l2b, "type", 32, RED)
    if t > 6.4:
        img = darken(img, (t - 6.4) / 0.6)
    return img


keys(0.4, 35, 14)
keys(3.9, 13, 14)
cue(5.1, "thud", 1.0)


def s02_booth(t):
    arm = None
    if 2.0 < t < 2.9:  # pushes its glasses up
        arm = (172, 168)
    img = booth(t, 0.0, clerk={"arm": arm})
    caption(img, "Checking 20,000 claims by hand takes weeks. An LLM would guess, and this world contradicts the web.", t - 1.0)
    if t < 0.8:
        img = darken(img, 1 - t / 0.8)
    return img


cue(7.0, "hum", 0.5)


def s03_applicant(t):
    shut = ease((t - 0.2) / 1.2)
    lean = round(lerp(0, 7, ease((t - 3.4) / 0.6)))
    who_arm = (118, 147) if t > 3.6 else None
    clerk_arm = (lerp(171, 164, ease((t - 5.0) / 0.5)), lerp(187, 151, ease((t - 5.0) / 0.5))) if t > 5.0 else None
    if t > 6.0:
        clerk_arm = (170, 176)

    def paper_on_ledge(d):
        if 3.9 < t < 6.0:  # the slip slides through the slot, along the ledge
            x = lerp(112, 160, ease((t - 4.2) / 1.2))
            d.rectangle([x, 146, x + 18, 149], fill=PAPER)
            d.line([(x, 149), (x + 18, 149)], fill=PAPER_SH)

    img = booth(t, shut, "salesman", t, lean, talk=1.6 < t < 3.4, who_arm=who_arm, clerk={"arm": clerk_arm}, extra=paper_on_ledge)
    if t > 5.8:  # what the slip says
        d = draw(img)
        k = ease_out((t - 5.8) / 0.4)
        y = round(lerp(90, 66, k))
        slip(d, 172, y)
    if t < 5.6:
        caption(img, "POLYGRAPH: an automatic inspector for anyone who must check what companies claim.", t - 0.6)
    else:
        caption(img, "It checks each claim against the timeline of everything else said about it.", t - 5.8)
    return img


cue(15.2, "shutter", 0.9)
cue(16.6, "mumble", 0.5)
cue(19.2, "paper", 0.8)
cue(20.8, "paper", 0.5)


# =====================================================================================
# ACT II · THE INSPECTION
# =====================================================================================
SLIP_X = 122
I_SUBJ = (STATEMENT.index("Hooly Pixel 10"), STATEMENT.index("Hooly Pixel 10") + len("Hooly Pixel 10"))
I_VAL = (STATEMENT.index("€799"), STATEMENT.index("€799") + 4)


def desk(dim=False):
    img = desk_base(dim).copy()
    return img, draw(img)


def underline(d, tx, ty, span, k, color=BLUE_PEN):
    x0, x1 = span_x(STATEMENT, span[0], span[1], tx)
    if k > 0:
        d.line([(x0, ty + 14), (lerp(x0, x1, min(1, k)), ty + 14)], fill=color, width=2)


def circle_mark(d, tx, ty, span, k, color=RED):
    x0, x1 = span_x(STATEMENT, span[0], span[1], tx)
    box = [x0 - 5, ty - 2, x1 + 4, ty + 16]
    if k > 0:
        d.arc(box, 200, 200 + 360 * min(1, k), fill=color, width=2)


def s04_input(t):
    img, d = desk()
    k = ease_out((t - 0.4) / 0.7)
    # the page the statement comes from
    paper(d, (100, 52, 380, 198))
    d.rectangle([100, 52, 380, 66], fill=PAPER_SH)
    text(d, (108, 55), "PAGE  ·  05 OCT 2026", "signb", 8, INK)
    text(d, (372, 55), "1 SENTENCE", "sign", 8, INK_LT, "ra")
    scribble(d, 112, 170, 250, 3, PAPER_DK, rows=3, gap=6)
    x = round(lerp(-250, SLIP_X, k))
    tx, ty = slip(d, x, 100)
    if t > 1.2:  # the paper clip
        d.rectangle([x + 12, 94, x + 18, 112], outline=(150, 154, 160), width=1)
        d.rectangle([x + 14, 97, x + 16, 108], outline=(150, 154, 160))
    if t > 4.6:  # circle the date
        kk = ease((t - 4.6) / 0.8)
        d.arc([x + 236 - 80, 97, x + 236 - 1, 118], 200, 200 + 360 * kk, fill=RED, width=2)
    tab(img, 1, "INPUT", "the row and its page", t - 0.2)
    caption(img, "Each statement keeps its page and its date: lies cluster on pages, and truth changes over time.", t - 1.0)
    return img


cue(25.2, "blip", 0.6)
cue(25.4, "paper", 0.9)
cue(26.2, "clip", 0.7)
cue(29.6, "pencil", 0.7)

REGISTRY = ["Hooly Photos", "Hooly Photos Lite", "Hooly Photos Max", "Hooly Photos Plus", "Hooly Pixel 10",
            "Hooly Pixel 10 Pro", "Hooly Pixel 9", "Hooly Pixel Buds", "Hooly Pixel Fold"]
ATTRS = ["base storage", "battery capacity", "battery life", "charging power", "colours", "main camera", "memory",
         "price", "refresh rate", "released", "screen size", "shipping android", "store rating", "units sold",
         "update promise", "weight"]


def book(d, box=(52, 40, 428, 186), color=(92, 40, 36)):
    x0, y0, x1, y1 = box
    d.rectangle([x0 - 4, y0 - 3, x1 + 4, y1 + 5], fill=color)
    mid = (x0 + x1) // 2
    paper(d, (x0, y0, mid - 1, y1), shadow=False)
    paper(d, (mid + 1, y0, x1, y1), shadow=False)
    d.line([(mid, y0), (mid, y1)], fill=PAPER_DK)
    return mid


def s05_linker(t):
    img, d = desk()
    mid = book(d)
    text(d, (62, 46), "REGISTRY OF HOOLY", "signb", 8, INK)
    text(d, (mid - 8, 46), "62 NAMES", "sign", 8, INK_LT, "ra")
    target = REGISTRY.index("Hooly Pixel 10")
    row = min(target, max(0, (t - 1.0) / 2.0 * target)) if t > 1.0 else 0
    if t > 3.0:
        y = 60 + target * 13
        d.rectangle([60, y, mid - 10, y + 13], fill=(208, 220, 240))
    for i, name in enumerate(REGISTRY):
        y = 60 + i * 13
        found = t > 3.0 and i == target
        text(d, (66, y), name, "type", 16, INK if found else INK_LT)
        if found:
            d.line([(66, y + 13), (66 + text_w(name, "type", 16), y + 13)], fill=BLUE_PEN, width=2)
    if 1.0 < t < 3.6:  # the blue pencil runs down the list
        py = 60 + round(row) * 13 + 6
        d.line([(mid - 34, py + 10), (mid - 18, py - 2)], fill=BLUE_PEN, width=3)
        d.point((mid - 34, py + 11), fill=INK)
    if t > 3.4:  # its card
        text(d, (mid + 10, 46), "HOOLY PIXEL 10", "signb", 8, INK)
        text(d, (mid + 10, 58), "alias: Pixel 10", "type", 16, INK_LT)
        text(d, (mid + 10, 76), "16 ATTRIBUTES", "sign", 8, INK_LT)
        for i, a in enumerate(ATTRS):
            if t > 3.6 + i * 0.05:
                text(d, (mid + 10 + (i // 8) * 98, 90 + (i % 8) * 11), a.upper(), "sign", 8, INK)
    tx, ty = slip(d, SLIP_X, 188)
    underline(d, tx, ty, I_SUBJ, ease((t - 5.0) / 0.9))
    tab(img, 2, "WHO", "linker · Hooly's lexicon", t - 0.2)
    caption(img, "WHO? An exact lookup in Hooly's lexicon: 62 names, with their aliases.", t - 1.0)
    return img


cue(35.2, "blip", 0.6)
cue(35.5, "book", 0.9)
cue(36.0, "pencil", 0.5)
cue(38.0, "tick", 0.8)
cue(38.4, "page", 0.6)
cue(40.0, "pencil", 0.8)

RULES = [("€49 a month", "49 EUR per month"), ("$299.99", "299.99 USD"), ("€1.2bn", "1,200,000,000 EUR"),
         ("1,999 lei", "1,999 RON")]


def s06_reader(t):
    img, d = desk()
    mid = book(d, color=(40, 62, 92))
    text(d, (62, 46), "THE RULEBOOK", "signb", 8, INK)
    text(d, (mid - 8, 46), "MONEY", "signb", 8, RED, "ra")
    for i, (a, b) in enumerate(RULES):
        y = 64 + i * 26
        text(d, (64, y), a, "type", 16, INK)
        arrow(d, 64, y + 18, 80, INK_LT)
        text(d, (86, y + 11), b, "type", 16, INK_LT)
    text(d, (mid + 10, 46), "IT ALSO READS", "sign", 8, INK_LT)
    for i, s in enumerate(["dates", "counts", "percentages", "durations", "versions"]):
        text(d, (mid + 14, 60 + i * 15), "· " + s, "type", 16, INK)
    text(d, (mid + 10, 142), "EVERY EXAMPLE IN THE", "sign", 8, INK_LT)
    text(d, (mid + 10, 152), "RULES IS ONE OF OUR TESTS", "sign", 8, INK_LT)
    tx, ty = slip(d, SLIP_X, 188)
    underline(d, tx, ty, I_SUBJ, 1)
    circle_mark(d, tx, ty, I_VAL, ease((t - 4.0) / 0.9))
    if t > 5.4:
        n = int((t - 5.4) * 20)
        text(d, (366, 196), "= money"[:n], "type", 16, RED)
        text(d, (366, 210), "799 EUR"[: max(0, n - 7)], "type", 16, RED)
    tab(img, 3, "WHICH VALUE", "reader · the organisers' value rules", t - 0.2)
    caption(img, "WHICH value? Rules, not a model: a clone of the organisers' value rules.", t - 1.0)
    return img


cue(47.2, "blip", 0.6)
cue(47.5, "book", 0.9)
cue(51.0, "pencil", 0.9)
cue(52.4, "pencil", 0.5)

CANDIDATES = [("Hooly Pixel 10 · price", 0.9929), ("Hooly Pixel 10 Pro · price", 0.0006),
              ("Hooly Pixel 9 · price", 0.0006), ("Hooly Pixel Buds · price", 0.0006)]
WIN = (5, 1)  # the winning drawer (column, row) in the wall of 52


def s07_attributor(t):
    img, d = desk()
    text(d, (474, 30), "SCORING 52 CANDIDATE FACTS", "sign", 8, PAPER, "ra")
    lit = int(min(52, max(0, (t - 0.8) / 2.2 * 52)))
    out = ease((t - 6.0) / 0.5) - ease((t - 9.0) / 0.5)
    for k in range(52):
        c, r = k % 13, k // 13
        x, y = 46 + c * 30, 44 + r * 21
        win = (c, r) == WIN
        dy = round(out * 6) if win else 0
        d.rectangle([x, y + dy, x + 27, y + 18 + dy], fill=ARCH_LT if win and t > 6.0 else ARCH)
        d.rectangle([x, y + dy, x + 27, y + 18 + dy], outline=ARCH_DK)
        d.line([(x + 9, y + 12 + dy), (x + 18, y + 12 + dy)], fill=ARCH_DK, width=2)
        d.rectangle([x + 6, y + 4 + dy, x + 21, y + 8 + dy], fill=PAPER_SH)
        on = k < lit
        d.rectangle([x + 23, y + 2 + dy, x + 25, y + 4 + dy], fill=(AMBER if not (win and t > 5.2) else LAMP) if on else ARCH_DK)
        if win and t > 5.2:
            d.rectangle([x - 1, y - 1 + dy, x + 28, y + 19 + dy], outline=PAPER)
    # the scores of the best four
    for i, (name, p) in enumerate(CANDIDATES):
        if t < 3.2 + i * 0.25:
            continue
        y = 136 + i * 17
        best = i == 0
        text(d, (52, y), name, "type", 16, PAPER if best else PAPER_DK)
        w = 150 * p * ease((t - 3.4 - i * 0.25) / 1.0)
        d.rectangle([248, y + 4, 398, y + 9], fill=WOOD_DK)
        d.rectangle([248, y + 4, 248 + max(1, round(w)), y + 9], fill=PAPER if best else PAPER_DK)
        text(d, (474, y), f"{p * 100:.1f}%" if p > 0.01 else f"{p * 100:.2f}%", "type", 16, PAPER if best else PAPER_DK, "ra")
    # the slip goes into the drawer
    if 6.8 < t < 8.4:
        k = ease((t - 6.8) / 1.2)
        wx, wy = 46 + WIN[0] * 30 + 4, 44 + WIN[1] * 21 + 4
        x, y = lerp(220, wx, k), lerp(214, wy, k)
        s = lerp(1.0, 0.6, k)
        d.rectangle([x, y, x + 30 * s, y + 10 * s], fill=PAPER)
        scribble(d, x + 2, y + 3, 24 * s, 1, INK_LT, rows=1)
    elif t <= 6.8:
        d.rectangle([220, 214, 250, 224], fill=PAPER)
        scribble(d, 222, 218, 24, 1, INK_LT, rows=1)
    tab(img, 4, "WHICH FACT", "attributor · a trained model", t - 0.2)
    caption(img, "WHICH fact? Gradient-boosted trees, trained on 2,400 practice facts, score every drawer.", t - 1.0)
    return img


cue(59.2, "blip", 0.6)
for i in range(13):
    cue(59.8 + i * 0.17, "tick", 0.35)
cue(64.2, "tick", 0.9)
cue(65.0, "drawer", 0.9)
cue(66.0, "paper", 0.6)
cue(68.0, "drawer", 0.9)


def s08_kb(t):
    img, d = desk()
    paper(d, (96, 44, 384, 214))
    text(d, (104, 50), "LEDGER OF WHAT IS ON FILE", "signb", 8, INK)
    lines(d, 104, 90, 272, 8, 15, PAPER_SH)
    text(d, (106, 76), "filed under:", "type", 16, INK_LT)
    text(d, (196, 76), "Hooly Pixel 10 · price", "type", 16, INK)
    text(d, (106, 91), "value read:", "type", 16, INK_LT)
    text(d, (196, 91), "€799", "type", 16, INK)
    if t > 1.2:
        k = ease((t - 1.2) / 0.5)
        if k > 0.3:
            check(d, 106, 112, GREEN, 2)
        text(d, (128, 112), "fits the drawer", "type", 16, GREEN)
    if t > 2.2:
        text(d, (106, 140), "NO CORRECTION NEEDED", "signb", 8, GREEN)
        text(d, (106, 154), "(a value that exactly matches another fact on", "type", 16, INK_LT)
        text(d, (106, 167), " this date would have been moved there)", "type", 16, INK_LT)
    tab(img, 5, "ON FILE?", "knowledge base", t - 0.2)
    caption(img, "A value that exactly matches what is on file for this date corrects a slip. None here.", t - 0.6)
    return img


cue(71.2, "blip", 0.6)
cue(71.3, "page", 0.7)
cue(72.3, "pencil", 0.6)
cue(73.2, "tick", 0.8)

# ---- step 6: the archive ---------------------------------------------------------------------
X0D, X1D = "2025-10-01", "2026-11-01"


def day_x(day: str, x0=58, x1=466) -> float:
    import datetime as dt
    a, b, c = (dt.date.fromisoformat(s) for s in (X0D, X1D, day))
    return x0 + (x1 - x0) * (c - a).days / (b - a).days


LANES = {799: 92, 749: 152}
# the archive's documents about Hooly Pixel 10 · price (the trace of s-7): date, value, seal
DOCS = [("2026-04-28", 799, 1, "p-370"), ("2026-04-28", 799, 1, "p-384"), ("2026-04-28", 799, 1, "p-622"),
        ("2026-04-28", 799, 1, "p-1074"), ("2026-04-28", 799, -1, "p-1245"), ("2026-04-28", 799, 1, "p-1873"),
        ("2026-04-29", 799, 1, "p-633"), ("2026-05-14", 799, 1, "p-1255"), ("2026-09-02", 749, 1, "p-1859"),
        ("2026-10-08", 749, 0, "p-946")]


def s09a_walk(t):
    """Off the stool, lamp in hand, through the archive door."""
    x = lerp(SEAT[0], 452, ease((t - 0.5) / 3.4))
    walking = 0.5 < t < 3.9
    img = booth(t, 0.0, clerk=False)
    d = draw(img)
    if x < 446:
        mouse(d, x, 224, t, arm=(x + 12, 210), walk=t if walking else None, lamp=True, facing=1)
    tab(img, 6, "WHEN", "truth engine", t - 0.2)
    if t > 4.0:
        img = darken(img, (t - 4.0) / 0.5)
    return img


cue(76.2, "blip", 0.6)
for i in range(14):
    cue(76.6 + i * 0.25, "step", 0.5)


def shelves(d, offset=0):
    d.rectangle([0, 0, W, H], fill=(18, 22, 26))
    months = ["OCT 25", "NOV 25", "DEC 25", "JAN 26", "FEB 26", "MAR 26", "APR 26", "MAY 26", "JUN 26", "JUL 26",
              "AUG 26", "SEP 26", "OCT 26"]
    for i, m in enumerate(months):
        x = 10 + i * 72 - offset
        if x < -70 or x > W:
            continue
        d.rectangle([x, 30, x + 66, 232], fill=ARCH_DK)
        text(d, (x + 33, 34), m, "sign", 8, PAPER_SH, "mt")
        for s in range(4):
            y = 50 + s * 44
            d.rectangle([x + 2, y + 36, x + 64, y + 39], fill=WOOD_DK)
            r = random.Random(i * 10 + s)
            fx = x + 4
            while fx < x + 60:
                fw = r.randint(3, 6)
                d.rectangle([fx, y + 12 + r.randint(0, 6), fx + fw - 1, y + 36], fill=(PAPER_SH if r.random() < 0.5 else PAPER_DK))
                fx += fw + 1
    d.rectangle([0, 232, W, H], fill=(28, 26, 24))


def lamp_light(img, cx, cy, r=70):
    """Darkness everywhere but a stepped circle of lamplight."""
    over = Image.new("RGBA", (W, H), NIGHT + (215,))
    od = draw(over)
    for k, a in ((r, 150), (r * 0.75, 90), (r * 0.5, 30)):
        od.ellipse([cx - k, cy - k, cx + k, cy + k], fill=NIGHT + (a,))
    img.paste(over, (0, 0), over)


def s09b_archive(t):
    img = Image.new("RGB", (W, H), NIGHT)
    d = draw(img)
    shelves(d, offset=round(lerp(0, 380, ease(t / 2.6))))
    x = lerp(70, 240, ease(t / 1.8))
    mouse(d, x, 228, t, arm=(x + 12, 214), walk=t if t < 1.8 else None, lamp=True, facing=1)
    lamp_light(img, x + 12, 200)
    d = draw(img)
    if t > 1.6:  # files fly out to the clerk's arms
        for i in range(6):
            k = ease((t - 1.6 - i * 0.12) / 0.5)
            if k > 0:
                fx, fy = lerp(120 + i * 52, x - 4, k), lerp(70 + (i % 3) * 44, 196, k)
                d.rectangle([fx, fy, fx + 9, fy + 12], fill=PAPER)
    caption(img, "WHEN was it true? Every document about this fact goes on one timeline.", t - 0.1)
    return img


for i in range(7):
    cue(80.6 + i * 0.26, "step", 0.45)
cue(82.3, "paper", 0.8)


def board(d):
    d.rectangle([0, 0, W, H], fill=WOOD_DK)
    d.rectangle([10, 8, W - 10, 226], fill=CORK)
    r = random.Random(11)
    for _ in range(700):
        x, y = r.randrange(12, W - 12), r.randrange(10, 224)
        d.point((x, y), fill=CORK_DK if r.random() < 0.6 else CORK_LT)
    text(d, (W // 2, 14), "HOOLY PIXEL 10 · PRICE", "signb", 8, PAPER, "mt")
    # the axis: Oct 2025 -> Oct 2026
    d.line([(58, 196), (466, 196)], fill=INK)
    import datetime as dt
    for m in range(13):
        day = dt.date(2025 + (9 + m) // 12, (9 + m) % 12 + 1, 1).isoformat()
        x = round(day_x(day))
        d.line([(x, 193), (x, 199)], fill=INK)
        label = dt.date.fromisoformat(day).strftime("%b").upper()
        text(d, (x, 202), label, "sign", 8, INK, "mt")
    text(d, (58, 212), "2025", "sign", 8, CORK_DK)
    text(d, (466, 212), "2026", "sign", 8, CORK_DK, "ra")
    for v, y in LANES.items():
        paper(d, (16, y - 7, 50, y + 6), shadow=False)
        text(d, (33, y - 6), f"€{v}", "type", 16, INK, "mt")
        for x in range(58, 466, 6):
            d.point((x, y), fill=CORK_DK)


def doc_card(d, x, y, sealed, seed):
    paper(d, (x - 9, y - 7, x + 9, y + 7))
    scribble(d, x - 6, y - 3, 12, seed, INK_LT, rows=2, gap=3)
    if sealed:
        seal(d, (x + 6, y + 5), 3, GREEN if sealed > 0 else RED, seed)
    d.ellipse([x - 1, y - 9, x + 1, y - 7], fill=RED)  # pin


def pos(i):
    day, v, s, _ = DOCS[i]
    same = [k for k in range(i) if DOCS[k][0] == day]
    return day_x(day) - 4 + len(same) * 2, LANES[v] - len(same) * 10


def s09c_board(t):
    img = Image.new("RGB", (W, H), NIGHT)
    d = draw(img)
    board(d)
    for i, (day, v, s, rid) in enumerate(DOCS):
        if t > 0.6 + i * 0.48:
            x, y = pos(i)
            doc_card(d, x, y, s, i)
    # the lime line: the staircase the engine fits
    k = ease((t - 5.8) / 2.8)
    if k > 0:
        xa, xb, xc = day_x("2026-04-28"), day_x("2026-09-02"), day_x("2026-10-08") + 8
        pts = [(xa, LANES[799]), (xb, LANES[799]), (xb, LANES[749]), (xc, LANES[749])]
        total = (xb - xa) + (LANES[749] - LANES[799]) + (xc - xb)
        left = total * k
        path = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            seg = abs(b[0] - a[0]) + abs(b[1] - a[1])
            if left >= seg:
                path.append(b)
                left -= seg
            else:
                f = left / seg
                path.append((lerp(a[0], b[0], f), lerp(a[1], b[1], f)))
                break
        d.line(path, fill=LIME, width=3)
    # today's statement, pinned on 5 October
    if t > 8.0:
        x = day_x("2026-10-05")
        for yy in range(26, 192, 6):
            d.line([(x, yy), (x, yy + 2)], fill=LIME)
        d.rectangle([x - 10, LANES[799] - 8, x + 10, LANES[799] + 8], fill=PAPER)
        text(d, (x, LANES[799] - 6), "€799", "type", 16, RED, "mt")
        d.ellipse([x - 15, LANES[799] - 13, x + 15, LANES[799] + 13], outline=LIME, width=2)
        text(d, (x, 26), "5 OCT", "signb", 8, LIME, "mt")
    if t > 8.6:
        x = day_x("2026-10-05")
        paper(d, (x - 66, LANES[749] + 14, x + 6, LANES[749] + 30))
        text(d, (x - 30, LANES[749] + 15), "holds €749", "type", 16, INK, "mt")
    caps = [(0.0, "Each fact becomes a staircase over time, fitted by dynamic programming; sealed rows anchor it."),
            (5.6, "€799 was true. In April."), (8.4, "On 5 October, the timeline says €749.")]
    cur = [c for c in caps if t >= c[0]][-1]
    caption(img, cur[1], t - cur[0] if cur[0] else t + 5)
    return img


for i in range(len(DOCS)):
    cue(83.6 + i * 0.48, "pin", 0.7)
cue(88.8, "marker", 0.8)
cue(91.0, "pin", 1.0)


def s09d_same(t):
    img, d = desk()
    paper(d, (8, 92, 234, 180))
    text(d, (16, 98), "ARCHIVE · 28 APR 2026", "signb", 8, INK)
    text(d, (16, 118), "Hooly Pixel 10 costs €799", "type", 16, INK)
    scribble(d, 16, 146, 120, 5, PAPER_DK, rows=2, gap=6)
    seal(d, (212, 160), 9, GREEN, 3)
    text(d, (16, 166), "SEALED TRUE", "sign", 8, GREEN)
    paper(d, (244, 92, 470, 180))
    text(d, (252, 98), "STATEMENT · 05 OCT 2026", "signb", 8, INK)
    text(d, (252, 118), STATEMENT, "type", 16, INK)
    scribble(d, 252, 146, 120, 6, PAPER_DK, rows=2, gap=6)
    lines_ = [("SAME SENTENCE.", PAPER, 0.6), ("TRUE IN APRIL.", (130, 190, 110), 1.6), ("FALSE IN OCTOBER.", (230, 90, 84), 2.6)]
    for i, (s, c, at) in enumerate(lines_):
        if t > at:
            n = int((t - at) * 26)
            text(d, (W // 2 - text_w(s, "signb", 16) // 2, 14 + i * 22), s[:n], "signb", 16, c)
    return img


cue(94.6, "thud", 0.35)
cue(95.6, "thud", 0.45)
cue(96.6, "thud", 0.6)

# ---- step 7: the verdict -------------------------------------------------------------------------
P_FALSE = 0.982


def needle_value(t):
    if t < 2.4:
        return 0.0
    x = t - 2.4
    return P_FALSE - P_FALSE * math.exp(-3.2 * x) * math.cos(7 * x) + (0.004 * math.sin(40 * t) if x > 1.4 else 0)


def s10a_polygraph(t):
    img, d = desk()
    cx, cy, r = 300, 160, 80
    d.rectangle([cx - r - 18, cy - r - 16, cx + r + 18, cy + 34], fill=(88, 72, 56))
    d.pieslice([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=PAPER)
    d.arc([cx - r + 4, cy - r + 4, cx + r - 4, cy + r - 4], 180 + 180 * 0.6, 360, fill=RED, width=6)
    for i in range(11):
        a = math.pi * (1 - i / 10)
        d.line([(cx + (r - 14) * math.cos(a), cy - (r - 14) * math.sin(a)), (cx + (r - 4) * math.cos(a), cy - (r - 4) * math.sin(a))], fill=INK)
    a = math.pi * (1 - 0.6)
    d.line([(cx + 20 * math.cos(a), cy - 20 * math.sin(a)), (cx + (r - 2) * math.cos(a), cy - (r - 2) * math.sin(a))], fill=RED)
    text(d, (cx + (r + 6) * math.cos(a), cy - (r + 12) * math.sin(a)), "60%", "sign", 8, PAPER, "mb")
    text(d, (cx - r + 2, cy + 4), "TRUE", "sign", 8, PAPER, "la")
    text(d, (cx + r - 2, cy + 4), "FALSE", "sign", 8, PAPER, "ra")
    v = needle_value(t)
    a = math.pi * (1 - v)
    d.line([(cx, cy), (cx + (r - 10) * math.cos(a), cy - (r - 10) * math.sin(a))], fill=INK, width=2)
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=INK)
    text(d, (cx, cy + 10), "P(FALSE)", "sign", 8, PAPER, "mt")
    if t > 4.4:
        text(d, (cx, cy + 18), f"{P_FALSE * 100:.1f}%", "type", 16, PAPER, "mt")
    # the 64 clues, fed in
    n = int(min(64, max(0, (t - 0.3) / 2.0 * 64)))
    for i in range(min(n, 12)):
        paper(d, (40 + i, 150 - i * 4, 104 + i, 186 - i * 4), shadow=False)
    if n < 64:
        k = ((t - 0.3) * 32) % 1
        d.rectangle([lerp(104, cx - r - 16, k), 120, lerp(104, cx - r - 16, k) + 10, 126], fill=PAPER)
    text(d, (72, 196), f"{n} CLUES", "signb", 8, PAPER, "mt")
    # the chart strip
    d.rectangle([0, 210, W, 236], fill=PAPER)
    r_ = random.Random(int(t * 10))
    pts = []
    for x in range(0, W, 4):
        amp = 3 if t < 2.4 else 9
        pts.append((x, 223 + r_.uniform(-amp, amp) * (0.3 + 0.7 * (x > W - 120))))
    d.line(pts, fill=INK)
    tab(img, 7, "VERDICT", "judge · decision trees on 64 clues", t - 0.2)
    caption(img, "64 clues; decision trees trained only on labelled rows; confidence calibrated on its own mistakes.", t - 0.6)
    return img


cue(100.2, "blip", 0.6)
cue(100.4, "cards", 0.8)
for i in range(16):
    cue(102.4 + i * 0.12, "tick", 0.5 - i * 0.02)


def s10b_stamp(t):
    img, d = desk()
    tx, ty = slip(d, SLIP_X, 40, h=176)
    underline(d, tx, ty, I_SUBJ, 1)
    circle_mark(d, tx, ty, I_VAL, 1)
    hit = 1.0
    sx, sy = SLIP_X + 118, 148
    if t >= hit:
        paste_rot(img, stamp_img("FALSE", "STALE · 98% SURE", RED, 32), (sx, sy), -6)
        d = draw(img)
    # the stamp itself: down, thud, up
    if t < hit:
        y = lerp(-80, sy - 18, ease(t / hit))
    else:
        y = lerp(sy - 18, -80, ease((t - hit - 0.25) / 0.6))
    if y > -79:
        d.rectangle([sx - 34, y - 16 + 22, sx + 34, y + 22], fill=(100, 30, 28))
        d.rectangle([sx - 30, y - 20, sx + 30, y + 6], fill=WOOD_HI)
        d.rectangle([sx - 8, y - 60, sx + 8, y - 20], fill=WOOD)
        d.ellipse([sx - 14, y - 76, sx + 14, y - 52], fill=WOOD_HI)
    caption(img, "64 clues; decision trees trained only on labelled rows; confidence calibrated on its own mistakes.", 9)
    return img


cue(107.0, "thud", 1.0)


def s10c_nod(t):
    nod = 3 * max(0, math.sin(t * 5)) if t < 1.3 else 0
    return booth(t, 0.0, clerk={"nod": nod})


def s11_writer(t):
    img, d = desk()
    paper(d, (96, 44, 384, 150))
    text(d, (106, 52), "/OUTPUT/OUTPUT.CSV", "signb", 8, INK)
    text(d, (106, 68), "id,type,text,form,label,confidence", "type", 16, INK_LT)
    line = "s-7,,,,false,0.982"
    n = int(max(0, (t - 0.3) * 11))
    text(d, (106, 86), line[:n], "type", 16, INK)
    if n < len(line) and int(t * 4) % 2:
        d.rectangle([106 + text_w(line[:n], "type", 16) + 2, 88, 106 + text_w(line[:n], "type", 16) + 7, 98], fill=INK)
    # the typewriter
    d.rectangle([90, 128, 390, 142], fill=(40, 42, 46))
    d.polygon([(70, 236), (410, 236), (380, 142), (100, 142)], fill=(54, 58, 62))
    for row in range(3):
        for k in range(10 - row):
            x = 130 + row * 12 + k * 24
            y = 166 + row * 20
            press = n < len(line) and (k + row) % 7 == n % 7
            d.ellipse([x, y + (2 if press else 0), x + 14, y + 12 + (2 if press else 0)], fill=PAPER_SH, outline=INK)
    tab(img, 8, "THE RECORD", "writer · output.csv", t - 0.1)
    caption(img, "A safe table within seconds, then the final one, swapped in whole.", t - 0.3)
    return img


cue(112.1, "blip", 0.5)
keys(112.3, 18, 11, 0.7)
cue(114.1, "bell", 0.6)

# =====================================================================================
# ACT III · THE SHIFT
# =====================================================================================
CASES = [
    {"who": "gavin", "text": "Gavin: Gemini speaks 40 languages, which is more than any competitor.", "date": "10 JUN 2026",
     "record": ["HOOLY GEMINI · LANGUAGES", "on 10 Jun 2026: 12"], "stamp": ("FALSE", "INVENTED · 96% SURE"), "color": RED},
    {"who": "host", "text": "Hooly Pixel 10 Pro arrives the same day at €1,049.", "date": "28 APR 2026",
     "record": ["HOOLY PIXEL 10 PRO · PRICE", "on 28 Apr 2026: €1,099", "€1,049 only later"], "stamp": ("FALSE", "PREMATURE · 93% SURE"), "color": RED},
    {"who": "salesman", "text": "Hooly Photos Max now gives you 10 TB of storage.", "date": "14 JUN 2026",
     "record": ["HOOLY PHOTOS MAX · STORAGE", "10 TB since 7 May 2026"], "stamp": ("TRUE", "98% SURE"), "color": GREEN},
]


def s12_montage(t):
    i = min(2, int(t // 5))
    c, u = CASES[i], t - i * 5
    if u < 1.1:
        img = booth(u, 1.0, c["who"], u, lean=3, talk=True)
    else:
        img, d = desk()
        w = 210
        paper(d, (24, 52, 24 + w, 52 + 22 + 13 * len(wrap(c["text"], 28)) + 8))
        text(d, (30, 56), "STATEMENT", "sign", 8, INK_LT)
        text(d, (24 + w - 6, 56), c["date"], "sign", 8, (110, 70, 120), "ra")
        for k, row in enumerate(wrap(c["text"], 28)):
            text(d, (30, 72 + 13 * k), row, "type", 16, INK)
        if u > 1.6:
            x = round(lerp(480, 256, ease_out((u - 1.6) / 0.4)))
            paper(d, (x, 52, x + 200, 52 + 18 + 14 * len(c["record"])))
            text(d, (x + 6, 56), "ARCHIVE RECORD", "signb", 8, INK)
            for k, row in enumerate(c["record"]):
                text(d, (x + 6, 68 + 14 * k), row if k else row, "type" if k else "sign", 16 if k else 8, INK)
        if u > 3.0:
            paste_rot(img, stamp_img(*c["stamp"], color=c["color"], scale=24), (130, 170), -6 if i != 1 else 5)
    caption(img, "It catches all three kinds of lie: never true, no longer true, not true yet.", t - 0.3)
    return img


for i in range(3):
    cue(115.0 + i * 5 + 0.1, "mumble", 0.5)
    cue(115.0 + i * 5 + 1.1, "paper", 0.7)
    cue(115.0 + i * 5 + 1.6, "paper", 0.5)
    cue(115.0 + i * 5 + 3.0, "thud" if i < 2 else "seal", 1.0)


CLAIMS_CAPTION = "And it writes 1,000 new claims, only from sealed records: 992 true when checked."


def s13_after(t):
    if t < 4.0:
        shut = 1 - ease((t - 0.2) / 1.0)
        writing = t > 1.6
        arm = (164 + 3 * math.sin(stepped(t) * 18), 150 + 2 * math.cos(stepped(t) * 13)) if writing else None
        img = booth(t, shut, "salesman" if shut > 0.05 else None, t, clerk={"arm": arm}, lit=False)
        img = darken(img, 0.22)
        d = draw(img)
        if writing:
            d.rectangle([150, 147, 168, 150], fill=PAPER)
        caption(img, CLAIMS_CAPTION, t - 0.3)
        return img
    u = t - 4.0
    img, d = desk(dim=True)
    sheets = [("Hooly Pixel 10 Pro costs €1,049.", 0.2), ("Hooly Pixel 10 cost €799 at Made by Hooly 2026.", 2.4)]
    done = sum(1 for _, at in sheets if u > at + 1.8)
    count = done if u < 4.6 else int(lerp(2, 1000, ease((u - 4.6) / 2.6)))
    # the stack, on the right
    layers = min(16, max(done, count // 60))
    for j in range(layers):
        paper(d, (300 - j, 150 - j * 3, 452 - j, 196 - j * 3), shadow=(j == 0))
        seal(d, (440 - j, 186 - j * 3), 4, GREEN, j)
    if count:
        text(d, (376, 206), f"{count:,} CLAIM{'' if count == 1 else 'S'}", "signb", 8, PAPER, "mt")
    if 4.6 < u < 7.2:  # sheets flick onto the stack
        k = ((u - 4.6) * 6) % 1
        fx, fy = lerp(150, 300, k), lerp(120, 150 - layers * 3, k)
        d.rectangle([fx, fy, fx + 60, fy + 18], fill=PAPER)
    # the certificate being written, on the left
    for k, (text_, at) in enumerate(sheets):
        if not (at <= u < at + 2.3):
            continue
        slide = ease((u - at - 1.8) / 0.5)
        x = round(lerp(lerp(-260, 24, ease_out((u - at) / 0.4)), 300, slide))
        y = round(lerp(56, 150 - layers * 3, slide))
        paper(d, (x, y, x + 260, y + 80))
        text(d, (x + 8, y + 6), f"CERTIFIED STATEMENT  No. {k + 1:04d}", "signb", 8, INK)
        typed = int((u - at) * 40)
        for j, row in enumerate(wrap(text_, 31)):
            text(d, (x + 8, y + 22 + 13 * j), row[: max(0, typed)], "type", 16, INK)
            typed -= len(row) + 1
        if u > at + 1.1:
            seal(d, (x + 238, y + 62), 9, GREEN, k)
            check(d, x + 8, y + 64, GREEN)
            text(d, (x + 20, y + 65), "CHECKED AGAINST THE RULEBOOK", "sign", 8, GREEN)
    caption(img, CLAIMS_CAPTION, 9)
    return img


cue(130.2, "shutter", 0.8)
cue(131.6, "pencil", 0.6)
cue(134.2, "paper", 0.7)
cue(135.3, "seal", 0.9)
cue(136.4, "paper", 0.7)
cue(137.5, "seal", 0.9)
for i in range(22):
    cue(138.6 + i * 0.12, "flick", 0.35)


# ---- part 3 and 4: memos on the desk -----------------------------------------------------------------
def memo(t, rows, box=(36, 22, 444, 222), gap=19, rate=0.9, start=0.3):
    """A typed memo: rows of (text, style), style in title-red, title-green, tick, plain, blank."""
    img, d = desk(dim=True)
    paper(d, box)
    x, y = box[0] + 12, box[1] + 10
    at = start
    for row, style in rows:
        if style == "blank":
            y += gap // 2
            continue
        if t > at:
            n = int((t - at) * 70)
            if style.startswith("title"):
                text(d, (x, y + 4), row[:n], "signb", 8, RED if style == "title-red" else GREEN)
            elif style == "tick":
                check(d, x, y + 5, GREEN, 2)
                text(d, (x + 20, y), row[:n], "type", 16, INK)
            else:
                text(d, (x, y), row[:n], "type", 16, INK)
            at += rate if style != "plain" else rate * 0.55
        y += gap
    return img


WHY = [("WHAT MAKES IT DIFFERENT", "title-red"), ("", "blank"),
       ("It judges facts on their date, not the wording.", "tick"),
       ("No LLM: only what this world says counts.", "tick"),
       ("Every verdict shows its evidence.", "tick"),
       ("Calibrated confidence: 90% means about 90%.", "tick")]


def s16_why(t):
    img = memo(t, WHY, box=(36, 36, 444, 192), gap=24)
    caption(img, "The benefit: verdicts you can audit, at a scale no team could read.", t - 4.2)
    return img


REPORT = [("UNDER THE HOOD", "title-red"), ("", "blank"),
          ("Python, numpy, scikit-learn: one Docker image.", "plain"),
          ("A run the size of the real one:", "plain"),
          ("  19,000 statements in 200 s   (limit 1,800 s)", "plain"),
          ("  memory 0.8 GB                (limit 6 GB)", "plain"),
          ("Labels right on held-out rows: 88%  (all-true: 83%)", "plain"),
          ("New claims: 1,000 · 992 true when checked", "plain"),
          ("Docker vs. trace: 400 of 400 labels identical", "plain"),
          ("LLMs at run time: 0 · network: none", "plain")]


def s15_report(t):
    return memo(t, REPORT, box=(30, 18, 450, 230), rate=0.5)


LIMITS = [("WHAT IT STILL MISSES", "title-red"),
          ("Catches 45% of the lies in testing (126 of 277).", "plain"),
          ("It slips on ambiguity: which quarter's revenue?", "plain"),
          ("Rumours are rarely called unsure (2 of 39).", "plain"),
          ("", "blank"),
          ("NEXT", "title-green"),
          ("Sharper extraction for ambiguous sentences.", "plain"),
          ("A rumour detector, for honest unsure verdicts.", "plain"),
          ("Any company: give it its names and its documents.", "plain")]


def s17_limits(t):
    return memo(t, LIMITS, box=(30, 18, 450, 230), rate=0.75)


def s18_title(u):
    img = Image.new("RGB", (W, H), NIGHT)
    d = draw(img)
    text(d, (W // 2, 70), "POLYGRAPH", "signb", 32, PAPER, "mt")
    text(d, (W // 2, 112), "TEAM ICARUS", "sign", 16, LIME, "mt")
    last = "Hype is easy to write. Hard to keep consistent. We check the timeline."
    for k, row in enumerate(wrap(last, 40)):
        text(d, (W // 2, 160 + k * 18), row[: max(0, int((u - 0.4) * 50) - k * 40)], "cap", 13, PAPER_DK, "mt")
    if u > 3.4:
        img = darken(img, (u - 3.4) / 0.6)
    return img


# =====================================================================================
# THE TIMELINE (docs/PITCH_PAPERS.md, Part 3)
# =====================================================================================
# (start, end, shot, original start, original end): a shot written for the original slot
# plays sped up or slowed to fit its new one, and its sound cues move with it.
TIMELINE = [
    # 1/4 the problem: who, why, what
    (0.0, 7.0, s01_title, 0.0, 7.0), (7.0, 15.0, s02_booth, 7.0, 15.0), (15.0, 25.0, s03_applicant, 15.0, 25.0),
    # 2/4 the demo: one statement from input to output, drawn...
    (25.0, 32.0, s04_input, 25.0, 35.0), (32.0, 41.0, s05_linker, 35.0, 47.0), (41.0, 49.0, s06_reader, 47.0, 59.0),
    (49.0, 58.0, s07_attributor, 59.0, 71.0), (58.0, 62.0, s08_kb, 71.0, 76.0), (62.0, 65.0, s09a_walk, 76.0, 80.5),
    (65.0, 67.0, s09b_archive, 80.5, 83.0), (67.0, 75.5, s09c_board, 83.0, 94.0), (75.5, 80.5, s09d_same, 94.0, 100.0),
    (80.5, 85.5, s10a_polygraph, 100.0, 106.0), (85.5, 88.5, s10b_stamp, 106.0, 110.0),
    (88.5, 89.5, s10c_nod, 110.0, 112.0), (89.5, 92.5, s11_writer, 112.0, 115.0),
    # ...then a real one: sample row s-20 through the real system (live.py, full HD)
    (92.5, 132.5, "live", None, None),
    # 3/4 why it matters
    (132.5, 143.0, s12_montage, 115.0, 130.0), (143.0, 150.0, s13_after, 130.0, 142.0), (150.0, 158.0, s16_why, None, None),
    # 4/4 under the hood: implementation, limits, next
    (158.0, 165.0, s15_report, None, None), (165.0, 174.0, s17_limits, None, None), (174.0, 178.0, s18_title, None, None),
]
TOTAL = 178.0
LIVE = (92.5, 132.5)
CHAPTERS = [(7.0, 25.0, "1/4 · THE PROBLEM"), (25.0, 92.5, "2/4 · THE DEMO"), (132.5, 158.0, "3/4 · WHY IT MATTERS"),
            (158.0, 174.0, "4/4 · UNDER THE HOOD")]
# the music's arrangement, section by section (sound.py)
ARRANGEMENT = [(7.0, 25.0, {"bass": 1, "kick": 0.6, "hat": 0, "mel": 0}),
               (25.0, 92.5, {"bass": 1, "kick": 0.8, "hat": 0.5, "mel": 0.6}),
               (92.5, 132.5, {"bass": 0.6, "kick": 0.4, "hat": 0.3, "mel": 0.3}),
               (132.5, 143.0, {"bass": 1.1, "kick": 1, "hat": 1, "mel": 0.9, "fast": 1}),
               (143.0, 158.0, {"bass": 0.8, "kick": 0.5, "hat": 0.3, "mel": 0.6}),
               (158.0, 174.0, {"bass": 0.7, "kick": 0.4, "hat": 0, "mel": 0.4})]
END_CHORD = 174.0

# move every cue written on the original clock into its shot's new slot
_orig = list(CUES)
CUES.clear()
for c, name, g in _orig:
    for a, b, fn, oa, ob in TIMELINE:
        if oa is not None and oa <= c < ob:
            CUES.append((round(a + (c - oa) * (b - a) / (ob - oa), 3), name, g))
            break
# the new shots' cues, on the new clock
import live  # noqa: E402
for c, name, g in live.CUES:
    cue(LIVE[0] + c, name, g)
for i in range(4):
    cue(150.3 + i * 0.9, "pencil", 0.4)
keys(158.3, 46, 30, 0.3)
keys(165.3, 40, 30, 0.3)
cue(174.1, "thud", 0.8)


def chapter(img: Image.Image, t: float):
    """The part of the organisers' structure we are in, top right."""
    for a, b, label in CHAPTERS:
        if a <= t < b:
            d = draw(img)
            w = text_w(label, "sign", 8) + 12
            d.rectangle([W - w - 6, 5, W - 6, 20], fill=NIGHT)
            text(d, (W - 12, 7), label, "sign", 8, PAPER_DK, "ra")
            return img
    return img


def frame(t: float) -> Image.Image:
    """The frame at t: 480x270 pixel art, or a full-HD frame for the live walkthrough."""
    for a, b, fn, oa, ob in TIMELINE:
        if a <= t < b and fn is not None:
            if fn == "live":
                return live.frame(t - a)
            local = (t - a) * ((ob - oa) / (b - a)) if oa is not None else t - a
            return chapter(fn(local), t)
    return Image.new("RGB", (W, H), NIGHT)
