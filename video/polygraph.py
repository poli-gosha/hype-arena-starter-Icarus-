"""Polygraph: the idea in about three minutes. Team Icarus, Hype or Truth.

Render a preview:   .venv/Scripts/python.exe -m manim -ql polygraph.py S01Court
Render everything:  .venv/Scripts/python.exe render.py          (1080p, joins the scenes)
"""
from characters import MouseJudge
from style import *

STAGES = [("Linker", "who it's about"), ("Reader", "values, by the rules"), ("Attributor", "which fact · trained"),
          ("Truth engine", "timelines × trust"), ("Judge", "true / false / unsure"), ("Claim forge", "1,000 new claims"),
          ("Writer", "the answer table")]


def pipeline(width=13.6):
    """The seven stages as connected boxes; .boxes[i] for each stage."""
    n = len(STAGES)
    gap = 0.26
    bw = (width - gap * (n - 1)) / n
    boxes = VGroup()
    for i, (name, sub) in enumerate(STAGES):
        r = RoundedRectangle(corner_radius=0.12, width=bw, height=1.25, stroke_color=BLUE, stroke_width=3,
                             fill_color=LIME, fill_opacity=0)  # transparent: a highlighted frame must not hide its label
        num = T(f"{i + 1}", 18, LIME, BOLD)
        nm = T(name, 21, INK, BOLD)
        sb = T(sub, 13, DIM)
        if nm.width > bw - 0.2:
            nm.scale_to_fit_width(bw - 0.2)
        if sb.width > bw - 0.16:
            sb.scale_to_fit_width(bw - 0.16)
        VGroup(num, nm, sb).arrange(DOWN, buff=0.1).move_to(r)
        boxes.add(VGroup(r, num, nm, sb))
    boxes.arrange(RIGHT, buff=gap)
    arrows = VGroup(*[Arrow(boxes[i].get_right(), boxes[i + 1].get_left(), buff=0.02, stroke_width=3,
                            color=BLUE, max_tip_length_to_length_ratio=0.5) for i in range(n - 1)])
    g = VGroup(boxes, arrows)
    g.boxes, g.arrows = boxes, arrows
    return g


def light(stage_box, on=True):
    return stage_box[0].animate.set_stroke(LIME if on else BLUE, width=5 if on else 3).set_fill(
        LIME, opacity=0.1 if on else 0)


def chars(t: Text, full: str, phrase: str):
    """The glyphs of `phrase` inside Text `t` (Text has no glyphs for spaces)."""
    flat = full.replace(" ", "")
    i = flat.index(phrase.replace(" ", ""))
    return t[i:i + len(phrase.replace(" ", ""))]


