"""The mouse judge, drawn from shapes so its parts can move."""
from style import *

FUR = "#B8BDC8"
FUR_DARK = "#8E94A1"
PINK = "#EBA3B5"
WIG = "#F2F0EA"
WIG_LINE = "#B9B4A8"
ROBE = "#121318"
WOOD = "#7A4E2A"
WOOD_DARK = "#5A381D"


def _curl(r=0.2):
    c = Circle(radius=r, fill_color=WIG, fill_opacity=1, stroke_color=WIG_LINE, stroke_width=2)
    swirl = Arc(radius=r * 0.55, start_angle=0.3, angle=4.2, color=WIG_LINE, stroke_width=2).move_to(c)
    return VGroup(c, swirl)


class MouseJudge(VGroup):
    """parts: .body .head .brain_center .gavel (rotate about .gavel_pivot) .eyes"""

    def __init__(self, **kw):
        super().__init__(**kw)
        # robe and collar
        robe = Polygon([-1.55, -2.6, 0], [1.55, -2.6, 0], [1.05, -0.95, 0], [-1.05, -0.95, 0],
                       fill_color=ROBE, fill_opacity=1, stroke_color=SLATE, stroke_width=2)
        jabot = VGroup(*[Polygon([-0.22, 0, 0], [0.22, 0, 0], [0, -0.32, 0], fill_color=WIG, fill_opacity=1,
                                 stroke_color=WIG_LINE, stroke_width=1.5).shift(DOWN * 0.18 * i)
                         for i in range(2)]).move_to([0, -1.25, 0])
        # ears behind the head
        ears = VGroup()
        for side in (-1, 1):
            outer = Circle(radius=0.62, fill_color=FUR, fill_opacity=1, stroke_color=FUR_DARK, stroke_width=2)
            inner = Circle(radius=0.38, fill_color=PINK, fill_opacity=1, stroke_width=0)
            ears.add(VGroup(outer, inner).move_to([side * 0.95, 0.85, 0]))
        # wig: curls over the top and down both sides
        wig = VGroup()
        for i in range(9):
            a = PI * (0.12 + 0.76 * i / 8)
            wig.add(_curl(0.24).move_to([1.02 * np.cos(a), 0.15 + 0.95 * np.sin(a), 0]))
        for side in (-1, 1):
            for j in range(4):
                wig.add(_curl(0.22).move_to([side * (1.08 + 0.04 * j), -0.15 - 0.36 * j, 0]))
        head = Ellipse(width=2.05, height=1.85, fill_color=FUR, fill_opacity=1, stroke_color=FUR_DARK, stroke_width=2)
        snout = Ellipse(width=0.95, height=0.62, fill_color="#D3D7DF", fill_opacity=1, stroke_width=0).move_to([0, -0.42, 0])
        eyes = VGroup()
        for side in (-1, 1):
            e = Ellipse(width=0.24, height=0.3, fill_color="#0B0C10", fill_opacity=1, stroke_width=0).move_to([side * 0.38, 0.05, 0])
            glint = Circle(radius=0.045, fill_color=WHITE, fill_opacity=1, stroke_width=0).move_to(e.get_center() + [0.05, 0.07, 0])
            eyes.add(VGroup(e, glint))
        nose = Ellipse(width=0.2, height=0.15, fill_color=PINK, fill_opacity=1, stroke_width=0).move_to([0, -0.27, 0])
        mouth = Arc(radius=0.12, start_angle=-PI * 0.85, angle=PI * 0.7, color=FUR_DARK, stroke_width=2.5).move_to([0, -0.5, 0])
        whiskers = VGroup()
        for side in (-1, 1):
            for dy in (-0.05, 0.06):
                whiskers.add(Line([side * 0.3, -0.38, 0], [side * 1.15, -0.32 + dy * 2.2, 0],
                                  color=FUR_DARK, stroke_width=1.6))
        self.head = VGroup(ears, head, wig, snout, eyes, nose, mouth, whiskers)
        self.eyes = eyes
        self.brain_center = head.get_center() + UP * 0.25
        # bench in front, with a name plate
        bench = Rectangle(width=4.6, height=1.3, fill_color=SLATE, fill_opacity=1, stroke_color="#565D6D",
                          stroke_width=2).move_to([0, -2.25, 0])
        plate = VGroup(RoundedRectangle(corner_radius=0.06, width=2.4, height=0.42, fill_color=CARD,
                                        fill_opacity=1, stroke_color=LIME, stroke_width=1.5),
                       T("JUDGE POLYGRAPH", 17, LIME, BOLD)).move_to(bench.get_center() + UP * 0.12)
        plate[1].move_to(plate[0])
        # gavel resting on the bench, right paw side
        handle = Rectangle(width=1.25, height=0.13, fill_color=WOOD, fill_opacity=1, stroke_width=0)
        mallet = RoundedRectangle(corner_radius=0.05, width=0.36, height=0.55, fill_color=WOOD, fill_opacity=1,
                                  stroke_color=WOOD_DARK, stroke_width=2).move_to(handle.get_right() + RIGHT * 0.1)
        self.gavel = VGroup(handle, mallet).move_to([1.6, -1.25, 0]).rotate(25 * DEGREES)
        self.gavel_pivot = handle.get_left()
        block = RoundedRectangle(corner_radius=0.05, width=0.8, height=0.18, fill_color=WOOD_DARK,
                                 fill_opacity=1, stroke_width=0).move_to([2.05, -1.55, 0])
        self.body = VGroup(robe, jabot)
        self.add(self.body, self.head, bench, plate, block, self.gavel)

    def strike(self, scene, times=2):
        """The gavel comes down."""
        for _ in range(times):
            scene.play(Rotate(self.gavel, angle=-40 * DEGREES, about_point=self.gavel_pivot,
                              rate_func=there_and_back), run_time=0.35)

    def blink(self, scene):
        scene.play(self.eyes.animate.stretch(0.1, 1), run_time=0.08)
        scene.play(self.eyes.animate.stretch(10, 1), run_time=0.08)
