"""Six search algorithms compared, for interview prep. ManimGX + LFM3-Audio narration.

    manimgx inspect search_algorithms.py
    manimgx render search_algorithms.py

Narration lines live in narration.py; each [bracket] there is the span one animation plays on.
"""
import math
import sys
from pathlib import Path

import numpy as np

import manimgx as m

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))
from lfm_voice import load_script, lfm_voice  # noqa: E402

N = load_script(HERE / "narration.py").LINES

m.config.background_color = "#111111"
FG = "#FFFFFF"
DIM = "#9A9A9A"
ACCENT = "#FF8700"
GOOD = "#5FD787"
BAD = "#FF5F5F"
BLUE = "#5FAFFF"
PANEL = "#1C1C1C"
FONT = "Avenir Next"
MONO = "Menlo"

SORTED = [2, 5, 8, 12, 16, 23, 38, 45, 56, 62, 72, 80, 85, 91, 95, 99]


# ---------- drawing helpers ----------
def T(s, size=28, color=FG, font=FONT):
    return m.Text(s, font=font, font_size=size, color=color)


def card(text, color=FG, size=24, width=None, height=None, fill=PANEL, font=FONT):
    lab = m.VGroup(*[T(line, size if i == 0 else size - 4, color if i == 0 else DIM, font)
                     for i, line in enumerate(text.split("\n"))])
    lab.arrange(m.DOWN, buff=0.12)
    box = m.RoundedRectangle(corner_radius=0.12, width=width or lab.width + 0.6, height=height or lab.height + 0.45,
                             stroke_color=color, stroke_width=3, fill_color=fill, fill_opacity=1)
    lab.move_to(box)
    return m.VGroup(box, lab)


def code(lines, size=22, color=FG):
    g = m.VGroup(*[T(line.lstrip(), size, color, MONO) for line in lines]).arrange(m.DOWN, aligned_edge=m.LEFT, buff=0.14)
    char = T("x" * 10, size, color, MONO).width / 10
    for t, line in zip(g, lines):
        t.shift((len(line) - len(line.lstrip())) * char * m.RIGHT)
    g.move_to(m.ORIGIN)
    box = m.RoundedRectangle(corner_radius=0.12, width=g.width + 1.0, height=g.height + 0.6, stroke_color=DIM,
                             stroke_width=2, fill_color=PANEL, fill_opacity=1)
    g.move_to(box)
    return m.VGroup(box, g)


def cells(vals, w=0.66, size=22, widths=None):
    out = m.VGroup()
    for i, v in enumerate(vals):
        ww = widths[i] if widths else w
        sq = m.Rectangle(width=ww, height=w, stroke_color=DIM, stroke_width=2, fill_color=PANEL, fill_opacity=1)
        out.add(m.VGroup(sq, T(str(v), size).move_to(sq)))
    return out.arrange(m.RIGHT, buff=0.06)


def indices(arr, size=16):
    return m.VGroup(*[T(str(i), size, DIM).next_to(c, m.DOWN, buff=0.1) for i, c in enumerate(arr)])


def fill(c, color, op=0.85):
    return c[0].animate.set_fill(color, op)


def ptr(label, color=ACCENT, up=True):
    """A small arrow with a label; up=True sits below a cell and points up at it."""
    a = m.Arrow(m.ORIGIN, 0.6 * (m.UP if up else m.DOWN), buff=0, color=color, stroke_width=4,
                max_tip_length_to_length_ratio=0.35)
    lab = T(label, 18, color)
    lab.next_to(a, m.DOWN if up else m.UP, buff=0.06)
    return m.VGroup(a, lab)


def at(p, c, up=True):
    return p.animate.next_to(c, m.DOWN if up else m.UP, buff=0.08)


def place(p, c, up=True):
    return p.next_to(c, m.DOWN if up else m.UP, buff=0.08)


