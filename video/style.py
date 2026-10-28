"""Shared look for the Polygraph explainer: QA DNA's palette and Figtree."""
from pathlib import Path

import manimpango
from manim import *  # noqa: F401,F403

manimpango.register_font(str(Path(__file__).parent / "fonts" / "Figtree.ttf"))

# QA DNA (hype-arena.vercel.app): near-black, bone white, lime, slate, blue
BG = "#0A0A0A"
INK = "#FCFCFC"
LIME = "#D7F13B"      # truth
SLATE = "#3D4350"
BLUE = "#2859B5"      # the machine
RED = "#FF4D5E"       # lies
AMBER = "#FFB020"     # unsure
DIM = "#8A90A0"
CARD = "#15171C"
FONT = "Figtree"


SYMBOLS = "Segoe UI Symbol"  # Figtree has no Σ, ≠, λ or ✓


def T(text, size=36, color=INK, weight=NORMAL, font=FONT, **kw):
    """Text in Figtree (or another font for symbols)."""
    return Text(text, font=font, font_size=size, color=color, weight=weight, **kw)


def caption(text, size=34, color=INK):
    """A caption bar at the bottom of the frame."""
    t = T(text, size=size, color=color)
    if t.width > 13.0:  # never run off the frame
        t.scale_to_fit_width(13.0)
    t.to_edge(DOWN, buff=0.55)
    return t


def card(text, width=None, size=26, stroke=SLATE, color=INK, pad=0.28):
    """A statement on a dark card."""
    t = T(text, size=size, color=color)
    w = width or t.width + 2 * pad
    box = RoundedRectangle(corner_radius=0.14, width=w, height=t.height + 2 * pad,
                           stroke_color=stroke, stroke_width=2, fill_color=CARD, fill_opacity=1)
    t.move_to(box)
    return VGroup(box, t)


def stamp(word, color, size=60):
    """A rubber-stamp verdict."""
    t = T(word, size=size, color=color, weight=BOLD)
    box = SurroundingRectangle(t, buff=0.18, color=color, stroke_width=6, corner_radius=0.08)
    return VGroup(box, t).rotate(-6 * DEGREES)