def counter(tracker: ValueTracker, label: str, size=60, color=LIME):
    """A rolling number in Figtree (Manim's own counters need LaTeX)."""
    return always_redraw(lambda: VGroup(T(f"{int(round(tracker.get_value())):,}", size, color, BOLD),
                                        T(label, size // 2, DIM)).arrange(RIGHT, buff=0.25, aligned_edge=DOWN))


def counter_at(tracker, label, corner):
    return always_redraw(lambda: counter_static(tracker, label).to_corner(corner, buff=0.45))


def counter_static(tracker, label):
    return VGroup(T(f"{int(round(tracker.get_value())):,}", 60, LIME, BOLD),
                  T(label, 28, DIM)).arrange(RIGHT, buff=0.25, aligned_edge=DOWN)


class Base(MovingCameraScene):
    def setup(self):
        super().setup()
        self.camera.background_color = BG
        self.cap = None

    def say(self, text, wait=0.0, color=INK, size=32):
        new = caption(text, size=size, color=color)
        if self.cap is None:
            self.play(FadeIn(new, shift=UP * 0.15), run_time=0.6)
        else:
            self.play(FadeOut(self.cap, shift=UP * 0.15), FadeIn(new, shift=UP * 0.15), run_time=0.6)
        self.cap = new
        if wait:
            self.wait(wait)

    def unsay(self):
        if self.cap is not None:
            self.play(FadeOut(self.cap), run_time=0.4)
            self.cap = None


# ---- 1. cold open ------------------------------------------------------------------------
class S01Court(Base):
    def construct(self):
        tag = VGroup(T("HYPE OR TRUTH", 22, LIME, BOLD), T("Team Icarus", 22, DIM)).arrange(RIGHT, buff=0.4)
        tag.to_corner(UL, buff=0.5)
        judge = MouseJudge().scale(0.95).shift(UP * 0.55)
        self.play(FadeIn(tag), FadeIn(judge, shift=UP * 0.3), run_time=1.4)
        judge.blink(self)
        self.say("Hooly is a tech company. For a year, it said a lot.", 2.2)
        self.say("Press releases. Blog posts. Decks. A CEO named Gavin.", 2.4)
        judge.blink(self)
        self.say("Not all of it was true.", 0.6, color=RED, size=38)
        judge.strike(self, 2)
        self.wait(1.4)
        self.unsay()
        self.play(FadeOut(judge), FadeOut(tag), run_time=0.8)


# ---- 2. the case -------------------------------------------------------------------------
SENTENCES = [
    "Hooly AI Pro costs €49 per month.", "Hooly Jules supports 8 languages.", "Gemini kept 98.7% uptime last quarter.",
    "Hooly Cloud covers 3 regions.", "Gavin: Gemini speaks 40 languages.", "Hooly Photos holds 4,900,000,000 photos.",
    "Hooly Chrome 72.0 starts in 1.3 s.", "Holdan started at Hooly on 12 January 2026.", "Hooly Maps works offline.",
    "Hooly Gemini handles 22 formats.", "The Hooly Board meets 4 times a year.", "Hooly Workspace costs €199 per month.",
    "Hooly I/O 2026 took place in Berlin.", "Pixel Fold costs €1,799.", "Hooly Search has 540,000,000 users.",
    "I have been told the trade-in scheme is coming.", "Hooly Cloud has 140 customers.", "Hooly Translate supports 140 languages.",
]
LIES = {4, 9, 14, 15}


class S02Case(Base):
    def construct(self):
        rng = np.random.default_rng(7)
        cards = VGroup()
        for i, s in enumerate(SENTENCES):
            c = card(s, size=19)
            c.rotate(rng.uniform(-0.1, 0.1))
            half = c.width / 2 + 0.3
            c.move_to([rng.uniform(-7.1 + half, 7.1 - half), rng.uniform(-2.3, 2.1), 0])
            cards.add(c)
        self.say("Our system gets about 20,000 of its sentences, one year of pages.", 0)
        self.play(LaggedStart(*[FadeIn(c, shift=rng.uniform(-1, 1, 3) * [1, 1, 0]) for c in cards],
                              lag_ratio=0.12), run_time=4)
        n = ValueTracker(0)
        counter = counter_at(n, "statements", UR)
        self.add(counter)
        self.play(n.animate.set_value(20000), run_time=2)
        self.say("Some are true. Some are hype. Some can't be decided.", 1.0)
        self.play(*[cards[i][0].animate.set_stroke(RED, width=4) for i in LIES],
                  *[cards[i][1].animate.set_color(RED) for i in LIES], run_time=1)
        self.wait(1.5)
        rules = VGroup(*[T(r, 28, c) for r, c in [
            ("Label every sentence: true · false · unsure, with a confidence", INK),
            ("Write 1,000 new claims, every one true", INK),
            ("No LLM at run time · offline · 2 CPUs · 30 minutes", LIME)]]).arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        panel = VGroup(SurroundingRectangle(rules, buff=0.4, color=SLATE, fill_color=CARD, fill_opacity=0.97,
                                            corner_radius=0.15), rules).move_to(UP * 0.4)
        self.say("The task, by QA DNA:", 0)
        self.play(cards.animate.set_opacity(0.25), FadeIn(panel, scale=0.96), run_time=1)
        self.wait(4.5)
        self.unsay()
        self.play(FadeOut(VGroup(cards, panel, counter)), run_time=0.8)


# ---- 3. into the judge's brain ---------------------------------------------------------
class S03IntoBrain(Base):
    def construct(self):
        judge = MouseJudge().scale(0.95).shift(UP * 0.55)
        self.add(judge)
        self.say("So we built a judge. Let's look inside its head.", 1.2)
        self.unsay()
        frame = self.camera.frame
        frame.save_state()
        brain = judge.head.get_center() + UP * 0.2
        self.play(frame.animate.scale(0.22).move_to(brain), run_time=2.2, rate_func=smooth)
        pipe = pipeline().scale(0.22 * 0.95).move_to(brain)
        self.play(FadeOut(judge), FadeIn(pipe), run_time=1.2)
        self.play(Restore(frame), pipe.animate.scale(1 / (0.22 * 0.95)).move_to(UP * 0.6), run_time=2.2)
        self.say("Seven stages. No neural network, no LLM:", 0)
        self.play(LaggedStart(*[Indicate(b[0], color=LIME, scale_factor=1.06) for b in pipe.boxes], lag_ratio=0.25),
                  run_time=3)
        self.say("rules, timelines, and two small models trained on the practice data.", 3.4)
        self.unsay()
        self.play(FadeOut(pipe), run_time=0.8)


# ---- 4. exhibit A, dissected -------------------------------------------------------------
EXHIBIT = "Hooly Jules works in 8 languages."


class S04Dissect(Base):
    def construct(self):
        pipe = pipeline().scale(0.62).to_edge(UP, buff=0.35)
        self.add(pipe)
        label = T("EXHIBIT A", 20, LIME, BOLD)
        sent = T(EXHIBIT, 46)
        date = T("page dated 8 September 2026", 22, DIM)
        ex = VGroup(label, sent).arrange(DOWN, buff=0.22).move_to(UP * 0.75)
        date.next_to(sent, DOWN, buff=0.95)
        ex.add(date)
        self.say("A sentence comes in.", 0)
        self.play(FadeIn(ex, shift=UP * 0.2), run_time=1)
        self.wait(1)
        # 1 linker
        self.play(light(pipe.boxes[0]), run_time=0.4)
        subj = chars(sent, EXHIBIT, "Hooly Jules")
        u1 = Underline(subj, color=BLUE, stroke_width=5)
        t1 = T("SUBJECT", 20, BLUE, BOLD).next_to(u1, DOWN, buff=0.15)
        self.say("The linker finds who it's about, from Hooly's own list of names.", 0)
        self.play(Create(u1), FadeIn(t1), run_time=0.8)
        self.wait(1.4)
        # 2 reader
        self.play(light(pipe.boxes[0], False), light(pipe.boxes[1]), run_time=0.4)
        val = chars(sent, EXHIBIT, "8 languages")
        b2 = SurroundingRectangle(val, color=LIME, buff=0.08, corner_radius=0.06)
        t2 = T("VALUE: 8 × language", 20, LIME, BOLD).next_to(b2, DOWN, buff=0.15)
        self.say("The reader reads the value by the referee's published rules.", 0)
        self.play(Create(b2), FadeIn(t2), run_time=0.8)
        self.wait(1.6)
        # 3 attributor
        self.play(light(pipe.boxes[1], False), light(pipe.boxes[2]), run_time=0.4)
        cands = VGroup(*[VGroup(T(a, 24, c), T(p, 24, c, BOLD)).arrange(RIGHT, buff=0.5) for a, p, c in [
            ("programming languages", "0.92", LIME), ("offline languages", "0.04", DIM), ("IDEs supported", "0.01", DIM)]])
        for row in cands:
            row[1].align_to(cands[0][1], RIGHT) if False else None
        cands.arrange(DOWN, buff=0.18, aligned_edge=LEFT).move_to(DOWN * 2.05 + RIGHT * 3.0)
        head = T("which fact is it?", 20, DIM).next_to(cands, UP, buff=0.2, aligned_edge=LEFT)
        self.say("A model trained on 2,400 labelled facts picks which fact it is.", 0)
        self.play(FadeIn(head), LaggedStart(*[FadeIn(r, shift=LEFT * 0.2) for r in cands], lag_ratio=0.3), run_time=1.4)
        self.play(Circumscribe(cands[0], color=LIME), run_time=1)
        self.wait(1.2)
        # the fact
        fact = VGroup(*[card(x, size=24, stroke=c) for x, c in [
            ("Hooly Jules", BLUE), ("programming languages", LIME), ("8 languages", LIME), ("8 Sep 2026", DIM)]])
        fact.arrange(RIGHT, buff=0.25).move_to(DOWN * 1.85)
        self.play(light(pipe.boxes[2], False), FadeOut(VGroup(cands, head)), run_time=0.5)
        self.say("Every sentence becomes facts: who, what, which value, on which date.", 0)
        self.play(TransformFromCopy(VGroup(subj, val), fact), run_time=1.4)
        self.wait(2.6)
        self.unsay()
        self.play(FadeOut(VGroup(ex, u1, t1, b2, t2, fact, pipe)), run_time=0.8)


# ---- 5. the truth engine -----------------------------------------------------------------
MONTHS = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]


def month_x(date: str) -> float:
    y, m, d = (int(p) for p in date.split("-"))
    return (y - 2025) * 12 + (m - 10) + (d - 1) / 30


# real mentions of Hooly Jules' programming languages in the practice data
JULES = [("2026-04-15", 3, "false"), ("2026-04-17", 1, "true"), ("2026-04-20", 1, "true"), ("2026-05-12", 1, "true"),
         ("2026-06-02", 1, "true"), ("2026-06-03", 1, "true"), ("2026-08-18", 2, "true"), ("2026-08-19", 2, "true"),
         ("2026-08-21", 2, "true"), ("2026-09-08", 1, "exhibit"), ("2026-09-20", 2, "true"), ("2026-10-26", 1, "false")]
LEVELS = {1: "8 languages", 2: "14 languages", 3: "40 languages"}


def timeline_axes():
    ax = Axes(x_range=[0, 13.2, 1], y_range=[0, 3.6, 1], x_length=10.5, y_length=4.1,
              axis_config={"color": SLATE, "stroke_width": 2, "include_ticks": False}, tips=False)
    xl = VGroup(*[T(MONTHS[i], 16, DIM).next_to(ax.c2p(i, 0), DOWN, buff=0.18) for i in range(0, 14, 2)])
    yl = VGroup(*[T(LEVELS[k], 18, DIM).next_to(ax.c2p(0, k), LEFT, buff=0.2) for k in LEVELS])
    grid = VGroup(*[DashedLine(ax.c2p(0, k), ax.c2p(13.2, k), color=SLATE, stroke_width=1, dash_length=0.08)
                    for k in LEVELS])
    return ax, VGroup(ax, xl, yl, grid)


class S05Truth(Base):
    def construct(self):
        title = T("TRUTH ENGINE · Hooly Jules · programming languages", 24, LIME, BOLD).to_edge(UP, buff=0.4)
        ax, chart = timeline_axes()
        chart.shift(DOWN * 0.2 + RIGHT * 0.6)
        self.play(FadeIn(title), Create(chart), run_time=1.2)
        self.say("Every other page that mentions this fact drops onto its timeline.", 0)
        dots = VGroup()
        for d, lvl, kind in JULES:
            dot = Dot(ax.c2p(month_x(d), lvl), radius=0.09, color=INK if kind != "exhibit" else BLUE)
            if kind == "exhibit":
                dot = VGroup(dot, Circle(radius=0.2, color=BLUE, stroke_width=4).move_to(dot))
            dots.add(dot)
        self.play(LaggedStart(*[FadeIn(d, scale=2) for d in dots], lag_ratio=0.18), run_time=3)
        self.wait(0.8)
        # page trust
        self.say("Pages earn trust. A rumour page counts less than a release note.", 0)
        rumour = card("rumour page · trust 0.31", size=18, stroke=RED, color=RED)
        rumour.next_to(dots[0], LEFT, buff=0.35)
        self.play(FadeIn(rumour), dots[0].animate.set_opacity(0.35), run_time=1)
        self.wait(1.8)
        # staircase
        self.say("The engine fits the most likely staircase through them.", 0)
        x0, x1, x2 = month_x("2026-04-17"), month_x("2026-08-15"), 13.0
        stairs = VMobject(color=LIME, stroke_width=6).set_points_as_corners(
            [ax.c2p(x0, 1), ax.c2p(x1, 1), ax.c2p(x1, 2), ax.c2p(x2, 2)])
        self.play(Create(stairs), run_time=2.4)
        out = T("outvoted", 18, RED).next_to(dots[0], UP, buff=0.12)
        self.play(dots[0].animate.set_color(RED), FadeIn(out), run_time=0.6)
        self.say("A lone wrong value is outvoted; a real change, repeated later, becomes a new step.", 3.2)
        # the maths
        self.unsay()
        frame = self.camera.frame
        frame.save_state()
        math = VGroup(
            T("find the timeline that minimises", 24, DIM),
            T("Σ  trust(page) × [ mention ≠ timeline ]  +  λ · (number of changes)", 30, INK, font=SYMBOLS),
            T("exact, by dynamic programming · one fact at a time", 22, LIME),
            T("then page trust is re-estimated from the timelines, and it repeats", 22, DIM),
        ).arrange(DOWN, buff=0.28)
        panel = VGroup(SurroundingRectangle(math, buff=0.35, color=BLUE, fill_color="#0E1424", fill_opacity=0.97,
                                            corner_radius=0.12), math).move_to(DOWN * 4.4)
        self.add(panel)
        self.play(frame.animate.move_to(panel).set(width=panel.width * 1.25), run_time=1.6)
        self.wait(5.2)
        self.play(Restore(frame), run_time=1.4)
        self.remove(panel)
        self.wait(0.5)
        self.unsay()
        self.play(FadeOut(VGroup(title, chart, rumour, out)), FadeOut(dots[0]), run_time=0.6)
        # keep the chart pieces for the verdict scene: it re-draws the same picture


# ---- 6. exhibit A's verdict --------------------------------------------------------------
class S06Verdict(Base):
    def construct(self):
        ax, chart = timeline_axes()
        chart.shift(DOWN * 0.2 + RIGHT * 0.6)
        x0, x1, x2 = month_x("2026-04-17"), month_x("2026-08-15"), 13.0
        stairs = VMobject(color=LIME, stroke_width=6).set_points_as_corners(
            [ax.c2p(x0, 1), ax.c2p(x1, 1), ax.c2p(x1, 2), ax.c2p(x2, 2)])
        dots = VGroup(*[Dot(ax.c2p(month_x(d), lvl), radius=0.09, color=INK) for d, lvl, k in JULES[1:] if k != "exhibit"])
        exd = Dot(ax.c2p(month_x("2026-09-08"), 1), radius=0.11, color=BLUE)
        ring = Circle(radius=0.22, color=BLUE, stroke_width=4).move_to(exd)
        self.add(chart, stairs, dots, exd, ring)
        ex = card(EXHIBIT + "   · 8 Sep 2026", size=24, stroke=BLUE).to_edge(UP, buff=0.4)
        self.play(FadeIn(ex), run_time=0.6)
        arrow = Arrow(ex.get_bottom(), ring.get_top(), buff=0.1, color=BLUE, stroke_width=4)
        self.play(GrowArrow(arrow), Flash(exd, color=BLUE), run_time=0.8)
        self.say("Exhibit A says 8 languages. On its date, the timeline says 14.", 2.2)
        s = stamp("FALSE", RED, 64).move_to(ax.c2p(2.6, 2.7))
        why = T("stale · true before, not on its date · 97% sure", 22, RED).next_to(s, DOWN, buff=0.3)
        why.align_to(ax.c2p(0.3, 0), LEFT)
        self.play(FadeIn(s, scale=1.6), run_time=0.35)
        self.play(FadeIn(why), run_time=0.6)
        self.wait(2.4)
        self.unsay()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)


# ---- 7. the three shapes of a lie --------------------------------------------------------
class S07Shapes(Base):
    def construct(self):
        title = T("A lie has one of three shapes", 34, INK, BOLD).to_edge(UP, buff=0.45)
        self.play(FadeIn(title), run_time=0.7)
        panels = VGroup()
        specs = [
            ("INVENTED", "never true", "Gavin: Gemini speaks 40 languages.", [(0.5, 1), (4.0, 1), (4.0, 2), (9.5, 2)], (6.2, 3.1)),
            ("STALE", "true before, not on its date", "Hooly Jules works in 8 languages.", [(0.5, 1), (5.0, 1), (5.0, 2), (9.5, 2)], (7.4, 1)),
            ("PREMATURE", "true only later", "Hooly Gemini handles 22 formats.", [(0.5, 1), (6.0, 1), (6.0, 2), (9.5, 2)], (2.6, 2)),
        ]
        for name, gist, example, pts, dot in specs:
            ax = Axes(x_range=[0, 10, 1], y_range=[0, 3.5, 1], x_length=3.9, y_length=2.9, tips=False,
                      axis_config={"color": SLATE, "stroke_width": 2, "include_ticks": False})
            st = VMobject(color=LIME, stroke_width=5).set_points_as_corners([ax.c2p(*p) for p in pts])
            dd = Dot(ax.c2p(*dot), radius=0.11, color=RED)
            ring = Circle(radius=0.2, color=RED, stroke_width=3).move_to(dd)
            head = T(name, 32, RED, BOLD)
            g = T(gist, 22, DIM)
            ex = T(f"“{example}”", 19, INK)
            if ex.width > 4.1:
                ex.scale_to_fit_width(4.1)
            panels.add(VGroup(head, g, VGroup(ax, st, dd, ring), ex).arrange(DOWN, buff=0.25))
        panels.arrange(RIGHT, buff=0.55).move_to(DOWN * 0.05)
        self.say("Red dot: the sentence. Green staircase: the truth over time.", 0)
        for p in panels:
            self.play(FadeIn(p[0:2], shift=DOWN * 0.15), Create(p[2][0]), run_time=0.7)
            self.play(Create(p[2][1]), run_time=0.8)
            self.play(FadeIn(p[2][2], scale=2), Create(p[2][3]), FadeIn(p[3]), run_time=0.8)
            self.wait(1.4)
        shares = VGroup(*[T(s, 22, LIME, BOLD).next_to(p, DOWN, buff=0.3) for s, p in
                          zip(["42% of the lies", "29% of the lies", "17% of the lies"], panels)])
        self.say("In the practice data, these shapes cover almost nine lies in ten.", 0)
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.1) for s in shares], lag_ratio=0.3), run_time=1.2)
        self.wait(3.2)
        self.say("And it says which shape, so a human can check every verdict.", 3.6)
        self.unsay()
        self.play(FadeOut(VGroup(title, panels, shares)), run_time=0.7)