class SearchAlgorithms(m.Scene):
    voice = staticmethod(lfm_voice(HERE / "narration.py"))

    def construct(self) -> None:
        self.intro()
        self.growth()
        self.linear()
        self.binary()
        self.jump()
        self.exponential()
        self.interpolation()
        self.hashing()
        self.compare()
        self.choose()
        self.quiz()

    # ---------- scene helpers ----------
    def beat(self, key, *anims):
        n = N[key].count("[")
        assert n == len(anims), f"{key}: {n} brackets, {len(anims)} animations"
        self.say(N[key], *anims)

    def clear_all(self):
        if self.mobjects:
            self.play(*[m.FadeOut(x) for x in self.mobjects], run_time=0.6)

    def fade(self, *mobs):
        self.play(*[m.FadeOut(x) for x in mobs], run_time=0.5)

    def header(self, text):
        self.clear_all()
        h = T(text, 34).to_edge(m.UP, buff=0.35)
        self.play(m.FadeIn(h, shift=0.2 * m.DOWN), run_time=0.6)
        return h

    # ---------- intro ----------
    def intro(self):
        title = T("Search Algorithms, Compared", 50).move_to(2.9 * m.UP)
        sub = T("interview prep  ·  how they work, what they cost, when to use them", 22, DIM).next_to(title, m.DOWN, buff=0.2)
        self.play(m.Write(title), m.FadeIn(sub), run_time=1.2)
        names = ["Linear", "Binary", "Jump", "Exponential", "Interpolation", "Hash table"]
        row = m.VGroup(*[card(n, ACCENT if i == 5 else FG, 24, height=0.8) for i, n in enumerate(names)])
        row.arrange(m.RIGHT, buff=0.22).move_to(0.9 * m.UP)
        three = m.VGroup(*[T(s, 26, DIM) for s in ["how it works", "what it costs", "when to pick it"]])
        three.arrange(m.RIGHT, buff=1.0).move_to(0.35 * m.DOWN)
        self.beat("in1", m.LaggedStart(*[m.FadeIn(c, shift=0.2 * m.UP) for c in row], lag_ratio=0.15),
                  m.LaggedStart(*[m.FadeIn(t) for t in three], lag_ratio=0.3))

        cols = m.VGroup(card("best · average · worst", FG, 24), card("space", BLUE, 24), card("prerequisites", GOOD, 24))
        cols.arrange(m.RIGHT, buff=0.5).move_to(2.0 * m.DOWN)
        self.beat("in2", m.FadeIn(cols[0], shift=0.2 * m.UP), m.FadeIn(cols[1], shift=0.2 * m.UP),
                  m.FadeIn(cols[2], shift=0.2 * m.UP))

    # ---------- 1. growth rates ----------
    def growth(self):
        self.header("1 · How big is each growth rate?")
        n_lab = card("n = 1,000,000", ACCENT, 30).move_to(2.3 * m.UP)
        self.beat("bg1", m.FadeIn(n_lab, scale=0.9))

        data = [("O(1)", 1, "1"), ("O(log log n)", 4.3, "≈ 4"), ("O(log n)", 20, "≈ 20"),
                ("O(√n)", 1000, "1,000"), ("O(n)", 1e6, "1,000,000")]
        colors = [GOOD, GOOD, BLUE, ACCENT, BAD]
        rows = m.VGroup()
        for (name, v, s), col in zip(data, colors):
            length = 0.15 + 7.5 * math.log10(v) / 6
            b = m.Rectangle(width=length, height=0.42, stroke_width=0, fill_color=col, fill_opacity=0.9)
            lab = T(name, 24, col)
            val = T(s, 22, FG)
            rows.add(m.VGroup(lab, b, val))
        rows.arrange(m.DOWN, buff=0.28).move_to(0.6 * m.DOWN)
        for r in rows:
            r[0].set_x(-4.6)
            r[1].move_to(np.array([-3.0, r[0].get_y(), 0]), aligned_edge=m.LEFT)
            r[2].next_to(r[1], m.RIGHT, buff=0.25)
        note = T("bar length on a log scale", 18, DIM).next_to(rows, m.DOWN, buff=0.3)
        self.beat("bg2", *[m.AnimationGroup(m.FadeIn(r[0]), m.GrowFromEdge(r[1], m.LEFT), m.FadeIn(r[2]),
                                            *( [m.FadeIn(note)] if i == 0 else []))
                           for i, r in enumerate(rows)])

        lab = T("←  50,000× fewer steps than O(n)", 22, ACCENT).next_to(rows[2][2], m.RIGHT, buff=0.4)
        lands = T("every algorithm below lands on one of these rows", 22, DIM).next_to(n_lab, m.DOWN, buff=0.25)
        self.beat("bg3", m.AnimationGroup(m.Indicate(rows[4]), m.Indicate(rows[2]), m.FadeIn(lab)),
                  m.FadeIn(lands))

    # ---------- 2. linear ----------
    def linear(self):
        self.header("2 · Linear search")
        vals = [7, 3, 9, 1, 8, 4, 6, 2, 5, 0]
        arr = cells(vals, 0.8, 26).move_to(1.2 * m.UP)
        tgt = T("target = 4", 24, ACCENT).next_to(arr, m.UP, buff=0.4)
        unsorted = T("unsorted", 20, DIM).next_to(arr, m.RIGHT, buff=0.3)
        self.play(m.FadeIn(arr), m.FadeIn(tgt), m.FadeIn(unsorted), run_time=0.8)
        p = place(ptr("i"), arr[0])
        self.beat("li1", m.AnimationGroup(m.FadeIn(p), fill(arr[0], ACCENT, 0.5)),
                  m.Succession(*[m.AnimationGroup(at(p, c), fill(c, ACCENT, 0.5)) for c in arr[1:5]]),
                  m.AnimationGroup(at(p, arr[5]), fill(arr[5], GOOD)))
        self.play(*[fill(c, PANEL, 1) for c in arr], m.FadeOut(p), run_time=0.5)

        best = T("best: 1 comparison → O(1)", 22, GOOD).next_to(arr[0], m.DOWN, buff=0.3).align_to(arr, m.LEFT)
        worst = T("worst: n comparisons → O(n)", 22, BAD).next_to(arr[-1], m.DOWN, buff=0.3).align_to(arr, m.RIGHT)
        br = m.Brace(arr[:5], m.DOWN, color=BLUE).shift(0.9 * m.DOWN)
        avg = T("average ≈ n/2 → still O(n)", 22, BLUE).next_to(br, m.DOWN, buff=0.15)
        self.beat("li2", m.AnimationGroup(fill(arr[0], GOOD), m.FadeIn(best)),
                  m.AnimationGroup(fill(arr[-1], BAD), m.FadeIn(worst)),
                  m.AnimationGroup(m.GrowFromCenter(br), m.FadeIn(avg)))

        cards = m.VGroup(card("Space O(1)\njust an index", BLUE, 24, width=3.8),
                         card("No prerequisites\nunsorted, linked lists", GOOD, 24, width=3.8),
                         card("Searching once?\nsorting costs O(n log n)", ACCENT, 24, width=3.8))
        cards.arrange(m.RIGHT, buff=0.3).move_to(2.65 * m.DOWN)
        self.beat("li3", *[m.FadeIn(c, shift=0.2 * m.UP) for c in cards])

    # ---------- 3. binary ----------
    def binary(self):
        h = self.header("3 · Binary search")
        arr = cells(SORTED).move_to(1.3 * m.UP)
        tgt = T("target = 23", 24, ACCENT).move_to(2.55 * m.UP + 4.5 * m.RIGHT)
        srt = T("sorted ✓", 22, GOOD).move_to(2.55 * m.UP + 4.5 * m.LEFT)
        lo, hi = place(ptr("low", BLUE), arr[0]), place(ptr("high", BLUE), arr[15])
        mid = place(ptr("mid", ACCENT, up=False), arr[7], up=False)
        self.beat("bi1", m.AnimationGroup(m.FadeIn(arr), m.FadeIn(srt), m.FadeIn(tgt)),
                  m.AnimationGroup(m.FadeIn(lo), m.FadeIn(hi)),
                  m.AnimationGroup(m.FadeIn(mid), fill(arr[7], ACCENT, 0.6)),
                  m.AnimationGroup(*[c.animate.set_opacity(0.25) for c in arr[7:]], at(hi, arr[6])))
        self.beat("bi2", m.AnimationGroup(at(mid, arr[3], up=False), fill(arr[3], ACCENT, 0.6)),
                  m.AnimationGroup(*[c.animate.set_opacity(0.25) for c in arr[:4]], at(lo, arr[4])),
                  m.AnimationGroup(at(mid, arr[5], up=False), fill(arr[5], GOOD)))

        seq = m.VGroup(*[T(s, 30, c) for s, c in zip(["16", "→ 8", "→ 4", "→ 2", "→ 1"], [FG, FG, FG, FG, GOOD])])
        seq.arrange(m.RIGHT, buff=0.3).move_to(0.6 * m.DOWN)
        steps = T("number of halvings = log₂ n", 28, ACCENT).move_to(1.5 * m.DOWN)
        mil = T("n = 1,000,000  →  ≈ 20 comparisons", 28, GOOD).move_to(2.4 * m.DOWN)
        self.beat("bi3", m.LaggedStart(*[m.FadeIn(s, shift=0.2 * m.RIGHT) for s in seq], lag_ratio=0.4),
                  m.FadeIn(steps), m.FadeIn(mil))
        self.fade(seq, steps, mil, lo, hi, mid)
        self.play(*[c.animate.set_opacity(1) for c in arr], *[fill(c, PANEL, 1) for c in arr], run_time=0.5)

        grid = m.VGroup(card("Best O(1)\ntarget is the first middle", GOOD, 24, width=5.2),
                        card("Average & worst O(log n)", ACCENT, 24, width=5.2, height=1.05),
                        card("Space O(1)\niterative loop", BLUE, 24, width=5.2),
                        card("Space O(log n)\nrecursive: call stack", BLUE, 24, width=5.2))
        grid.arrange_in_grid(rows=2, cols=2, buff=(0.4, 0.35)).move_to(1.3 * m.DOWN)
        self.beat("bi4", m.AnimationGroup(m.Indicate(arr[7], color=GOOD), fill(arr[7], GOOD), m.FadeIn(grid[0])),
                  m.FadeIn(grid[1]), m.FadeIn(grid[2]), m.FadeIn(grid[3]))
        self.fade(arr, grid, srt, tgt)

        c1 = code(["mid = lo + (hi - lo) // 2"], 28)
        n1 = T("not (lo + hi) / 2: overflows fixed-width integers", 22, DIM)
        c2 = code(["while lo <= hi:"], 28)
        n2 = T("<=, not <: a one-element range must still be checked", 22, DIM)
        g = m.VGroup(m.VGroup(c1, n1).arrange(m.DOWN, buff=0.2), m.VGroup(c2, n2).arrange(m.DOWN, buff=0.2))
        g.arrange(m.DOWN, buff=0.8).move_to(0.4 * m.DOWN)
        bugs = T("classic bugs", 24, BAD).next_to(h, m.DOWN, buff=0.35)
        self.play(m.FadeIn(bugs), run_time=0.4)
        self.beat("bi5", m.FadeIn(g[0], shift=0.2 * m.UP), m.FadeIn(g[1], shift=0.2 * m.UP))

    # ---------- 4. jump ----------
    def jump(self):
        self.header("4 · Jump search")
        arr = cells(SORTED).move_to(1.4 * m.UP)
        tgt = T("target = 62", 24, ACCENT).move_to(2.6 * m.UP + 4.5 * m.RIGHT)
        msz = T("block size m = √16 = 4", 22, DIM).move_to(2.6 * m.UP + 4.0 * m.LEFT)
        idx = indices(arr)
        self.play(m.FadeIn(arr), m.FadeIn(tgt), m.FadeIn(idx), run_time=0.8)
        divs = m.VGroup(*[m.Line(arr[i].get_corner(m.UR) + 0.15 * m.UP + 0.03 * m.RIGHT,
                                 arr[i].get_corner(m.DR) + 0.15 * m.DOWN + 0.03 * m.RIGHT, color=ACCENT, stroke_width=3)
                          for i in (3, 7, 11)])
        hops = m.VGroup(*[m.CurvedArrow(arr[a].get_top() + 0.08 * m.UP, arr[b].get_top() + 0.08 * m.UP, angle=-1.0, color=DIM)
                          for a, b in ((3, 7), (7, 11))])
        self.beat("ju1", m.AnimationGroup(m.FadeIn(msz), m.Create(divs)),
                  m.AnimationGroup(fill(arr[3], ACCENT, 0.6), m.Create(hops[0]), fill(arr[7], ACCENT, 0.6)),
                  m.AnimationGroup(m.Create(hops[1]), fill(arr[11], BAD)),
                  m.Succession(fill(arr[8], ACCENT, 0.6), fill(arr[9], GOOD)))

        l1 = T("jumps ≈ n / m", 28).move_to(0.1 * m.DOWN)
        l2 = T("+  scan inside one block ≤ m", 28).move_to(0.85 * m.DOWN)
        l3 = T("n/m + m is smallest at m = √n   →   ≈ 2√n steps", 28, ACCENT).move_to(1.7 * m.DOWN)
        self.beat("ju2", m.FadeIn(l1), m.FadeIn(l2), m.FadeIn(l3))

        cs = m.VGroup(card("O(√n)\naverage & worst", ACCENT, 30, width=3.9),
                      card("n = 1,000,000\n≈ 1,000 jumps + 1,000 steps", FG, 24, width=4.4),
                      card("one step back only\nhelps when going back is costly", BLUE, 24, width=4.6))
        cs.arrange(m.RIGHT, buff=0.25).move_to(3.0 * m.DOWN)
        self.beat("ju3", *[m.FadeIn(c, shift=0.2 * m.UP) for c in cs])

    # ---------- 5. exponential ----------
    def exponential(self):
        self.header("5 · Exponential search")
        arr = cells(SORTED).move_to(1.6 * m.UP)
        idx = indices(arr)
        tgt = T("target = 45", 24, ACCENT).move_to(2.75 * m.UP + 4.5 * m.RIGHT)
        self.play(m.FadeIn(arr), m.FadeIn(idx), m.FadeIn(tgt), run_time=0.8)
        tags = m.VGroup(*[T(f"i={i}", 18, ACCENT).next_to(arr[i], m.UP, buff=0.12) for i in (1, 2, 4)])
        tag8 = T("i=8", 18, BAD).next_to(arr[8], m.UP, buff=0.12)
        br = m.Brace(m.VGroup(*arr[4:9]), m.DOWN, color=BLUE).shift(0.35 * m.DOWN)
        brl = T("target is in [4, 8]", 20, BLUE).next_to(br, m.DOWN, buff=0.1)
        self.beat("ex1", m.Succession(*[m.AnimationGroup(fill(arr[i], ACCENT, 0.6), m.FadeIn(t)) for i, t in zip((1, 2, 4), tags)]),
                  m.AnimationGroup(fill(arr[8], BAD), m.FadeIn(tag8)),
                  m.AnimationGroup(m.GrowFromCenter(br), m.FadeIn(brl)),
                  m.Succession(m.AnimationGroup(*[c.animate.set_opacity(0.25) for c in [*arr[:4], *arr[9:]]]),
                               fill(arr[6], ACCENT, 0.6), fill(arr[7], GOOD)))

        l1 = T("doubling:  ≈ log₂ i probes", 26).move_to(0.6 * m.DOWN)
        l2 = T("binary search over ≤ i elements:  ≈ log₂ i", 26).move_to(1.3 * m.DOWN)
        l3 = T("total  O(log i)  ≤  O(log n)", 28, ACCENT).move_to(2.1 * m.DOWN)
        l4 = T("target near the front → very fast", 24, GOOD).move_to(2.85 * m.DOWN)
        self.beat("ex2", m.FadeIn(l1), m.FadeIn(l2), m.FadeIn(l3), m.FadeIn(l4))
        self.fade(arr, idx, tgt, tags, tag8, br, brl, l1, l2, l3, l4)

        stream = cells([3, 7, 9, 14, 20, 31, 40, 52, 66, 80], 0.75, 22)
        for i, c in enumerate(stream):
            c.set_opacity(1 - i * 0.09)
        nq = T("n = ?", 30, ACCENT)
        m.VGroup(stream, nq).arrange(m.RIGHT, buff=0.4).move_to(1.3 * m.UP)
        cs = m.VGroup(card("unbounded / infinite lists", GOOD, 24),
                      card("streams", GOOD, 24), card("API: value at index i", GOOD, 24)).arrange(m.RIGHT, buff=0.3)
        cs.move_to(0.4 * m.DOWN)
        sp = card("Space O(1)", BLUE, 26).move_to(2.2 * m.DOWN)
        self.beat("ex3", m.AnimationGroup(m.FadeIn(stream, shift=0.3 * m.RIGHT), m.FadeIn(nq)),
                  m.LaggedStart(*[m.FadeIn(c, shift=0.2 * m.UP) for c in cs], lag_ratio=0.25), m.FadeIn(sp))

    # ---------- 6. interpolation ----------
    def interpolation(self):
        self.header("6 · Interpolation search")
        letters = m.VGroup(*[T(chr(65 + i), 24, DIM) for i in range(26)]).arrange(m.RIGHT, buff=0.2).move_to(1.0 * m.UP)
        book = T("phone book", 22, DIM).next_to(letters, m.UP, buff=0.4)
        self.play(m.FadeIn(letters), m.FadeIn(book), run_time=0.6)
        midm = m.SurroundingRectangle(letters[12], color=BAD, buff=0.1)
        midl = T("binary: open the middle", 20, BAD).next_to(midm, m.DOWN, buff=0.3)
        wm = m.SurroundingRectangle(letters[22], color=GOOD, buff=0.1)
        wl = T("you: open near W", 20, GOOD).next_to(wm, m.DOWN, buff=0.3)
        idea = card("guess the position from the values", ACCENT, 26).move_to(1.6 * m.DOWN)
        self.beat("ip1", m.AnimationGroup(m.Create(midm), m.FadeIn(midl)),
                  m.AnimationGroup(m.Create(wm), m.FadeIn(wl), letters[22].animate.set_color(GOOD)),
                  m.FadeIn(idea, shift=0.2 * m.UP))
        self.clear_all()

        h = T("6 · Interpolation search", 34).to_edge(m.UP, buff=0.35)
        self.add(h)
        ax = m.Axes(x_range=[0, 15, 5], y_range=[0, 160, 40], x_length=6.0, y_length=3.2,
                    axis_config={"color": DIM, "include_ticks": False}).move_to(0.65 * m.UP)
        xl = T("index", 18, DIM).next_to(ax, m.DOWN, buff=0.1)
        yl = T("value", 18, DIM).next_to(ax, m.LEFT, buff=0.1)
        p0, p1 = ax.c2p(0, 10), ax.c2p(15, 160)
        line = m.Line(p0, p1, color=ACCENT, stroke_width=4)
        d0, d1 = m.Dot(p0, color=BLUE), m.Dot(p1, color=BLUE)
        l0 = T("(low, A[low])", 18, BLUE).next_to(ax.c2p(0, 0), m.DOWN, buff=0.15)
        l1 = T("(high, A[high])", 18, BLUE).next_to(d1, m.UL, buff=0.1)
        hz = m.DashedLine(ax.c2p(0, 130), ax.c2p(12, 130), color=FG)
        vt = m.DashedLine(ax.c2p(12, 130), ax.c2p(12, 0), color=GOOD)
        xlab = T("x", 28).next_to(ax.c2p(0, 130), m.LEFT, buff=0.1)
        poslab = T("pos", 20, GOOD).next_to(ax.c2p(12, 0), m.DOWN, buff=0.1)
        form = T("pos = low + (x − A[low]) · (high − low) / (A[high] − A[low])", 24, ACCENT, MONO)
        form.scale_to_fit_width(12.5).move_to(2.6 * m.DOWN)
        self.play(m.Create(ax), m.FadeIn(xl), m.FadeIn(yl), run_time=0.6)
        self.beat("ip2", m.AnimationGroup(m.FadeIn(d0), m.FadeIn(d1), m.Create(line), m.FadeIn(l0), m.FadeIn(l1),
                                          m.Create(hz), m.FadeIn(xlab), m.Create(vt), m.FadeIn(poslab)),
                  m.Write(form))
        self.fade(ax, xl, yl, line, d0, d1, l0, l1, hz, vt, xlab, poslab)
        self.play(form.animate.move_to(2.6 * m.UP + 0.0 * m.RIGHT).scale(0.85), m.FadeOut(h), run_time=0.6)

        vals = list(range(10, 170, 10))
        arr = cells(vals, 0.7, 20).move_to(1.0 * m.UP)
        idx = indices(arr)
        calc = T("pos = 0 + (130 − 10) · (15 − 0) / (160 − 10) = 12", 24, FG, MONO).move_to(1.0 * m.DOWN)
        tgt = T("target = 130", 22, ACCENT).move_to(1.8 * m.DOWN)
        p = place(ptr("pos", GOOD), arr[12]).shift(0.35 * m.DOWN)
        one = T("1 probe", 26, GOOD).move_to(2.7 * m.DOWN)
        self.beat("ip3", m.AnimationGroup(m.FadeIn(arr), m.FadeIn(idx), m.FadeIn(tgt)),
                  m.AnimationGroup(m.FadeIn(calc), m.FadeIn(p)),
                  m.AnimationGroup(fill(arr[12], GOOD), m.FadeIn(one)))
        self.fade(arr, idx, calc, tgt, p, one, form)

        uni = card("uniform data:  O(log log n)\n≈ 4 probes for a million elements", GOOD, 26).move_to(2.3 * m.UP)
        sk = cells([1, 2, 3, 4, 5, 6, 7, "1,000,000"], 0.75, 22, widths=[0.75] * 7 + [1.9]).move_to(0.3 * m.UP)
        skl = T("skewed data, target = 7", 22, DIM).next_to(sk, m.UP, buff=0.25)
        q = place(ptr("guess", ACCENT), sk[0])
        bad = T("each guess moves one step  →  worst case O(n)", 26, BAD).move_to(2.3 * m.DOWN)
        self.beat("ip4", m.FadeIn(uni, shift=0.2 * m.DOWN),
                  m.AnimationGroup(m.FadeIn(sk), m.FadeIn(skl)),
                  m.Succession(m.AnimationGroup(m.FadeIn(q), fill(sk[0], ACCENT, 0.5)),
                               *[m.AnimationGroup(at(q, c), fill(c, ACCENT, 0.5)) for c in sk[1:6]]),
                  m.FadeIn(bad))

    # ---------- 7. hash table ----------
    def hashing(self):
        h = self.header("7 · Hash table lookup")
        no = T("no comparisons  ·  no order", 24, DIM).next_to(h, m.DOWN, buff=0.3)
        buckets = m.VGroup(*[m.Rectangle(width=0.9, height=0.5, stroke_color=DIM, stroke_width=2,
                                         fill_color=PANEL, fill_opacity=1) for _ in range(8)])
        buckets.arrange(m.DOWN, buff=0.08).move_to(0.75 * m.DOWN + 1.2 * m.RIGHT)
        bidx = m.VGroup(*[T(str(i), 18, DIM).next_to(b, m.LEFT, buff=0.15) for i, b in enumerate(buckets)])
        key = card('"alice"', FG, 26, font=MONO).move_to(np.array([-5.4, buckets[3].get_y(), 0]))
        hf = card("hash(key) mod 8 = 3", ACCENT, 24).move_to(np.array([-2.6, buckets[3].get_y(), 0]))
        a1 = m.Arrow(key.get_right(), hf.get_left(), buff=0.1, color=DIM)
        a2 = m.Arrow(hf.get_right(), bidx[3].get_left(), buff=0.1, color=ACCENT)
        self.beat("ha1", m.FadeIn(no),
                  m.AnimationGroup(m.FadeIn(key), m.GrowArrow(a1), m.FadeIn(hf), m.FadeIn(buckets), m.FadeIn(bidx)),
                  m.AnimationGroup(m.GrowArrow(a2), buckets[3].animate.set_fill(GOOD, 0.6)))

        def chip(color=BLUE):
            return m.RoundedRectangle(corner_radius=0.06, width=0.42, height=0.36, stroke_width=0,
                                      fill_color=color, fill_opacity=0.9)

        spread = [0, 1, 1, 2, 3, 5, 6, 7]
        chips = m.VGroup()
        count = {}
        for b in spread:
            k = count.get(b, 0)
            count[b] = k + 1
            chips.add(chip().next_to(buckets[b], m.RIGHT, buff=0.12 + k * 0.5))
        lf = T("load factor = items / buckets, kept low by resizing", 20, DIM).move_to(3.45 * m.DOWN)
        avg = card("average O(1)", GOOD, 26).move_to(np.array([5.2, 1.4, 0]))
        self.beat("ha2", m.AnimationGroup(m.LaggedStart(*[m.FadeIn(c, scale=0.5) for c in chips], lag_ratio=0.1), m.FadeIn(lf)),
                  m.FadeIn(avg, shift=0.2 * m.LEFT))

        targets = [chip(BAD).next_to(buckets[3], m.RIGHT, buff=0.12 + k * 0.5) for k in range(8)]
        worst = card("worst O(n)", BAD, 26).move_to(np.array([5.2, -2.6, 0]))
        self.beat("ha3", m.AnimationGroup(*[m.Transform(c, t) for c, t in zip(chips, targets)]),
                  m.FadeIn(worst, shift=0.2 * m.LEFT))
        self.clear_all()

        h = T("7 · Hash table lookup", 34).to_edge(m.UP, buff=0.35)
        self.add(h)
        cs = m.VGroup(card("Space O(n)\nthe table itself", BLUE, 28, width=4.0),
                      card("No ordering\nno range queries, no next larger key", BAD, 28, width=5.6))
        cs.arrange(m.RIGHT, buff=0.4).move_to(0.6 * m.UP)
        use = card("use it for: exact keys, looked up many times", GOOD, 28).move_to(1.5 * m.DOWN)
        self.beat("ha4", m.FadeIn(cs[0], shift=0.2 * m.UP), m.FadeIn(cs[1], shift=0.2 * m.UP), m.FadeIn(use, shift=0.2 * m.UP))

    # ---------- 8. comparison ----------
    def compare(self):
        self.header("8 · Side by side")
        head = ["Algorithm", "Best", "Average", "Worst", "Space", "Needs"]
        rows = [
            ["Linear", "O(1)", "O(n)", "O(n)", "O(1)", "nothing (unsorted OK)"],
            ["Binary", "O(1)", "O(log n)", "O(log n)", "O(1)", "sorted"],
            ["Jump", "O(1)", "O(√n)", "O(√n)", "O(1)", "sorted"],
            ["Exponential", "O(1)", "O(log n)", "O(log n)", "O(1)", "sorted; size can be unknown"],
            ["Interpolation", "O(1)", "O(log log n)", "O(n)", "O(1)", "sorted + uniform"],
            ["Hash table", "O(1)", "O(1)", "O(n)", "O(n)", "a hash table"],
        ]
        xs = [-5.3, -3.15, -1.7, -0.05, 1.35, 4.25]
        ys = [2.3 - 0.72 * i for i in range(7)]
        table = [[T(s, 22, DIM).move_to(np.array([x, ys[0], 0])) for s, x in zip(head, xs)]]
        for r, y in zip(rows, ys[1:]):
            table.append([T(s, 22 if j else 24, FG if j else ACCENT).move_to(np.array([x, y, 0])) for j, (s, x) in enumerate(zip(r, xs))])
        flat = m.VGroup(*[c for row in table for c in row])
        rule = m.Line(np.array([-6.6, ys[0] - 0.36, 0]), np.array([6.6, ys[0] - 0.36, 0]), color=DIM, stroke_width=1.5)
        self.play(m.FadeIn(flat), m.Create(rule), run_time=1.0)

        def col(j, r0=1, r1=6):
            return m.VGroup(*[table[r][j] for r in range(r0, r1 + 1)])

        def box(g, color):
            return m.SurroundingRectangle(g, color=color, buff=0.12, stroke_width=3)

        bb = box(col(1), GOOD)
        self.beat("cm1", m.Create(bb), m.AnimationGroup(m.FadeOut(bb), col(1, 0).animate.set_opacity(0.3)))

        hb = box(table[6][2], GOOD)
        ib = box(m.VGroup(table[5][2], table[5][3]), ACCENT)
        bxb = m.VGroup(box(m.VGroup(table[2][2], table[2][3]), BLUE), box(m.VGroup(table[4][2], table[4][3]), BLUE))
        self.beat("cm2", m.Create(hb), m.Create(ib), m.Create(bxb))
        self.fade(hb, ib, bxb)

        sb = box(col(4, 1, 5), GOOD)
        hs = box(table[6][4], BAD)
        self.beat("cm3", m.Create(sb), m.Create(hs))

    # ---------- 9. choosing ----------
    def choose(self):
        self.header("9 · Which one do I pick?")
        pairs = [("unsorted, searched once?", "Linear"), ("exact keys, many lookups?", "Hash table"),
                 ("sorted, in memory?", "Binary  (safe default)"), ("size unknown / unbounded?", "Exponential"),
                 ("sorted and evenly spread?", "Interpolation"), ("stepping back is costly?", "Jump")]
        rows = m.VGroup()
        for q, a in pairs:
            qt = T(q, 26)
            ar = m.Arrow(m.LEFT, m.RIGHT, buff=0, color=DIM).scale(0.5)
            at_ = T(a, 26, ACCENT)
            rows.add(m.VGroup(qt, ar, at_))
        rows.arrange(m.DOWN, buff=0.38).move_to(0.4 * m.DOWN)
        for r in rows:
            r[0].move_to(np.array([-1.0, r.get_y(), 0]), aligned_edge=m.RIGHT)
            r[1].move_to(np.array([-0.4, r.get_y(), 0]))
            r[2].move_to(np.array([0.3, r.get_y(), 0]), aligned_edge=m.LEFT)
        rows.set_x(0)
        f = lambda r: m.FadeIn(r, shift=0.2 * m.RIGHT)  # noqa: E731
        self.beat("ch1", f(rows[0]), f(rows[1]))
        self.beat("ch2", f(rows[2]), f(rows[3]), f(rows[4]), f(rows[5]))

    # ---------- 10. quiz ----------
    def quiz(self):
        self.header("10 · Say these out loud before the interview")
        qs = m.VGroup(*[card(s, FG, 24, width=5.8, height=1.15) for s in [
            "Why is binary search O(log n)?\nit halves the range each step",
            "Why is the jump size √n?\nminimizes n/m + m",
            "When is a hash lookup O(n)?\nall keys collide in one bucket",
            "When does linear beat binary?\nunsorted data, one search, tiny n",
        ]])
        qs.arrange_in_grid(rows=2, cols=2, buff=(0.35, 0.3)).move_to(0.2 * m.UP)
        self.beat("qz1", *[m.FadeIn(q, shift=0.2 * m.UP) for q in qs])
        self.fade(qs)
        snippet = code([
            "def binary_search(a, x):",
            "    lo, hi = 0, len(a) - 1",
            "    while lo <= hi:",
            "        mid = lo + (hi - lo) // 2",
            "        if a[mid] == x: return mid",
            "        if a[mid] < x: lo = mid + 1",
            "        else: hi = mid - 1",
            "    return -1",
        ], 22).move_to(0.3 * m.DOWN)
        self.beat("qz2", m.FadeIn(snippet, shift=0.2 * m.UP))
        self.wait(1.5)
