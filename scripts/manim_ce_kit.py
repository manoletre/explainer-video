"""Manim Community scenes timed to the narration, in the house style. Import it in the scene:

    import sys; sys.path.insert(0, "<this skill>/scripts")
    from manim import *
    from manim_ce_kit import Explainer, T, M, card
    class XExplainer(Explainer):
        narration = Path(__file__).parent / "narration.py"
        def construct(self):
            self.section("in1")                      # clears the screen, shows the section's title
            self.beat("in1", 0, Write(T("Hello")))   # plays when bracket 0 of line in1 is spoken

Every play waits for its words: beat(key, i, *anims) starts the animations when bracket i of line
key starts being spoken (times from the audio, scripts/timeline.py). The narration track is added
as the scene's sound. At the end the scene writes check.json beside it (brackets used, layout
problems at every beat), which manim_ce.py check turns into the reports.
"""
import json
import sys
from pathlib import Path

import manim as mn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import style  # noqa: E402
import timeline as TLM  # noqa: E402

S = None  # the theme, set when the scene starts


def T(text, size=36, color=None, weight=mn.NORMAL, mono=False):
    """Text in the theme's font."""
    return mn.Text(text, font=(S.mono if mono else S.font) if S else "PT Serif", font_size=size,
                   color=color or (S.fg if S else mn.WHITE), weight=weight)


def M(tex, size=48, color=None):
    """A formula (LaTeX)."""
    return mn.MathTex(tex, font_size=size, color=color or (S.fg if S else mn.WHITE))


def card(title, w=3.2, h=1.2, sub=None, size=32, color=None):
    """A rounded panel with a title (and a dim subtitle)."""
    box = mn.RoundedRectangle(width=w, height=h, corner_radius=0.15, stroke_color=color or S.line,
                              stroke_width=3, fill_color=S.panel, fill_opacity=1)
    parts = [T(title, size, weight=mn.BOLD)]
    if sub:
        parts.append(T(sub, size * 0.62, S.dim))
    text = mn.VGroup(*parts).arrange(mn.DOWN, buff=0.12).move_to(box)
    return mn.VGroup(box, text)


class Explainer(mn.Scene):
    narration = None  # Path to narration.py; set in the subclass

    def setup(self):
        global S
        d = Path(self.narration).resolve().parent
        S = style.theme(self.narration)
        self.camera.background_color = S.bg
        work = d / "manim-ce"
        self.tl = TLM.prepare(d, work / "timeline.json", work / "narration.wav", quiet=True)
        self.lines = {ln["key"]: ln for ln in self.tl["lines"]}
        self.used, self.problems, self._header = set(), [], None
        self.add_sound(str(work / "narration.wav"), time_offset=0)

    def now(self):
        return self.renderer.time

    def until(self, t):
        if t > self.now() + 1 / 120:
            self.wait(t - self.now())

    def at(self, key, i=0):
        ln = self.lines[key]
        if i >= len(ln["spans"]):
            raise IndexError(f"line {key} has {len(ln['spans'])} brackets, so there is no bracket {i}")
        self.used.add(f"{key}:{i}")
        return ln["spans"][i]["start"]

    def section(self, key):
        """Clear the screen and show the title of the section that starts at line key."""
        sec = next((s for s in self.tl["sections"] if s["first"] == key), None)
        if sec is None:
            raise KeyError(f"no section starts at line {key}: add it to SECTIONS in narration.py")
        if self.mobjects:
            self.until(sec["start"] - 0.4)
            self.play(*[mn.FadeOut(m) for m in self.mobjects], run_time=0.4)
        self.until(sec["start"])
        num, _, rest = sec["title"].partition(" · ")
        title = (mn.VGroup(T(num, 40, S.ink, mn.BOLD), T("·", 40, S.dim), T(rest, 40, weight=mn.BOLD))
                 .arrange(mn.RIGHT, buff=0.18) if rest else T(sec["title"], 40, weight=mn.BOLD))
        title.to_corner(mn.UL, buff=0.5)
        self._header = title
        self.play(mn.FadeIn(title), run_time=0.5)

    def beat(self, key, i, *anims, run_time=None):
        """Play anims when bracket i of line key starts; by default they last as long as its words (0.5-1.5 s)."""
        t = self.at(key, i)
        span = self.lines[key]["spans"][i]
        self.until(t)
        if anims:
            self.play(*anims, run_time=run_time or min(1.5, max(0.5, span["end"] - span["start"])))
        self._check_layout()

    def highlight(self, mob):
        """A gold marker behind mob, as an animation."""
        hl = mn.SurroundingRectangle(mob, color=S.accent, fill_color=S.accent, fill_opacity=0.35, buff=0.08,
                                     stroke_width=0, corner_radius=0.06)
        return mn.Succession(mn.FadeIn(hl, run_time=0.3), mn.Wait(0.6), mn.FadeOut(hl, run_time=0.3))

    def _check_layout(self):
        fw, fh = mn.config.frame_width / 2, mn.config.frame_height / 2
        boxes = []
        for m in self.mobjects:
            if m is self._header or not m.has_points() and not m.submobjects:
                continue
            try:
                op = max(m.get_fill_opacity(), m.get_stroke_opacity())
            except Exception:  # noqa: BLE001
                op = 1
            if op < 0.3:
                continue
            (x0, y0, _), (x1, y1, _) = m.get_corner(mn.DL), m.get_corner(mn.UR)
            boxes.append((m, x0, y0, x1, y1))
            if x0 < -fw - 0.02 or x1 > fw + 0.02 or y0 < -fh - 0.02 or y1 > fh + 0.02:
                self.problems.append(f"{self.now():7.2f}s  off frame: {type(m).__name__}")
        # graph pieces (axes, curves, dots on them, lines, arrows) are meant to overlap what they draw on
        drawn = (mn.Axes, mn.NumberPlane, mn.ParametricFunction, mn.Dot, mn.Line, mn.TracedPath)
        boxes = [b for b in boxes if not isinstance(b[0], drawn)]
        for a in range(len(boxes)):
            for b in range(a + 1, len(boxes)):
                p, q = boxes[a], boxes[b]
                w, h = min(p[3], q[3]) - max(p[1], q[1]), min(p[4], q[4]) - max(p[2], q[2])
                if w <= 0 or h <= 0:
                    continue
                small = min((p[3] - p[1]) * (p[4] - p[2]), (q[3] - q[1]) * (q[4] - q[2])) or 1e-9
                inside = all(p[k] <= q[k] for k in (1, 2)) and all(p[k] >= q[k] for k in (3, 4)) or \
                    all(q[k] <= p[k] for k in (1, 2)) and all(q[k] >= p[k] for k in (3, 4))
                if not inside and w * h > 0.03 * small:
                    self.problems.append(f"{self.now():7.2f}s  overlap: {type(p[0]).__name__} and "
                                         f"{type(q[0]).__name__} ({round(100 * w * h / small)}%)")

    def tear_down(self):
        self.until(self.tl["duration"])
        out = Path(self.narration).resolve().parent / "manim-ce" / "check.json"
        out.write_text(json.dumps({"used": sorted(self.used), "problems": self.problems}, indent=1))