# ---- 8. the judge ------------------------------------------------------------------------
def tree_icon(color=BLUE, s=1.0):
    pts = {"r": [0, 0.8, 0], "a": [-0.5, 0.1, 0], "b": [0.5, 0.1, 0], "c": [-0.8, -0.6, 0], "d": [-0.2, -0.6, 0],
           "e": [0.2, -0.6, 0], "f": [0.8, -0.6, 0]}
    edges = [("r", "a"), ("r", "b"), ("a", "c"), ("a", "d"), ("b", "e"), ("b", "f")]
    g = VGroup(*[Line(pts[u], pts[v], color=color, stroke_width=3) for u, v in edges],
               *[Dot(p, radius=0.08, color=LIME if k in "cdef" else color) for k, p in pts.items()])
    return g.scale(s)


class S08Judge(Base):
    def construct(self):
        title = T("JUDGE", 28, LIME, BOLD).to_edge(UP, buff=0.45)
        self.play(FadeIn(title), run_time=0.5)
        ev = VGroup(*[card(e, size=20, stroke=SLATE) for e in [
            "timeline: stale", "pages agreeing: 4 of 5", "page trust: 0.82", "a confirmed row nearby disagrees",
            "wording: no hedges", "speaker: none"]]).arrange(DOWN, buff=0.18, aligned_edge=LEFT).to_edge(LEFT, buff=0.6)
        forest = VGroup(*[tree_icon(s=0.5) for _ in range(5)]).arrange_in_grid(2, 3, buff=0.35).move_to(LEFT * 0.2 + UP * 0.3)
        bars = VGroup()
        for name, p, c in [("TRUE", 0.03, LIME), ("FALSE", 0.97, RED), ("UNSURE", 0.00, AMBER)]:
            lab = T(name, 22, c, BOLD)
            bar = Rectangle(width=max(0.04, 2.6 * p), height=0.32, fill_color=c, fill_opacity=1, stroke_width=0)
            val = T(f"{p:.2f}", 20, c)
            bars.add(VGroup(lab, bar, val).arrange(RIGHT, buff=0.25))
        bars.arrange(DOWN, buff=0.3, aligned_edge=LEFT).to_edge(RIGHT, buff=0.6).shift(UP * 0.3)
        x_bar = max(b[0].get_right()[0] for b in bars) + 0.25
        for b in bars:
            b[1].align_to([x_bar, 0, 0], LEFT)
            b[2].next_to(b[1], RIGHT, buff=0.2)
        self.say("The judge weighs the evidence about Exhibit A,", 0)
        self.play(LaggedStart(*[FadeIn(e, shift=RIGHT * 0.2) for e in ev], lag_ratio=0.2), run_time=2)
        self.say("with a forest of decision trees trained on 1,900 labelled rows.", 0)
        self.play(LaggedStart(*[Create(t) for t in forest], lag_ratio=0.15), run_time=1.6)
        flows = VGroup(*[Arrow(e.get_right(), forest.get_left(), buff=0.15, color=SLATE, stroke_width=2,
                               max_tip_length_to_length_ratio=0.08) for e in ev])
        self.play(LaggedStart(*[GrowArrow(f) for f in flows], lag_ratio=0.1), run_time=1)
        self.play(LaggedStart(*[Indicate(t, color=LIME, scale_factor=1.08) for t in forest], lag_ratio=0.12), run_time=1.2)
        self.play(FadeIn(bars, shift=LEFT * 0.2), run_time=0.8)
        self.wait(1.4)
        self.say("Trained fairly: no row ever sees its own label.", 3)
        loop = CurvedArrow(bars.get_bottom() + DOWN * 0.2, forest.get_bottom() + DOWN * 0.3, angle=-TAU / 4, color=LIME)
        lt = T("confident verdicts → weak evidence for other rows → judge again", 20, LIME).next_to(loop, DOWN, buff=0.1)
        lt.set_x(0)
        self.say("Then confident verdicts sharpen the other timelines, and it judges again.", 0)
        self.play(Create(loop), FadeIn(lt), run_time=1.2)
        self.wait(2.6)
        self.unsay()
        self.play(FadeOut(VGroup(title, ev, forest, flows, bars, loop, lt)), run_time=0.7)


