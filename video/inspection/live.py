"""The live walkthrough: one of the organisers' 20 sample rows (s-20, published 09:00 on 29 Oct)
through Polygraph, stage by stage, beside the architecture diagram, in the frontend's clean style.

Every number is from the real trace of the live Docker run on the sample (out/live/trace.json),
copied here so the film renders the same anywhere. Drawn in full HD with soft, keynote-style
motion: fades, rises and blur-to-sharp, eased.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
DUR = 40.0
FONTS = Path(__file__).resolve().parent.parent / "fonts"
BG, FG, MID, LOW = (11, 11, 12), (237, 237, 237), (154, 158, 166), (90, 94, 102)
LIME, GREEN, RED = (215, 241, 59), (123, 216, 143), (255, 107, 122)

# ---- the case: sample row s-20, as the system traced it -------------------------------------------
TEXT = "Hooly I/O brought 3,000 attendees to Berlin for 2 days and 24 talks."
SUBJECT = "Hooly I/O"
VALUES = [("3,000 attendees", "quantity · 3,000 · attendee"), ("2 days", "duration · 2 · day"), ("24 talks", "quantity · 24 · talk")]
FACTS = [  # value, fact, probability, candidates scored
    ("Berlin", "Hooly I/O 2026 · city", 0.966, 42), ("3,000 attendees", "Hooly I/O 2026 · attendees", 0.963, 91),
    ("24 talks", "Hooly I/O 2026 · talks", 0.427, 46), ("2 days", "Hooly I/O 2026 · length", 0.184, 46)]
TRUTH = [  # fact = value, status, evidence
    ("city = Berlin", True, "7 mentions, 5 sealed true"), ("talks = 24", True, "5 mentions, 3 sealed true"),
    ("length = 2 days", True, "3 mentions, 2 sealed true"), ("attendees = 3,000", False, "the archive holds 1,200")]
ATTENDEES = [("2026-03-24", 1200, 0), ("2026-03-24", 1200, 1), ("2026-03-27", 1200, 1), ("2026-04-10", 1200, 1),
             ("2026-09-17", 3000, -1)]  # date, value, seal (1 true, -1 false, 0 none); this sentence: 30 Mar, 3,000
P_FALSE, PROBS, CONF = 0.918, [("true", 0.081, GREEN), ("false", 0.916, RED), ("unsure", 0.003, (245, 184, 90))], 0.895
CSV = "s-20,,,,false,0.895"

# the stages: (start, name, step label)
STAGES = [(3.4, "input", "01 · INPUT"), (7.6, "read", "02 · LINKER + READER"), (12.6, "attr", "03 · ATTRIBUTOR"),
          (17.6, "kb", "04 · KNOWLEDGE BASE"), (20.4, "truth", "05 · TRUTH ENGINE"), (28.2, "judge", "06 · JUDGE"),
          (34.0, "writer", "07 · WRITER")]
END = 38.6


@lru_cache(maxsize=None)
def F(size: int, weight: str = "Regular") -> ImageFont.FreeTypeFont:
    if weight == "mono":
        return ImageFont.truetype("C:/Windows/Fonts/consola.ttf", size)
    f = ImageFont.truetype(str(FONTS / "Figtree.ttf"), size)
    f.set_variation_by_name(weight)
    return f


def clamp(x):
    return max(0.0, min(1.0, x))


def out5(x):  # ease-out quint: quick start, long soft landing
    x = clamp(x)
    return 1 - (1 - x) ** 5


def back(x, s=1.4):  # ease-out back: a small overshoot
    x = clamp(x) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def inout(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def rgba(c, a):
    return (*c, max(0, min(255, int(255 * a))))


class Layer:
    """A transparent layer to draw one block on, then fade, rise and blur it in."""

    def __init__(self):
        self.im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def text(self, xy, s, size, color=FG, weight="Regular", a=1.0, anchor="la"):
        self.d.text(xy, s, font=F(size, weight), fill=rgba(color, a), anchor=anchor)

    def put(self, base: Image.Image, alpha=1.0, dy=0.0, blur=0.0):
        im = self.im
        if blur > 0.3:
            im = im.filter(ImageFilter.GaussianBlur(blur))
        if alpha < 1:
            im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
        base.alpha_composite(im, (0, int(round(dy))))


def tw(s, size, weight="Regular"):
    b = F(size, weight).getbbox(s)
    return b[2] - b[0]


# ---- the architecture, left -----------------------------------------------------------------------
CX = 330
NODES = {"input": (CX, 340, "Input"), "linker": (CX - 60, 450, "Linker"), "reader": (CX + 60, 450, "Reader"),
         "attr": (CX, 560, "Attributor"), "kb": (CX, 660, "Knowledge base"), "truth": (CX, 760, "Truth engine"),
         "judge": (CX, 860, "Judge"), "writer": (CX, 960, "Writer")}
ORDER = {"input": 0, "linker": 1, "reader": 1, "attr": 2, "kb": 3, "truth": 4, "judge": 5, "writer": 6}
EDGES = [("input", "linker", 1), ("input", "reader", 1), ("linker", "attr", 2), ("reader", "attr", 2), ("attr", "kb", 3),
         ("kb", "truth", 4), ("truth", "judge", 5), ("judge", "writer", 6)]
SUB = {"input": "row s-20 · 30 Mar 2026", "linker": "Hooly I/O 2026", "reader": "3 values", "attr": "4 facts",
       "kb": "no correction", "truth": "1 never true", "judge": "P(false) 91.8%", "writer": "false 0.895"}


def curve(a, b, n=40):
    (x0, y0), (x1, y1) = a, b
    m = (y1 - y0) / 2
    pts = []
    for i in range(n + 1):
        u = i / n
        x = (1 - u) ** 3 * x0 + 3 * (1 - u) ** 2 * u * x0 + 3 * (1 - u) * u ** 2 * x1 + u ** 3 * x1
        y = (1 - u) ** 3 * y0 + 3 * (1 - u) ** 2 * u * (y0 + m) + 3 * (1 - u) * u ** 2 * (y1 - m) + u ** 3 * y1
        pts.append((x, y))
    return pts


def stage_at(t):
    cur = -1
    for i, (s, _, _) in enumerate(STAGES):
        if t >= s:
            cur = i
    return cur


def pipeline(base, t, appear):
    L = Layer()
    d = L.d
    cur = stage_at(t)
    for a, b, k in EDGES:
        pts = curve(NODES[a][:2], NODES[b][:2])
        d.line(pts, fill=rgba((255, 255, 255), 0.14), width=3)
        s0 = STAGES[k][0]
        prog = inout((t - (s0 - 0.75)) / 0.75)
        if prog > 0:
            n = max(2, int(len(pts) * prog))
            d.line(pts[:n], fill=rgba(LIME, 1), width=5)
            if prog < 1:
                hx, hy = pts[n - 1]
                d.ellipse([hx - 7, hy - 7, hx + 7, hy + 7], fill=rgba(LIME, 1))
    for key, (x, y, name) in NODES.items():
        k = ORDER[key]
        reached = cur >= k
        current = cur == k
        if current:
            pulse = 0.5 + 0.5 * math.sin(t * 4)
            r = 22 + 4 * pulse
            d.ellipse([x - r, y - r, x + r, y + r], outline=rgba(LIME, 0.35), width=2)
        fill = LIME if current else FG if reached else (11, 11, 12)
        d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=rgba(fill, 1), outline=rgba(FG if reached else LOW, 1), width=3)
        left = key == "linker"
        tx = x - 34 if left else x + 34
        anchor = "rs" if left else "ls"
        d.text((tx, y + 2), name, font=F(30, "SemiBold"), fill=rgba(FG if reached else LOW, 1), anchor=anchor)
        if reached:
            a = out5((t - STAGES[k][0]) / 0.6)
            d.text((tx, y + 32), SUB[key], font=F(20, "mono"), fill=rgba(MID, a), anchor=anchor)
    L.put(base, appear, (1 - appear) * 24)


# ---- the stages, right --------------------------------------------------------------------------------
PX, PY = 760, 330


def head(L, label, title, t, t0):
    a = out5((t - t0) / 0.6)
    L.text((PX, PY), "STEP " + label, 22, LIME, "mono", a)
    L.text((PX, PY + 34), title, 52, FG, "Bold", a)


def highlight_sentence(L, x, y, t, t0, size=36):
    """The sentence, with its subject underlined and its values lit up one by one."""
    f = F(size, "Medium")
    L.d.text((x, y), TEXT, font=f, fill=rgba(FG, 1))
    marks = [(SUBJECT, "subj", 0.3)] + [(v, "val", 0.7 + i * 0.35) for i, (v, _) in enumerate(VALUES)]
    for s, kind, at in marks:
        k = out5((t - t0 - at) / 0.5)
        if k <= 0:
            continue
        i = TEXT.index(s)
        x0 = x + f.getlength(TEXT[:i])
        x1 = x0 + f.getlength(s)
        if kind == "subj":
            L.d.line([(x0, y + size + 8), (x0 + (x1 - x0) * k, y + size + 8)], fill=rgba(FG, 1), width=3)
        else:
            L.d.rounded_rectangle([x0 - 6, y - 4, x1 + 6, y + size + 10], 8, fill=rgba(LIME, 0.22 * k))
            L.d.text((x0, y), s, font=f, fill=rgba(LIME, k))


def panel(name, t, t0):
    L = Layer()
    d = L.d
    if name == "input":
        head(L, "01 · INPUT", "The sentence and its page", t, t0)
        k = out5((t - t0 - 0.25) / 0.7)
        d.rounded_rectangle([PX, PY + 130, PX + 1060, PY + 330], 22, fill=rgba((24, 24, 27), k), outline=rgba((255, 255, 255), 0.08 * k), width=2)
        L.text((PX + 36, PY + 170), TEXT, 36, FG, "Medium", k)
        L.text((PX + 36, PY + 250), "page dated 30 Mar 2026 · 1 sentence on its page · sample row s-20", 24, MID, "mono", k)
        L.text((PX, PY + 380), "The page and its date travel with every sentence: lies cluster", 28, MID, "Regular", out5((t - t0 - 0.7) / 0.7))
        L.text((PX, PY + 418), "on pages, and truth changes over time.", 28, MID, "Regular", out5((t - t0 - 0.7) / 0.7))
    elif name == "read":
        head(L, "02 · LINKER + READER", "Who, and which values", t, t0)
        highlight_sentence(L, PX, PY + 140, t, t0)
        a = out5((t - t0 - 1.0) / 0.6)
        L.text((PX, PY + 230), "WHO", 20, LOW, "mono", a)
        L.text((PX, PY + 260), "Hooly I/O 2026", 34, FG, "SemiBold", a)
        L.text((PX, PY + 304), "written “Hooly I/O”, from Hooly's lexicon", 22, MID, "mono", a)
        L.text((PX + 520, PY + 230), "VALUES, BY THE ORGANISERS' RULES", 20, LOW, "mono", a)
        for i, (v, form) in enumerate(VALUES):
            b = out5((t - t0 - 1.3 - i * 0.25) / 0.6)
            L.text((PX + 520, PY + 262 + i * 66), v, 32, LIME, "SemiBold", b)
            L.text((PX + 520, PY + 300 + i * 66), form, 22, MID, "mono", b)
    elif name == "attr":
        head(L, "03 · ATTRIBUTOR", "Which fact each value belongs to", t, t0)
        L.text((PX, PY + 128), "Gradient-boosted trees score every fact a value could belong to; the best is kept.", 26, MID, "Regular",
               out5((t - t0 - 0.3) / 0.6))
        for i, (v, fact, p, n) in enumerate(FACTS):
            b = out5((t - t0 - 0.6 - i * 0.22) / 0.6)
            y = PY + 200 + i * 96
            L.text((PX, y), v, 30, LIME, "SemiBold", b)
            L.text((PX + 270, y), fact, 30, FG, "Medium", b)
            L.text((PX + 270, y + 40), f"best of {n} candidate facts", 20, LOW, "mono", b)
            d.rounded_rectangle([PX + 720, y + 12, PX + 980, y + 24], 6, fill=rgba((255, 255, 255), 0.08 * b))
            bw = 260 * p * out5((t - t0 - 0.9 - i * 0.22) / 1.1)
            if bw > 2:
                d.rounded_rectangle([PX + 720, y + 12, PX + 720 + bw, y + 24], 6, fill=rgba(LIME, b))
            L.text((PX + 1060, y), f"{p * 100:.1f}%", 28, FG, "mono", b, anchor="ra")
    elif name == "kb":
        head(L, "04 · KNOWLEDGE BASE", "Checked against what's on file", t, t0)
        a = out5((t - t0 - 0.3) / 0.6)
        d.line([(PX + 4, PY + 186), (PX + 22, PY + 204), (PX + 52, PY + 164)], fill=rgba(GREEN, a), width=7, joint="curve")
        L.text((PX + 70, PY + 160), "No correction needed: every value fits its fact.", 34, FG, "Medium", a)
        L.text((PX + 70, PY + 214), "A value that exactly matches another fact on this date would be moved there.", 24, MID, "Regular", a)
    elif name == "truth":
        head(L, "05 · TRUTH ENGINE", "Each fact against its timeline", t, t0)
        for i, (fact, ok, ev) in enumerate(TRUTH):
            b = out5((t - t0 - 0.4 - i * 0.45) / 0.6)
            y = PY + 140 + i * 74
            L.text((PX, y), fact, 32, FG, "SemiBold", b)
            pill = "HOLDS" if ok else "NEVER TRUE"
            pc = GREEN if ok else RED
            pw = tw(pill, 22, "Bold") + 28
            d.rounded_rectangle([PX + 380, y + 2, PX + 380 + pw, y + 38], 18, fill=rgba(pc, 0.18 * b), outline=rgba(pc, b), width=2)
            L.text((PX + 394, y + 9), pill, 22, pc, "Bold", b)
            L.text((PX + 400 + pw, y + 9), ev, 22, MID, "mono", b)
        # the attendees' timeline: everything ever said about it
        c = out5((t - t0 - 2.4) / 0.8)
        if c > 0:
            x0, x1, yb = PX, PX + 1060, PY + 470
            lanes = {1200: yb + 40, 3000: yb + 120}
            import datetime as dt
            day = lambda s: (dt.date.fromisoformat(s) - dt.date(2026, 3, 1)).days  # noqa: E731
            X = lambda s: x0 + 150 + (x1 - x0 - 170) * day(s) / 245  # noqa: E731
            L.text((x0, yb - 6), "ATTENDEES, EVERY MENTION IN THE ARCHIVE", 20, LOW, "mono", c)
            for v, y in lanes.items():
                L.text((x0, y - 14), f"{v:,}", 26, MID, "Medium", c)
                d.line([(x0 + 140, y), (x1, y)], fill=rgba((255, 255, 255), 0.07 * c), width=2)
            line = out5((t - t0 - 2.8) / 1.0)
            if line > 0:
                xa, xb = X("2026-03-24"), X("2026-09-17") + 10
                d.line([(xa, lanes[1200]), (xa + (xb - xa) * line, lanes[1200])], fill=rgba(LIME, c), width=5)
            for j, (s, v, seal) in enumerate(ATTENDEES):
                k = out5((t - t0 - 2.9 - j * 0.12) / 0.4)
                col = GREEN if seal > 0 else RED if seal < 0 else (200, 204, 212)
                r = 9 if seal else 6
                x, y = X(s) + j % 2 * 6, lanes[v]
                d.ellipse([x - r * k, y - r * k, x + r * k, y + r * k], fill=rgba(col, c))
            k = out5((t - t0 - 3.6) / 0.6)
            x, y = X("2026-03-30"), lanes[3000]
            d.ellipse([x - 15, y - 15, x + 15, y + 15], outline=rgba(LIME, k), width=4)
            L.text((x + 24, y - 14), "this sentence, 30 Mar", 22, LIME, "mono", k)
            L.text((X("2026-09-17") - 10, y + 22), "the only other “3,000”: labelled false", 20, RED, "mono", k, anchor="ra")
    elif name == "judge":
        head(L, "06 · JUDGE", "The verdict", t, t0)
        a = out5((t - t0 - 0.3) / 0.6)
        x0, x1, y = PX, PX + 1060, PY + 200
        d.rounded_rectangle([x0, y, x1, y + 14], 7, fill=rgba((255, 255, 255), 0.08 * a))
        cx = x0 + (x1 - x0) * 0.6
        d.rounded_rectangle([cx, y, x1, y + 14], 7, fill=rgba(RED, 0.25 * a))
        d.line([(cx, y - 18), (cx, y + 32)], fill=rgba(FG, a), width=2)
        L.text((cx, y - 50), "60% cutoff", 20, MID, "mono", a, anchor="ma")
        L.text((x0, y - 50), "← true", 20, MID, "mono", a)
        L.text((x1, y - 50), "false →", 20, MID, "mono", a, anchor="ra")
        v = P_FALSE * back((t - t0 - 0.6) / 1.4)
        nx = x0 + (x1 - x0) * clamp(v)
        if t - t0 > 0.6:
            d.ellipse([nx - 13, y - 6, nx + 13, y + 20], fill=rgba(LIME, a))
            L.text((nx, y + 30), f"P(false) {v * 100:.1f}%", 24, LIME, "mono", a, anchor="ma")
        b = out5((t - t0 - 2.1) / 0.7)
        for i, (name_, p, col) in enumerate(PROBS):
            L.text((x0 + i * 300, y + 100), name_, 22, MID, "mono", b)
            L.text((x0 + i * 300, y + 130), f"{p * 100:.1f}%", 40, col, "SemiBold", b)
        c = out5((t - t0 - 2.8) / 0.6)
        s = 1 + 0.12 * (1 - c)
        pw, ph = 330 * s, 72 * s
        d.rounded_rectangle([x0, y + 220, x0 + pw, y + 220 + ph], 36, fill=rgba(RED, c))
        L.text((x0 + pw / 2, y + 220 + ph / 2), "FALSE · 89% sure", int(34 * s), (255, 255, 255), "Bold", c, anchor="mm")
        L.text((x0 + 360, y + 230), "Hooly I/O 2026 attendees: this value is never true", 24, MID, "Regular", c)
        L.text((x0 + 360, y + 262), "in the timeline. Confidence calibrated on past mistakes.", 24, MID, "Regular", c)
    elif name == "writer":
        head(L, "07 · WRITER", "The record", t, t0)
        a = out5((t - t0 - 0.3) / 0.6)
        d.rounded_rectangle([PX, PY + 140, PX + 1060, PY + 320], 18, fill=rgba((0, 0, 0), a), outline=rgba((255, 255, 255), 0.1 * a), width=2)
        L.text((PX + 32, PY + 166), "/output/output.csv", 22, LOW, "mono", a)
        L.text((PX + 32, PY + 206), "id,type,text,form,label,confidence", 30, MID, "mono", a)
        n = int(clamp((t - t0 - 0.6) / 1.2) * len(CSV))
        L.text((PX + 32, PY + 250), CSV[:n], 30, LIME, "mono", a)
        if n < len(CSV) and int(t * 4) % 2:
            cx = PX + 32 + F(30, "mono").getlength(CSV[:n])
            d.rectangle([cx + 4, PY + 252, cx + 20, PY + 284], fill=rgba(LIME, a))
        b = out5((t - t0 - 2.0) / 0.6)
        d.line([(PX + 2, PY + 396), (PX + 16, PY + 410), (PX + 40, PY + 380)], fill=rgba(GREEN, b), width=6, joint="curve")
        L.text((PX + 56, PY + 374), "The Docker container wrote the very same line.", 32, FG, "Medium", b)
        L.text((PX + 56, PY + 418), "Trace and container agreed on all 400 labels of this run.", 24, MID, "Regular", b)
    return L


def frame(t: float) -> Image.Image:
    base = Image.new("RGBA", (W, H), BG + (255,))
    # the header: where this comes from, then the sentence, word by word
    L = Layer()
    a = out5((t - 0.2) / 0.7)
    L.text((80, 70), "LIVE · SAMPLE ROW s-20 · PUBLISHED 09:00, 29 OCT 2026 · TRACED THROUGH THE REAL SYSTEM", 22, LIME, "mono", a)
    L.put(base, a, (1 - a) * 16)
    words = TEXT.split(" ")
    x = 80
    for i, w in enumerate(words):
        k = out5((t - 0.6 - i * 0.09) / 0.7)
        if k > 0:
            Lw = Layer()
            Lw.text((x, 118), w, 58, FG, "Bold")
            Lw.put(base, k, (1 - k) * 26, (1 - k) * 8)
        x += F(58, "Bold").getlength(w + " ")
    d = ImageDraw.Draw(base)
    d.line([(80, 230), (W - 80, 230)], fill=(30, 30, 33), width=2)
    # the architecture, left, then the stage in focus, right
    pipeline(base, t, out5((t - 2.4) / 1.0))
    i = stage_at(t)
    if i >= 0:
        s0, name, _ = STAGES[i]
        nxt = STAGES[i + 1][0] if i + 1 < len(STAGES) else END
        enter = out5((t - s0) / 0.7)
        leave = inout((t - (nxt - 0.35)) / 0.35)
        p = panel(name, t, s0)
        p.put(base, enter * (1 - leave), (1 - enter) * 40 - leave * 30, (1 - enter) * 10 + leave * 8)
    if t > END:
        base = Image.blend(base, Image.new("RGBA", (W, H), BG + (255,)), clamp((t - END) / (DUR - END)))
    return base.convert("RGB")


CUES = [(s, "blip", 0.35) for s, _, _ in STAGES] + [(34.6 + i / 15, "key", 0.3) for i in range(len(CSV))] + [(31.0, "seal", 0.5)]
