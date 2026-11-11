"""Gradient descent on f(x) = x², in Manim Community with the skill's kit (manim_ce_kit.py)."""
import sys
from pathlib import Path

from manim import (DOWN, UP, Axes, Create, Dot, FadeIn, TransformMatchingTex, ValueTracker, Write,
                   always_redraw)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))
import manim_ce_kit as K  # noqa: E402


class GradientDescent(K.Explainer):
    narration = HERE / "narration.py"

    def construct(self):
        S = K.S
        self.section("gd1")
        name = K.T("gradient descent", 44, S.fg).to_edge(UP, buff=1.3)
        axes = Axes(x_range=[-3, 3, 1], y_range=[0, 9, 3], x_length=7, y_length=4.2,
                    axis_config={"color": S.fg}).shift(DOWN * 1.1 + 2.6 * K.mn.LEFT)
        curve = axes.plot(lambda x: x**2, color=S.ink, stroke_width=5)
        self.beat("gd1", 0, Write(name))
        self.beat("gd1", 1, Create(axes), Create(curve))
        x = ValueTracker(2.6)
        dot = always_redraw(lambda: Dot(axes.c2p(x.get_value(), x.get_value() ** 2), radius=0.12, color=S.accent))
        self.add(dot)

        rule = K.M(r"x \leftarrow x - \eta\, f'(x)", 50).move_to(3.6 * K.mn.RIGHT + 0.9 * UP)
        self.beat("gd2", 0, x.animate.set_value(2.2))
        self.beat("gd2", 1, Write(rule))
        deriv = K.M(r"f'(x) = 2x", 44, S.dim).next_to(rule, DOWN, buff=0.5)
        self.beat("gd2", 2, FadeIn(deriv))

        simple = K.M(r"x \leftarrow x\,(1 - 2\eta)", 50).move_to(rule)
        self.beat("gd3", 0, TransformMatchingTex(rule, simple))
        self.beat("gd3", 1, self.highlight(simple))
        eta = K.M(r"\eta = 0.1", 44, S.dim).next_to(deriv, DOWN, buff=0.4)
        self.beat("gd3", 2, FadeIn(eta))
        keep = K.M(r"x \leftarrow 0.8\,x", 50, S.ink).next_to(eta, DOWN, buff=0.5)
        self.beat("gd3", 3, Write(keep), self.highlight(keep))
        steps = [x.animate.set_value(2.2 * 0.8 ** k) for k in range(1, 9)]
        self.beat("gd3", 4, K.mn.Succession(*steps), run_time=3)