# ---- 9. the claim forge ------------------------------------------------------------------
CLAIMS = [("FACT", "Hooly Cloud has 8 regions."), ("COMPARE", "Hooly Workspace costs more than Hooly AI Pro."),
          ("CHANGE", "Hooly Jules went from 8 languages to 14 languages."),
          ("AT EVENT", "Hooly Cloud had 5 regions at the May 2026 outage."),
          ("RELATION", "The CTO of Hooly joined on 1 July 2026.")]


class S09Forge(Base):
    def construct(self):
        title = T("CLAIM FORGE", 28, LIME, BOLD).to_edge(UP, buff=0.45)
        self.play(FadeIn(title), run_time=0.5)
        self.say("The second job: write 1,000 new claims, every one true.", 0)
        rows = VGroup()
        for typ, text in CLAIMS:
            tag = T(typ, 18, BLUE, BOLD)
            c = card(text, size=24, stroke=SLATE)
            rows.add(VGroup(tag, c).arrange(RIGHT, buff=0.35))
        for r in rows[1:]:
            r[0].align_to(rows[0][0], LEFT)
        rows.arrange(DOWN, buff=0.28, aligned_edge=LEFT).move_to(LEFT * 0.9 + DOWN * 0.05)
        n = ValueTracker(0)
        counter = counter_at(n, "claims", UR)
        self.add(counter)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.3) for r in rows], lag_ratio=0.35),
                  n.animate.set_value(1000), run_time=4)
        self.say("Only from timeline steps that confirmed rows back up.", 2.4)
        checks = VGroup(*[VGroup(T("✓", 24, LIME, font=SYMBOLS), T("reads back", 20, LIME, BOLD)).arrange(
            RIGHT, buff=0.1).next_to(r, RIGHT, buff=0.3) for r in rows])
        self.say("Our copy of the referee reads each one back; anything it rejects never ships.", 0)
        self.play(LaggedStart(*[FadeIn(c, scale=1.4) for c in checks], lag_ratio=0.25), run_time=1.8)
        self.wait(2.6)
        self.unsay()
        self.play(FadeOut(VGroup(title, rows, checks, counter)), run_time=0.7)


# ---- 10. the numbers ---------------------------------------------------------------------
class S10Numbers(Base):
    def construct(self):
        title = T("Measured on held-out practice data", 26, DIM).to_edge(UP, buff=0.5)
        stats = [("0.879", "label accuracy", "vs 0.833 for “everything is true”"),
                 ("986 / 1,000", "claims verified true", "0 rejected by the referee clone"),
                 ("3.5 min", "for 20,000 rows", "of 30 allowed · 0.8 GiB of 6"),
                 ("0", "LLMs at run time", "every verdict comes with its reason")]
        tiles = VGroup()
        for big, what, note in stats:
            b = T(big, 54, LIME, BOLD)
            w = T(what, 24, INK)
            n = T(note, 18, DIM)
            inner = VGroup(b, w, n).arrange(DOWN, buff=0.14)
            box = RoundedRectangle(corner_radius=0.16, width=6.1, height=2.1, stroke_color=SLATE, stroke_width=2,
                                   fill_color=CARD, fill_opacity=1)
            inner.move_to(box)
            tiles.add(VGroup(box, inner))
        tiles.arrange_in_grid(2, 2, buff=0.35).move_to(DOWN * 0.25)
        self.play(FadeIn(title), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.2) for t in tiles], lag_ratio=0.45), run_time=3.2)
        self.wait(6)
        self.play(FadeOut(VGroup(title, tiles)), run_time=0.7)


# ---- 11. back to court -------------------------------------------------------------------
class S11Finale(Base):
    def construct(self):
        pipe = pipeline().move_to(UP * 0.6)
        self.add(pipe)
        judge = MouseJudge().scale(0.95).shift(UP * 0.55)
        brain = judge.head.get_center() + UP * 0.2
        frame = self.camera.frame
        frame.save_state()
        self.say("All of that, in about four seconds per sample row...", 1.0)
        self.unsay()
        self.play(pipe.animate.scale(0.22 * 0.95).move_to(brain), frame.animate.scale(0.22).move_to(brain), run_time=2)
        self.play(FadeIn(judge), FadeOut(pipe), run_time=1)
        self.play(Restore(frame), run_time=1.8)
        ex = card(EXHIBIT, size=22, stroke=BLUE).to_corner(UL, buff=0.6)
        self.play(FadeIn(ex, shift=RIGHT * 0.3), run_time=0.6)
        judge.strike(self, 1)
        s = stamp("FALSE", RED, 56).next_to(ex, DOWN, buff=0.3)
        self.play(FadeIn(s, scale=1.8), run_time=0.3)
        self.wait(1.4)
        self.play(FadeOut(VGroup(judge, ex, s)), run_time=0.8)
        end = VGroup(T("POLYGRAPH", 72, LIME, BOLD), T("Every verdict comes with its evidence.", 32, INK),
                     T("Team Icarus · Hype or Truth · NEXXT AI Hackathon 2026", 22, DIM)).arrange(DOWN, buff=0.35)
        self.play(FadeIn(end[0], scale=0.9), run_time=1)
        self.play(FadeIn(end[1:], shift=UP * 0.15), run_time=0.8)
        self.wait(3)
