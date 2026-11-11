"""Must-know data structures, for interview prep. ManimGX + Kokoro narration.

    manimgx inspect data_structures.py
    manimgx render data_structures.py

Narration lines live in narration.py; each [bracket] there is the span one animation plays on.
"""
import sys
from pathlib import Path

import manimgx as m

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))
from kokoro_voice import kokoro_voice, load_script  # noqa: E402
from stage import Pointer, chrome, hold, say_synced  # noqa: E402
from style import theme  # noqa: E402

N = load_script(HERE / "narration.py").LINES

S = theme(HERE / "narration.py")  # scripts/style.py: PT Serif, gold on black (or light)
m.config.background_color = S.bg
FG = S.fg
DIM = S.dim
ACCENT = S.ink
GOOD = S.good
BAD = S.bad
BLUE = S.blue
PANEL = S.panel
FONT = S.font
MONO = S.mono


# ---------- drawing helpers ----------
def T(s, size=28, color=FG, font=FONT):
    return m.Text(s, font=font, font_size=size, color=color).set_z_index(1)


def M(tex, scale=1.0, color=FG):
    return m.MathTex(tex, color=color).scale(scale).set_z_index(1)


def card(text, color=FG, size=24, width=None, height=None, fill=PANEL):
    lab = m.VGroup(*[T(line, size if i == 0 else size - 4, color if i == 0 else DIM)
                     for i, line in enumerate(text.split("\n"))])
    lab.arrange(m.DOWN, buff=0.12)
    box = m.RoundedRectangle(corner_radius=0.12, width=width or lab.width + 0.6, height=height or lab.height + 0.45,
                             stroke_color=color, stroke_width=3, fill_color=fill, fill_opacity=1)
    lab.move_to(box)
    return m.VGroup(box, lab)


def badge(text, color):
    return card(text, color, 24)


def cell(v, w=0.7, size=24, color=DIM):
    sq = m.Rectangle(width=w, height=w, stroke_color=color, stroke_width=2, fill_color=PANEL, fill_opacity=1)
    return m.VGroup(sq, T(str(v), size).move_to(sq))


def cells(vals, w=0.7, size=24, buff=0.06):
    return m.VGroup(*[cell(v, w, size) for v in vals]).arrange(m.RIGHT, buff=buff)


def node(v, r=0.36, color=FG, size=24):
    c = m.Circle(radius=r, stroke_color=color, stroke_width=3, fill_color=PANEL, fill_opacity=1)
    return m.VGroup(c, T(str(v), size).move_to(c))


def edge(a, b, color=DIM, r=0.36):
    return m.Line(a.get_center(), b.get_center(), buff=r, color=color, stroke_width=3)


def arrow(a, b, color=DIM, buff=0.08):
    return m.Arrow(a, b, buff=buff, color=color, stroke_width=4, max_tip_length_to_length_ratio=0.2)


def lnode(v):
    """A linked-list node: value box and next-pointer box."""
    val = m.Rectangle(width=0.8, height=0.7, stroke_color=FG, stroke_width=2, fill_color=PANEL, fill_opacity=1)
    nxt = m.Rectangle(width=0.4, height=0.7, stroke_color=DIM, stroke_width=2, fill_color=PANEL, fill_opacity=1)
    nxt.next_to(val, m.RIGHT, buff=0)
    dot = m.Dot(nxt.get_center(), radius=0.06, color=DIM)
    return m.VGroup(val, T(str(v), 24).move_to(val), nxt, dot)


def link(a, b, color=DIM):
    return m.Arrow(a[3].get_center(), b[0].get_left(), buff=0.02, color=color, stroke_width=3,
                   max_tip_length_to_length_ratio=0.15)


def chip(s, color=BLUE, size=20):
    return card(s, color, size, height=0.48)


class DataStructures(m.Scene):
    voice = staticmethod(kokoro_voice(HERE / "narration.py"))

    def construct(self) -> None:
        self.ptr = Pointer()
        self.intro()
        self.arrays()
        self.linked_lists()
        self.stacks_queues()
        self.hash_tables()
        self.bsts()
        self.heaps()
        self.graphs()
        self.tries()
        self.compare()
        self.choose()
        self.quiz()

    # ---------- scene helpers ----------
    def beat(self, key, *anims):
        say_synced(self, key, N[key], *anims)

    def clear_all(self):
        rest = [x for x in self.mobjects if x is not self.ptr]
        if rest:
            self.play(*[m.FadeOut(x) for x in rest], self.ptr.hide(), run_time=0.6)

    def clear_below(self):
        """Fade everything but the header and the pointer."""
        rest = [x for x in self.mobjects if x is not self.ptr and not getattr(x, "is_chrome", False)]
        if rest:
            self.play(*[m.FadeOut(x) for x in rest], self.ptr.hide(), run_time=0.5)

    def fade(self, *mobs):
        self.play(*[m.FadeOut(x) for x in mobs], run_time=0.5)

    def header(self, text):
        self.clear_all()
        h = chrome(T(text, 34).to_edge(m.UP, buff=0.35))
        self.play(m.FadeIn(h, shift=0.2 * m.DOWN), run_time=0.6)
        return h

    # ---------- intro ----------
    def intro(self):
        title = T("Must-Know Data Structures", 50).move_to(2.6 * m.UP)
        sub = T("interview prep  ·  layout, costs, and when to use each", 22, DIM).next_to(title, m.DOWN, buff=0.2)
        names = ["Arrays", "Linked lists", "Stacks & queues", "Hash tables",
                 "Binary search trees", "Heaps", "Graphs", "Tries"]
        cards = m.VGroup(*[card(n, ACCENT if i == 3 else FG, 24, width=3.1, height=0.8) for i, n in enumerate(names)])
        cards.arrange_in_grid(rows=2, cols=4, buff=(0.25, 0.3)).move_to(0.25 * m.UP)
        self.beat("in1", m.AnimationGroup(m.Write(title), m.FadeIn(sub)),
                  m.LaggedStart(*[m.FadeIn(c, shift=0.2 * m.UP) for c in cards], lag_ratio=0.15))

        three = m.VGroup(*[card(s, BLUE, 22) for s in ["memory layout", "cost of each operation", "what it's built for"]])
        three.arrange(m.RIGHT, buff=0.4).move_to(1.65 * m.DOWN)
        end = m.VGroup(card("comparison table", ACCENT, 22), card("how to choose", ACCENT, 22))
        end.arrange(m.RIGHT, buff=0.4).move_to(2.95 * m.DOWN)
        self.beat("in2", *[m.FadeIn(c, shift=0.2 * m.UP) for c in three], *[m.FadeIn(c, shift=0.2 * m.UP) for c in end])

    # ---------- 1. arrays ----------
    def arrays(self):
        self.header("1 · Arrays")
        arr = cells([7, 3, 9, 4, 1, 8], w=0.9, size=28, buff=0).move_to(1.3 * m.UP)
        addr = m.VGroup(*[T(str(1000 + 4 * i), 18, DIM).next_to(c, m.DOWN, buff=0.12) for i, c in enumerate(arr)])
        mem = T("addresses (4-byte ints)", 20, DIM).next_to(addr, m.RIGHT, buff=0.4)
        self.beat("ar1", m.LaggedStart(*[m.FadeIn(c, shift=0.15 * m.DOWN) for c in arr], lag_ratio=0.12),
                  m.AnimationGroup(m.LaggedStart(*[m.FadeIn(a) for a in addr], lag_ratio=0.1), m.FadeIn(mem)),
                  self.ptr.sweep(addr))

        idx = m.VGroup(*[T(f"i={i}", 18, ACCENT).next_to(c, m.UP, buff=0.12) for i, c in enumerate(arr)])
        formula = M(r"\text{address}(i) = \text{start} + i \times \text{size}", 0.95).move_to(0.9 * m.DOWN)
        worked = M(r"\text{address}(3) = 1000 + 3 \times 4 = 1012", 0.85, DIM).next_to(formula, m.DOWN, buff=0.3)
        o1 = badge("access by index: O(1)", GOOD).move_to(3.05 * m.DOWN)
        self.beat("ar2", m.AnimationGroup(m.FadeIn(idx), self.ptr.at(idx[3], m.UP)),
                  m.Write(formula),
                  m.AnimationGroup(m.FadeIn(worked), m.Indicate(arr[3], color=ACCENT), self.ptr.at(addr[3])),
                  m.FadeIn(o1, shift=0.2 * m.UP))
        self.fade(formula, worked, o1, idx, mem)

        slot = arr[2].get_center().copy()
        new = cell(5, 0.9, 28).set_color(ACCENT).move_to(slot + 1.4 * m.UP)
        new[1].set_color(FG)
        tail = m.VGroup(*arr[2:])  # values move; the addresses stay where they are
        a7 = T("1024", 18, DIM).next_to(addr[5], m.RIGHT, buff=0.47)
        on = badge("insert / delete: O(n)", BAD).move_to(1.6 * m.DOWN + 2.6 * m.LEFT)
        sn = badge("search (unsorted): O(n)", BAD).move_to(1.6 * m.DOWN + 2.6 * m.RIGHT)
        self.beat("ar3", m.AnimationGroup(m.FadeIn(new, shift=0.3 * m.DOWN), self.ptr.at(new, m.RIGHT)),
                  m.Succession(m.AnimationGroup(tail.animate.shift(0.9 * m.RIGHT), m.FadeIn(a7)), new.animate.move_to(slot)),
                  self.ptr.sweep(m.VGroup(*addr[2:], a7)),
                  m.FadeIn(on, shift=0.2 * m.UP),
                  m.FadeIn(sn, shift=0.2 * m.UP))
        self.clear_below()

        langs = m.VGroup(chip("Python list"), chip("Java ArrayList"), chip("C++ vector")).arrange(m.RIGHT, buff=0.3)
        langs.move_to(2.3 * m.UP)
        small = cells([1, 2, 3, 4], w=0.8).move_to(0.9 * m.UP + 3 * m.LEFT)
        cap4 = T("capacity 4: full", 20, BAD).next_to(small, m.DOWN, buff=0.15)
        big = cells(["1", "2", "3", "4", "", "", "", ""], w=0.8).move_to(1.3 * m.DOWN)
        cap8 = T("capacity 8", 20, GOOD).next_to(big, m.DOWN, buff=0.15)
        copies = [m.TransformFromCopy(small[i][1], big[i][1]) for i in range(4)]
        dbl = M(r"4 \rightarrow 8", 1.0, ACCENT).next_to(big, m.RIGHT, buff=0.5)
        self.beat("ar4", m.AnimationGroup(m.LaggedStart(*[m.FadeIn(c) for c in langs], lag_ratio=0.2), m.FadeIn(small)),
                  m.AnimationGroup(m.FadeIn(cap4), m.Indicate(small, color=BAD)),
                  m.AnimationGroup(m.FadeIn(m.VGroup(*[c[0] for c in big])), m.AnimationGroup(*copies, lag_ratio=0.2)),
                  m.AnimationGroup(m.FadeIn(cap8), m.Write(dbl)))
        self.clear_below()

        apps = m.VGroup(*[m.Square(0.48, stroke_color=DIM, stroke_width=2, fill_color=PANEL, fill_opacity=1)
                          for _ in range(16)]).arrange(m.RIGHT, buff=0.1).move_to(1.5 * m.DOWN)
        anum = m.VGroup(*[T(str(i + 1), 16, DIM).next_to(a, m.DOWN, buff=0.08) for i, a in enumerate(apps)])
        alab = T("appends", 18, DIM).next_to(anum, m.DOWN, buff=0.12)
        hits = {2: 1, 3: 2, 5: 4, 9: 8}  # the append that overflows capacity c copies c items
        bars = m.VGroup(*[m.Rectangle(width=0.44, height=0.3 * c, stroke_width=0, fill_color=ACCENT, fill_opacity=0.9)
                          .next_to(apps[k - 1], m.UP, buff=0.08) for k, c in hits.items()])
        blab = m.VGroup(*[T(str(c), 18, ACCENT).next_to(b, m.UP, buff=0.08) for b, c in zip(bars, hits.values())])
        total = M(r"1 + 2 + 4 + 8 = 15 \text{ copies}", 0.95).move_to(2.2 * m.UP + 3.9 * m.RIGHT)
        per = M(r"\frac{15}{16} < 1 \text{ copy per append}", 0.95).next_to(total, m.DOWN, buff=0.35)
        amort = badge("append: O(1) amortized", GOOD).move_to(3.15 * m.DOWN)
        self.beat("ar5", m.AnimationGroup(m.LaggedStart(*[m.FadeIn(a) for a in apps], lag_ratio=0.05), m.FadeIn(anum), m.FadeIn(alab)),
                  self.ptr.sweep(anum),
                  m.AnimationGroup(*[m.GrowFromEdge(b, m.DOWN) for b in bars], m.FadeIn(blab), m.Write(total)),
                  m.Write(per),
                  m.FadeIn(amort, shift=0.2 * m.UP))

    # ---------- 2. linked lists ----------
    def linked_lists(self):
        self.header("2 · Linked lists")
        spots = [(-5.2, 0.9), (-2.0, -0.3), (1.0, 1.1), (4.0, -0.1)]
        nodes = m.VGroup(*[lnode(v).move_to([x, y, 0]) for v, (x, y) in zip([7, 3, 9, 4], spots)])
        links = m.VGroup(*[link(a, b) for a, b in zip(nodes, nodes[1:])])
        null = T("null", 20, DIM).next_to(nodes[3], m.RIGHT, buff=0.6)
        nl = m.Arrow(nodes[3][3].get_center(), null.get_left() + 0.1 * m.LEFT, buff=0.02, color=DIM, stroke_width=3,
                     max_tip_length_to_length_ratio=0.25)
        head = T("head", 22, ACCENT).move_to(nodes[0].get_center() + 1.5 * m.UP)
        harrow = arrow(head.get_bottom(), nodes[0].get_top(), ACCENT)
        self.beat("ll1", m.LaggedStart(*[m.FadeIn(n, scale=0.8) for n in nodes], lag_ratio=0.25),
                  m.AnimationGroup(m.LaggedStart(*[m.GrowArrow(a) for a in links], lag_ratio=0.3), m.GrowArrow(nl), m.FadeIn(null)),
                  self.ptr.circle(nodes[1]),
                  m.AnimationGroup(m.FadeIn(head), m.GrowArrow(harrow)))

        q = T("4th element?", 20, ACCENT).next_to(nodes[3], m.UP, buff=0.3)
        walk = m.LaggedStart(*[m.Indicate(n, color=ACCENT) for n in nodes], lag_ratio=0.7)
        on = badge("access / search: O(n)", BAD).move_to(2.6 * m.DOWN)
        self.beat("ll2", m.AnimationGroup(m.FadeIn(q), self.ptr.at(nodes[3], m.DOWN)),
                  m.AnimationGroup(walk, self.ptr.sweep(m.VGroup(nodes[0], nodes[3]))),
                  m.FadeIn(on, shift=0.2 * m.UP))
        self.fade(q, on)

        new = lnode(5).move_to([-0.5, -2.2, 0])
        new[0].set_stroke(ACCENT)
        to_next = link(new, nodes[2], ACCENT)
        to_new = link(nodes[1], new, ACCENT)
        o1 = badge("insert after a node you hold: O(1)", GOOD).move_to(3.2 * m.DOWN + 3.6 * m.RIGHT)
        self.beat("ll3", m.AnimationGroup(nodes[1][0].animate.set_stroke(ACCENT), self.ptr.at(nodes[1], m.DOWN)),
                  m.FadeIn(new, shift=0.2 * m.UP),
                  m.GrowArrow(to_next),
                  m.ReplacementTransform(links[1], to_new),
                  m.FadeIn(o1, shift=0.2 * m.UP))
        self.clear_below()

        big = lnode(7).scale(1.6).move_to(1.3 * m.UP + 3.5 * m.LEFT)
        ptrlab = T("+ one pointer per node", 20, BAD).next_to(big, m.DOWN, buff=0.25)
        cache = card("nodes scattered in memory\n→ cache misses", BAD, 22).move_to(1.3 * m.UP + 3.2 * m.RIGHT)
        dn = m.VGroup(*[lnode(v) for v in "ABC"]).arrange(m.RIGHT, buff=1.0).move_to(1.3 * m.DOWN)
        fw = m.VGroup(*[arrow(a.get_right() + 0.15 * m.UP, b.get_left() + 0.15 * m.UP) for a, b in zip(dn, dn[1:])])
        bw = m.VGroup(*[arrow(b.get_left() + 0.15 * m.DOWN, a.get_right() + 0.15 * m.DOWN, BLUE) for a, b in zip(dn, dn[1:])])
        dlab = T("doubly linked", 20, BLUE).next_to(dn, m.LEFT, buff=0.4)
        skip_f = m.CurvedArrow(dn[0].get_top(), dn[2].get_top(), angle=-0.8, color=GOOD)
        skip_b = m.CurvedArrow(dn[2].get_bottom(), dn[0].get_bottom(), angle=-0.8, color=GOOD)
        lru = card("hash map + doubly linked list = LRU cache", ACCENT, 22).move_to(3.2 * m.DOWN)
        self.beat("ll4", m.AnimationGroup(m.FadeIn(big), m.FadeIn(ptrlab), self.ptr.at(big[2], m.UP)),
                  m.FadeIn(cache, shift=0.2 * m.UP),
                  m.AnimationGroup(m.FadeIn(dn), m.FadeIn(fw), m.FadeIn(bw), m.FadeIn(dlab)),
                  m.AnimationGroup(m.FadeOut(dn[1]), m.FadeOut(fw), m.FadeOut(bw), m.Create(skip_f), m.Create(skip_b)),
                  m.FadeIn(lru, shift=0.2 * m.UP))

    # ---------- 3. stacks and queues ----------
    def stacks_queues(self):
        self.header("3 · Stacks and queues")
        base = 1.6 * m.DOWN + 3.6 * m.LEFT
        walls = m.VGroup(m.Line(base + 0.65 * m.LEFT + 3.0 * m.UP, base + 0.65 * m.LEFT, color=DIM, stroke_width=4),
                         m.Line(base + 0.65 * m.LEFT, base + 0.65 * m.RIGHT, color=DIM, stroke_width=4),
                         m.Line(base + 0.65 * m.RIGHT, base + 0.65 * m.RIGHT + 3.0 * m.UP, color=DIM, stroke_width=4))
        items = [cell(c, 1.1, 26) for c in "ABC"]
        for i, it in enumerate(items):
            it.move_to(base + (0.6 + 0.62 * i) * m.UP)
            it[0].stretch_to_fit_height(0.56)
        stack = m.VGroup(*items)
        slab = T("stack", 24, ACCENT).next_to(walls, m.DOWN, buff=0.25)
        d = cell("D", 1.1, 26)
        d[0].stretch_to_fit_height(0.56)
        d.move_to(base + 3.6 * m.UP)
        dpos = base + (0.6 + 0.62 * 3) * m.UP
        o1 = badge("push / pop / peek: O(1)", GOOD).move_to(3.2 * m.DOWN + 3.6 * m.LEFT)
        self.beat("sq1", m.AnimationGroup(m.Create(walls), m.FadeIn(stack), m.FadeIn(slab)),
                  m.Succession(m.FadeIn(d), d.animate.move_to(dpos)),
                  d.animate.shift(2.0 * m.UP).set_opacity(0),
                  m.FadeIn(o1, shift=0.2 * m.UP),
                  self.ptr.at(items[2], m.RIGHT))
        self.remove(d)

        uses = m.VGroup(card("undo", FG, 22), card("function call stack", FG, 22), card("balanced brackets:  ( [ ] )", FG, 22))
        uses.arrange(m.DOWN, buff=0.35, aligned_edge=m.LEFT).move_to(1.0 * m.UP + 2.6 * m.RIGHT)
        rule = T("push on  ( [   ·   pop on  ] )", 22, ACCENT).next_to(uses, m.DOWN, buff=0.4)
        self.beat("sq2", *[m.FadeIn(u, shift=0.2 * m.LEFT) for u in uses],
                  m.AnimationGroup(m.FadeIn(rule), self.ptr.at(uses[2], m.RIGHT)))
        self.clear_below()

        q = m.VGroup(*[cell(c, 0.9, 26) for c in "ABC"]).arrange(m.RIGHT, buff=0.08).move_to(1.4 * m.UP)
        front = T("front", 20, BLUE).next_to(q, m.LEFT, buff=0.4)
        back = T("back", 20, BLUE).next_to(q, m.RIGHT, buff=1.3)
        qlab = T("queue", 24, ACCENT).next_to(q, m.UP, buff=0.35)
        dq = cell("D", 0.9, 26).next_to(q[2], m.RIGHT, buff=0.08).shift(0.5 * m.LEFT + 1.1 * m.UP)
        o1 = badge("enqueue / dequeue: O(1)", GOOD).move_to(0.2 * m.DOWN)
        self.beat("sq3", m.AnimationGroup(m.FadeIn(q), m.FadeIn(qlab), m.FadeIn(front), m.FadeIn(back)),
                  self.ptr.sweep(q),
                  m.Succession(m.AnimationGroup(m.FadeIn(dq), q.animate.shift(0.5 * m.LEFT)), dq.animate.shift(1.1 * m.DOWN)),
                  m.AnimationGroup(q[0].animate.shift(1.0 * m.LEFT).set_opacity(0), front.animate.shift(0.48 * m.RIGHT)),
                  m.FadeIn(o1, shift=0.2 * m.UP))
        self.fade(o1)

        plain = cells("ABCDE", w=0.8).move_to(1.0 * m.DOWN + 2.5 * m.LEFT)
        plab = T("plain array", 20, DIM).next_to(plain, m.LEFT, buff=0.3)
        shift_lab = T("everything shifts: O(n)", 22, BAD).next_to(plain, m.DOWN, buff=0.3)
        fix = card("deque / ring buffer\nO(1) at both ends", GOOD, 22).move_to(1.0 * m.DOWN + 3.8 * m.RIGHT)
        bfs = card("breadth-first search", BLUE, 22).move_to(3.1 * m.DOWN + 2.0 * m.LEFT)
        sched = card("task scheduling", BLUE, 22).move_to(3.1 * m.DOWN + 2.4 * m.RIGHT)
        self.beat("sq4", m.Succession(m.AnimationGroup(m.FadeIn(plain), m.FadeIn(plab)), m.FadeOut(plain[0], shift=0.4 * m.UP)),
                  m.AnimationGroup(m.VGroup(*plain[1:]).animate.shift(0.86 * m.LEFT), m.FadeIn(shift_lab)),
                  m.FadeIn(fix, shift=0.2 * m.LEFT),
                  m.FadeIn(bfs, shift=0.2 * m.UP),
                  m.FadeIn(sched, shift=0.2 * m.UP))

    # ---------- 4. hash tables ----------
    def hash_tables(self):
        self.header("4 · Hash tables")
        buckets = m.VGroup(*[m.Rectangle(width=1.0, height=0.6, stroke_color=DIM, stroke_width=2, fill_color=PANEL,
                                         fill_opacity=1) for _ in range(8)]).arrange(m.RIGHT, buff=0.12)
        buckets.move_to(0.4 * m.DOWN)
        bidx = m.VGroup(*[T(str(i), 18, DIM).move_to(b) for i, b in enumerate(buckets)])
        blab = T("8 buckets", 20, DIM).next_to(buckets, m.LEFT, buff=0.3)
        table = m.VGroup(buckets, bidx, blab)
        cat = chip("cat", ACCENT).move_to(1.9 * m.UP + 5.0 * m.LEFT)
        fn = card("hash(\"cat\")", FG, 22).move_to(1.9 * m.UP + 2.0 * m.LEFT)
        num = T("98262", 30, BLUE).move_to(1.9 * m.UP + 1.2 * m.RIGHT)
        a1, a2 = arrow(cat.get_right(), fn.get_left()), arrow(fn.get_right(), num.get_left())
        note = T("hash = Java's String.hashCode", 16, DIM).next_to(fn, m.UP, buff=0.2)
        mod = M(r"98262 \bmod 8", 1.0).move_to(1.9 * m.UP + 4.2 * m.RIGHT)
        six = M(r"= 6", 1.0, ACCENT).next_to(mod, m.RIGHT, buff=0.2)
        cat_in = chip("cat", ACCENT).next_to(buckets[6], m.DOWN, buff=0.15)
        self.beat("ha1", m.AnimationGroup(m.FadeIn(table)),
                  m.FadeIn(cat, shift=0.2 * m.RIGHT),
                  m.AnimationGroup(m.FadeIn(fn), m.GrowArrow(a1), m.GrowArrow(a2), m.FadeIn(num), m.FadeIn(note)),
                  m.Write(mod),
                  m.FadeIn(six),
                  m.AnimationGroup(m.TransformFromCopy(cat, cat_in), buckets[6].animate.set_stroke(ACCENT)))

        o1 = badge("insert / lookup / delete: O(1) on average", GOOD).move_to(3.1 * m.DOWN)
        self.beat("ha2", m.AnimationGroup(m.Indicate(fn, color=ACCENT), self.ptr.at(fn, m.DOWN)),
                  self.ptr.at(cat_in, m.DOWN),
                  m.FadeIn(o1, shift=0.2 * m.UP))
        self.fade(cat, fn, num, a1, a2, note, mod, six, o1)

        dog = chip("dog").next_to(buckets[4], m.DOWN, buff=0.15)
        owl = chip("owl").next_to(dog, m.DOWN, buff=0.3)
        dh = T("dog → 99644 mod 8 = 4", 22, FG, MONO).move_to(2.2 * m.UP + 3.0 * m.LEFT)
        oh = T("owl → 110468 mod 8 = 4", 22, FG, MONO).next_to(dh, m.DOWN, buff=0.2, aligned_edge=m.LEFT)
        coll = T("collision", 24, BAD).move_to(1.7 * m.UP + 3.6 * m.RIGHT)
        chain = arrow(dog.get_bottom(), owl.get_top(), BLUE, buff=0.03)
        self.beat("ha3", m.AnimationGroup(m.FadeIn(dh), m.FadeIn(dog, shift=0.2 * m.DOWN)),
                  m.FadeIn(oh),
                  m.AnimationGroup(m.FadeIn(coll), buckets[4].animate.set_stroke(BAD), m.Indicate(m.VGroup(dh, oh), color=BAD)),
                  m.AnimationGroup(m.FadeIn(owl, shift=0.2 * m.DOWN), m.GrowArrow(chain)),
                  self.ptr.at(owl, m.RIGHT))
        self.fade(dh, oh, coll)

        more = [("bee", 2, 0), ("fox", 7, 0), ("ant", 7, 1)]
        extra = m.VGroup()
        for k, b, depth in more:
            c = chip(k)
            c.next_to(buckets[b], m.DOWN, buff=0.15)
            if depth:
                c.next_to(extra[-1], m.DOWN, buff=0.3)
            extra.add(c)
        fchain = arrow(extra[1].get_bottom(), extra[2].get_top(), BLUE, buff=0.03)
        lf = M(r"\text{load factor} = \frac{\text{items}}{\text{buckets}}", 0.95).move_to(2.1 * m.UP + 3.3 * m.LEFT)
        val = M(r"= \frac{6}{8} = 0.75", 0.95, ACCENT).next_to(lf, m.RIGHT, buff=0.25)
        grow = T("over the threshold: 8 → 16 buckets, rehash all", 22, ACCENT).move_to(0.75 * m.UP + 1.0 * m.RIGHT)
        java = chip("Java HashMap: resize past 0.75", FG, 20).move_to(3.25 * m.DOWN + 3.0 * m.LEFT)
        py = chip("Python dict: past 2/3", FG, 20).move_to(3.25 * m.DOWN + 3.0 * m.RIGHT)
        self.beat("ha4", m.Write(lf),
                  m.AnimationGroup(m.LaggedStart(*[m.FadeIn(c, shift=0.2 * m.DOWN) for c in extra], lag_ratio=0.3), m.GrowArrow(fchain)),
                  m.Write(val),
                  m.AnimationGroup(m.FadeIn(grow), m.Indicate(buckets, color=ACCENT)),
                  m.FadeIn(java, shift=0.2 * m.UP),
                  m.FadeIn(py, shift=0.2 * m.UP))
        self.clear_below()

        wb = m.VGroup(*[m.Rectangle(width=0.7, height=0.5, stroke_color=DIM, stroke_width=2, fill_color=PANEL, fill_opacity=1)
                        for _ in range(8)]).arrange(m.RIGHT, buff=0.08).move_to(2.0 * m.UP + 3.3 * m.LEFT)
        wb[2].set_stroke(BAD)
        pile = m.VGroup(*[chip(k, BAD, 18) for k in ["k1", "k2", "k3", "k4", "k5"]]).arrange(m.DOWN, buff=0.1)
        pile.next_to(wb[2], m.DOWN, buff=0.15)
        on = badge("worst case: O(n)", BAD).next_to(pile, m.RIGHT, buff=1.2)
        order = card("keys come out in bucket order,\nnot sorted order", FG, 22).move_to(1.4 * m.UP + 3.6 * m.RIGHT)
        nomin = T("min?  range [c, f]?  →  scan all n", 24, BAD).move_to(2.3 * m.DOWN + 3.0 * m.RIGHT)
        self.beat("ha5", m.AnimationGroup(m.FadeIn(wb), m.LaggedStart(*[m.FadeIn(c, shift=0.2 * m.DOWN) for c in pile], lag_ratio=0.2)),
                  m.FadeIn(on, shift=0.2 * m.UP),
                  m.FadeIn(order, shift=0.2 * m.LEFT),
                  m.FadeIn(nomin))

    # ---------- 5. binary search trees ----------
    def tree(self, vals, pos, r=0.36):
        ns = [node(v, r).move_to(p) for v, p in zip(vals, pos)]
        es = {}
        for i in range(1, len(ns)):
            es[i] = edge(ns[(i - 1) // 2], ns[i], r=r)
        return ns, es

    def bsts(self):
        self.header("5 · Binary search trees")
        pos = [[0, 2.0, 0], [-3, 0.8, 0], [3, 0.8, 0], [-4.5, -0.5, 0], [-1.5, -0.5, 0], [1.5, -0.5, 0], [4.5, -0.5, 0]]
        ns, es = self.tree([50, 30, 70, 20, 40, 60, 80], pos)
        left = T("< 50", 22, BLUE).move_to([-3, 1.85, 0])
        right = T("> 50", 22, ACCENT).move_to([3, 1.85, 0])
        self.beat("bs1", m.FadeIn(ns[0], scale=0.8),
                  m.AnimationGroup(m.Create(es[1]), m.FadeIn(ns[1]), m.FadeIn(left)),
                  m.AnimationGroup(m.Create(es[2]), m.FadeIn(ns[2]), m.FadeIn(right)),
                  m.LaggedStart(*[m.AnimationGroup(m.Create(es[i]), m.FadeIn(ns[i])) for i in range(3, 7)], lag_ratio=0.4))

        goal = chip("find 60", ACCENT, 22).move_to([5.3, 2.4, 0])
        lv = m.VGroup(*[T(f"level {i + 1}", 18, DIM).move_to([-5.9, y, 0]) for i, y in enumerate([2.0, 0.8, -0.5])])
        self.beat("bs2", m.FadeIn(goal, shift=0.2 * m.LEFT),
                  m.AnimationGroup(self.ptr.at(ns[0], m.LEFT), ns[0][0].animate.set_stroke(ACCENT)),
                  m.AnimationGroup(self.ptr.at(ns[2], m.RIGHT), es[2].animate.set_color(ACCENT), ns[2][0].animate.set_stroke(ACCENT)),
                  m.AnimationGroup(self.ptr.at(ns[5], m.DOWN), es[5].animate.set_color(ACCENT), ns[5][0].animate.set_fill(GOOD, 0.6)),
                  m.LaggedStart(*[m.FadeIn(x) for x in lv], lag_ratio=0.3))

        hb = m.Brace(m.VGroup(*lv), m.LEFT, color=ACCENT)
        hl = T("height h", 20, ACCENT).next_to(lv, m.DOWN, buff=0.3)
        f1 = M(r"h \approx \log_2 n", 1.0).move_to([-3.2, -2.1, 0])
        f2 = M(r"n = 1{,}000{,}000", 1.0).move_to([1.6, -2.1, 0])
        f3 = M(r"\log_2 10^6 \approx 19.9 \;\Rightarrow\; \text{about 20 levels}", 0.95, GOOD).move_to([0, -3.1, 0])
        self.beat("bs3", m.AnimationGroup(m.GrowFromCenter(hb), m.FadeIn(hl)),
                  m.Write(f1),
                  m.Write(f2),
                  m.Write(f3))
        self.clear_below()

        ins = T("insert 10, 20, 30, 40, 50", 24, FG).move_to([-3.5, 2.4, 0])
        cpos = [[-5.5 + 1.0 * i, 1.4 - 0.85 * i, 0] for i in range(5)]
        chain = [node(v, 0.32, size=20).move_to(p) for v, p in zip([10, 20, 30, 40, 50], cpos)]
        ce = [edge(a, b, r=0.32) for a, b in zip(chain, chain[1:])]
        cg = m.VGroup(*chain, *ce)
        on = badge("height n → O(n)", BAD).move_to([-3.5, -3.1, 0])
        bpos = [[3.5, 1.3, 0], [2.2, 0.1, 0], [4.8, 0.1, 0], [1.5, -1.1, 0], [5.5, -1.1, 0]]
        bal = [node(v, 0.32, GOOD, 20).move_to(p) for v, p in zip([30, 20, 40, 10, 50], bpos)]
        be = [edge(bal[a], bal[b], r=0.32) for a, b in [(0, 1), (0, 2), (1, 3), (2, 4)]]
        blab = T("red-black / AVL", 22, GOOD).move_to([3.5, 2.4, 0])
        rot = T("rotations keep h = O(log n)", 22, GOOD).move_to([3.5, -2.2, 0])
        self.beat("bs4", m.FadeIn(ins),
                  m.LaggedStart(*[m.FadeIn(x) for pair in zip(chain, [None] + ce) for x in pair if x is not None], lag_ratio=0.3),
                  self.ptr.sweep(cg),
                  m.FadeIn(on, shift=0.2 * m.UP),
                  m.AnimationGroup(m.FadeIn(blab), *[m.FadeIn(n) for n in bal], *[m.Create(e) for e in be]),
                  m.AnimationGroup(m.FadeIn(rot), m.Indicate(bal[0], color=GOOD)))
        self.clear_below()

        pos2 = [[0, 2.0, 0], [-2.6, 1.0, 0], [2.6, 1.0, 0], [-3.9, 0.0, 0], [-1.3, 0.0, 0], [1.3, 0.0, 0], [3.9, 0.0, 0]]
        ns2, es2 = self.tree([50, 30, 70, 20, 40, 60, 80], pos2, 0.32)
        tgrp = m.VGroup(*ns2, *es2.values())
        inorder = [3, 1, 4, 0, 5, 2, 6]
        row = cells([20, 30, 40, 50, 60, 70, 80], w=0.75).move_to(1.5 * m.DOWN)
        rng = m.SurroundingRectangle(m.VGroup(*row[2:5]), color=ACCENT, buff=0.08)
        rlab = T("range 40..60", 20, ACCENT).next_to(rng, m.DOWN, buff=0.15)
        tm = card("Java TreeMap = red-black tree", BLUE, 22).move_to(3.1 * m.DOWN)
        self.beat("bs5", m.FadeIn(tgrp),
                  m.LaggedStart(*[m.Indicate(ns2[i], color=ACCENT) for i in inorder], lag_ratio=0.5),
                  m.LaggedStart(*[m.AnimationGroup(m.FadeIn(row[k][0]), m.TransformFromCopy(ns2[i][1], row[k][1]))
                                  for k, i in enumerate(inorder)], lag_ratio=0.3),
                  m.AnimationGroup(m.Create(rng), m.FadeIn(rlab)),
                  m.FadeIn(tm, shift=0.2 * m.UP))

    # ---------- 6. heaps ----------
    def heaps(self):
        self.header("6 · Heaps")
        tp = [[0, 2.1, 0], [-2.6, 1.05, 0], [2.6, 1.05, 0], [-3.9, 0.0, 0], [-1.3, 0.0, 0], [1.3, 0.0, 0], [3.9, 0.0, 0]]
        vals = [3, 5, 9, 6, 7, 10]
        circ = [m.Circle(radius=0.34, stroke_color=FG, stroke_width=3, fill_color=PANEL, fill_opacity=1).move_to(p) for p in tp]
        tl = [T(str(v), 24).move_to(tp[i]) for i, v in enumerate(vals)]
        es = {i: edge(circ[(i - 1) // 2], circ[i], r=0.34) for i in range(1, 7)}
        tree6 = m.VGroup(*circ[:6], *tl, *[es[i] for i in range(1, 6)])
        q = chip("smallest?", ACCENT, 22).move_to([4.6, 2.4, 0])
        o1 = badge("peek min: O(1)", GOOD).move_to([4.6, 1.3, 0]).scale(0.9)
        self.beat("hp1", m.FadeIn(tree6),
                  m.FadeIn(q, shift=0.2 * m.LEFT),
                  m.AnimationGroup(*[m.Indicate(es[i], color=BLUE) for i in range(1, 6)], self.ptr.at(es[1], m.LEFT)),
                  m.AnimationGroup(self.ptr.at(circ[0], m.UP), circ[0].animate.set_stroke(GOOD)),
                  m.FadeIn(o1, shift=0.2 * m.UP))

        ap = [[-3.3 + 0.95 * i, -1.7, 0] for i in range(7)]
        boxes = [m.Square(0.8, stroke_color=DIM, stroke_width=2, fill_color=PANEL, fill_opacity=1).move_to(p) for p in ap]
        al = [T(str(v), 24).move_to(ap[i]) for i, v in enumerate(vals)]
        ai = m.VGroup(*[T(str(i), 16, DIM).next_to(b, m.DOWN, buff=0.08) for i, b in enumerate(boxes)])
        kids = M(r"\text{children of } i:\; 2i+1,\; 2i+2", 0.9).move_to([0, -3.15, 0])
        c1 = m.CurvedArrow(boxes[1].get_top(), boxes[3].get_top(), angle=-1.2, color=BLUE)
        c2 = m.CurvedArrow(boxes[1].get_top(), boxes[4].get_top(), angle=-1.2, color=BLUE)
        self.beat("hp2", self.ptr.circle(tree6),
                  m.AnimationGroup(*[m.FadeIn(b) for b in boxes[:6]], *[m.TransformFromCopy(t, a) for t, a in zip(tl, al)], m.FadeIn(ai[:6])),
                  m.AnimationGroup(m.Write(kids), m.Create(c1), m.Create(c2)),
                  self.ptr.sweep(m.VGroup(*boxes[:6])))
        self.fade(c1, c2, kids, q, o1)

        def swap(i, j):
            tl[i], tl[j] = tl[j], tl[i]
            al[i], al[j] = al[j], al[i]
            return m.AnimationGroup(tl[i].animate.move_to(tp[i]), tl[j].animate.move_to(tp[j]),
                                    al[i].animate.move_to(ap[i]), al[j].animate.move_to(ap[j]))

        tl.append(T("2", 24, ACCENT).move_to(tp[6]))
        al.append(T("2", 24, ACCENT).move_to(ap[6]))
        rule = T("while smaller than parent: swap up", 22, ACCENT).move_to([-4.2, 2.6, 0])
        lv = m.Brace(m.VGroup(circ[0], circ[6]), m.RIGHT, color=BLUE)
        lvl = T("≤ one swap per level", 20, BLUE).next_to(lv, m.DOWN, buff=0.15)
        ol = badge("push: O(log n)", GOOD).move_to([4.6, -3.1, 0])
        self.beat("hp3", m.AnimationGroup(m.FadeIn(circ[6]), m.Create(es[6]), m.FadeIn(tl[6]), m.FadeIn(boxes[6]), m.FadeIn(al[6]), m.FadeIn(ai[6])),
                  m.FadeIn(rule),
                  self.ptr.at(circ[6], m.DOWN),
                  m.AnimationGroup(swap(6, 2), self.ptr.at(circ[2], m.DOWN)),
                  m.AnimationGroup(swap(2, 0), self.ptr.at(circ[0], m.UP)),
                  m.AnimationGroup(m.GrowFromCenter(lv), m.FadeIn(lvl)),
                  m.FadeIn(ol, shift=0.2 * m.UP))
        self.fade(rule, lv, lvl, ol)
        self.play(self.ptr.hide())

        # heap is now [2, 5, 3, 6, 7, 10, 9]
        gone_t, gone_a = tl[0], al[0]
        down = T("sift down: swap with the smaller child", 22, ACCENT).move_to([4.2, 2.6, 0])
        olog = badge("pop: O(log n)", GOOD).move_to([-4.6, -3.1, 0])
        hfy = T("heapify (build from n items)", 22, FG).move_to([2.0, -3.1, 0])
        on = badge("O(n)", GOOD).next_to(hfy, m.RIGHT, buff=0.3)

        def last_to_top():
            tl[0], al[0] = tl[6], al[6]
            return m.AnimationGroup(tl[0].animate.move_to(tp[0]).set_color(FG), al[0].animate.move_to(ap[0]).set_color(FG),
                                    m.FadeOut(circ[6]), m.FadeOut(es[6]), m.FadeOut(boxes[6]), m.FadeOut(ai[6]))

        self.beat("hp4", m.AnimationGroup(m.FadeOut(gone_t, shift=0.5 * m.UP), m.FadeOut(gone_a, shift=0.5 * m.UP)),
                  last_to_top(),
                  m.AnimationGroup(m.FadeIn(down), swap(0, 2)),
                  m.FadeIn(olog, shift=0.2 * m.UP),
                  m.FadeIn(hfy),
                  m.FadeIn(on, shift=0.2 * m.UP))
        self.clear_below()

        uses = m.VGroup(card("Dijkstra's shortest paths", BLUE, 22), card("schedulers", BLUE, 22), card("merging sorted lists", BLUE, 22))
        uses.arrange(m.RIGHT, buff=0.35).move_to(2.2 * m.UP)
        data = [5, 17, 2, 9, 21, 4, 13, 8, 30, 1, 11, 19]
        drow = cells(data, w=0.62, size=22).move_to(0.6 * m.DOWN)
        top = {21, 30, 19}
        dlab = T("n = 12 items, want the k = 3 largest", 20, DIM).next_to(drow, m.UP, buff=0.2)
        heap = cells([19, 21, 30], w=0.75).move_to(2.2 * m.DOWN + 1.5 * m.LEFT)
        hlab = T("min-heap of size k", 20, ACCENT).next_to(heap, m.LEFT, buff=0.3)
        cost = M(r"O(n \log k)", 1.1, GOOD).next_to(heap, m.RIGHT, buff=0.8)
        pq = T("heap = priority queue", 26, ACCENT).move_to(3.15 * m.DOWN + 3.6 * m.RIGHT)
        self.beat("hp5", m.FadeIn(pq),
                  m.FadeIn(uses[0], shift=0.2 * m.UP),
                  m.FadeIn(uses[1], shift=0.2 * m.UP),
                  m.FadeIn(uses[2], shift=0.2 * m.UP),
                  m.AnimationGroup(m.FadeIn(drow), m.FadeIn(dlab)),
                  m.AnimationGroup(m.FadeIn(heap), m.FadeIn(hlab), *[c[0].animate.set_stroke(ACCENT) for c, v in zip(drow, data) if v in top]),
                  m.Write(cost))

    # ---------- 7. graphs ----------
    def graphs(self):
        self.header("7 · Graphs")
        names = "ABCDE"
        gp = {"A": [-5.4, 1.2, 0], "B": [-3.6, 2.1, 0], "C": [-3.6, 0.1, 0], "D": [-1.8, 1.2, 0], "E": [-1.0, -0.8, 0]}
        vs = {k: node(k, 0.34).move_to(p) for k, p in gp.items()}
        E = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("D", "E")]
        es = m.VGroup(*[edge(vs[a], vs[b], r=0.34) for a, b in E])
        V = m.VGroup(*vs.values())
        p1, p2 = card("page 1", FG, 20), card("page 2", FG, 20)
        m.VGroup(p1, p2).arrange(m.RIGHT, buff=1.4).move_to([3.6, 1.6, 0])
        da = arrow(p1.get_right(), p2.get_left(), ACCENT)
        c1, c2 = card("Boston", FG, 20), card("NYC", FG, 20)
        m.VGroup(c1, c2).arrange(m.RIGHT, buff=2.3).move_to([3.6, -0.2, 0])
        wl = m.Line(c1.get_right(), c2.get_left(), color=BLUE, stroke_width=4)
        w = T("weight 306 km", 18, BLUE).next_to(wl, m.UP, buff=0.12)
        self.beat("gr1", m.FadeIn(V, scale=0.8),
                  m.LaggedStart(*[m.Indicate(v, color=ACCENT) for v in V], lag_ratio=0.2),
                  m.LaggedStart(*[m.Create(e) for e in es], lag_ratio=0.2),
                  m.AnimationGroup(m.FadeIn(p1), m.FadeIn(p2), m.GrowArrow(da)),
                  m.AnimationGroup(m.FadeIn(c1), m.FadeIn(c2), m.Create(wl), m.FadeIn(w)))
        self.fade(p1, p2, da, c1, c2, wl, w)

        adj = {(a, b) for a, b in E} | {(b, a) for a, b in E}
        grid = m.VGroup()
        for r, a in enumerate(names):
            for c, b in enumerate(names):
                grid.add(cell(0, 0.55, 20).move_to([1.6 + 0.6 * c, 1.6 - 0.6 * r, 0]))
        rl = m.VGroup(*[T(n, 20, DIM).move_to([1.0, 1.6 - 0.6 * i, 0]) for i, n in enumerate(names)])
        cl = m.VGroup(*[T(n, 20, DIM).move_to([1.6 + 0.6 * i, 2.2, 0]) for i, n in enumerate(names)])
        mlab = T("adjacency matrix", 22, ACCENT).move_to([5.6, 2.2, 0])
        ones = [grid[5 * names.index(a) + names.index(b)] for a, b in sorted(adj)]
        new1 = [T("1", 20, GOOD).move_to(o) for o in ones]
        ab = grid[1]
        o1 = chip("edge A–B?  O(1)", GOOD, 20).move_to([5.6, 1.2, 0])
        sq = chip("space O(V²)", BAD, 20).move_to([5.6, 0.4, 0])
        zeros = [g for g in grid if g not in ones]
        self.beat("gr2", m.AnimationGroup(m.FadeIn(grid), m.FadeIn(rl), m.FadeIn(cl), m.FadeIn(mlab)),
                  m.Indicate(grid, color=ACCENT, scale_factor=1.04),
                  m.AnimationGroup(*[m.Transform(o[1], n) for o, n in zip(ones, new1)], lag_ratio=0.1),
                  m.AnimationGroup(ab[0].animate.set_stroke(GOOD, 5), m.Indicate(ab, color=GOOD), m.FadeIn(o1)),
                  m.FadeIn(sq, shift=0.2 * m.UP),
                  m.AnimationGroup(*[m.Indicate(z[1], color=BAD) for z in zeros]))
        mat = m.VGroup(grid, rl, cl, mlab, o1, sq)

        lst = m.VGroup(*[T(f"{a}:  " + "  ".join(b for b in names if (a, b) in adj), 24, FG, MONO) for a in names])
        lst.arrange(m.DOWN, buff=0.25, aligned_edge=m.LEFT).move_to([3.0, 0.6, 0])
        llab = T("adjacency list", 22, ACCENT).next_to(lst, m.UP, buff=0.3)
        ve = badge("space O(V + E)", GOOD).move_to([3.0, -2.2, 0])
        sp = T("sparse: E is far below V²", 22, DIM).next_to(ve, m.DOWN, buff=0.25)
        self.beat("gr3", m.AnimationGroup(m.FadeOut(mat), m.FadeIn(llab)),
                  m.LaggedStart(*[m.FadeIn(x, shift=0.2 * m.RIGHT) for x in lst], lag_ratio=0.25),
                  m.FadeIn(ve, shift=0.2 * m.UP),
                  m.FadeIn(sp))
        self.fade(lst, llab, ve, sp)

        cost = badge("both: O(V + E)", GOOD).move_to([3.4, 2.5, 0])
        bl = T("BFS", 26, BLUE).move_to([1.4, 1.3, 0])
        qrow = cells("A", w=0.5, size=18).next_to(bl, m.RIGHT, buff=0.3)
        qlab = T("queue", 18, DIM).next_to(qrow, m.RIGHT, buff=0.2)
        levels = [["A"], ["B", "C"], ["D"], ["E"]]
        lcol = [ACCENT, BLUE, GOOD, "#D787FF"]
        sp = T("A → E: 3 edges, the fewest", 22, BLUE).move_to([3.6, 0.4, 0])
        dl = T("DFS", 26, "#D787FF").move_to([1.4, -1.0, 0])
        srow = m.VGroup(*[cell(c, 0.5, 18) for c in "AB"]).arrange(m.UP, buff=0.04).next_to(dl, m.RIGHT, buff=0.3)
        slab = T("stack / recursion", 18, DIM).next_to(srow, m.RIGHT, buff=0.2)
        deep = T("A → B → D → C, then back for E", 22, "#D787FF").move_to([3.6, -2.4, 0])
        self.beat("gr4", m.FadeIn(cost, shift=0.2 * m.DOWN),
                  m.FadeIn(bl),
                  m.AnimationGroup(m.FadeIn(qrow), m.FadeIn(qlab)),
                  m.LaggedStart(*[m.AnimationGroup(*[vs[k][0].animate.set_stroke(c) for k in lev]) for lev, c in zip(levels, lcol)], lag_ratio=0.6),
                  m.FadeIn(sp),
                  m.FadeIn(dl),
                  m.AnimationGroup(m.FadeIn(srow), m.FadeIn(slab)),
                  m.AnimationGroup(m.LaggedStart(*[m.Indicate(vs[k], color="#D787FF") for k in "ABDCE"], lag_ratio=0.5), m.FadeIn(deep)))

    # ---------- 8. tries ----------
    def tries(self):
        self.header("8 · Tries")
        P = {"root": [0, 2.3, 0], "c": [-2.2, 1.3, 0], "d": [2.4, 1.3, 0], "ca": [-2.2, 0.2, 0], "do": [2.4, 0.2, 0],
             "car": [-3.3, -0.9, 0], "cat": [-1.1, -0.9, 0], "dog": [2.4, -0.9, 0], "cart": [-3.3, -2.0, 0]}
        parent = {"c": "root", "d": "root", "ca": "c", "do": "d", "car": "ca", "cat": "ca", "dog": "do", "cart": "car"}
        tn = {k: node("" if k == "root" else k[-1], 0.32, size=24).move_to(p) for k, p in P.items()}
        te = {k: edge(tn[p], tn[k], r=0.32) for k, p in parent.items()}
        trie = m.VGroup(*tn.values(), *te.values())
        ends = ["car", "cat", "dog", "cart"]
        words = m.VGroup(*[T(w, 24, GOOD).next_to(tn[w], m.RIGHT if w != "car" else m.LEFT, buff=0.2) for w in ends])
        words[0].shift(0.3 * m.UP)
        self.beat("tr1", m.FadeIn(trie),
                  m.AnimationGroup(self.ptr.at(tn["ca"], m.RIGHT), tn["c"][0].animate.set_stroke(ACCENT), tn["ca"][0].animate.set_stroke(ACCENT),
                                   te["c"].animate.set_color(ACCENT), te["ca"].animate.set_color(ACCENT)),
                  m.AnimationGroup(*[tn[w][0].animate.set_fill(GOOD, 0.45) for w in ends]),
                  m.LaggedStart(*[m.FadeIn(w) for w in words], lag_ratio=0.3))

        L = T("cart: L = 4", 24, FG).move_to([4.4, 2.5, 0])
        steps = m.LaggedStart(*[m.Indicate(tn[k], color=ACCENT) for k in ["c", "ca", "car", "cart"]], lag_ratio=0.6)
        indep = T("doesn't depend on how many words", 20, DIM).next_to(L, m.DOWN, buff=0.2)
        sub = m.VGroup(tn["ca"], tn["car"], tn["cat"], tn["cart"])
        auto = card("\"ca\" → car, cart, cat", BLUE, 22).move_to([4.4, -2.1, 0])
        mem = T("cost: one node per character", 22, BAD).move_to([4.4, -3.2, 0])
        self.beat("tr2", m.FadeIn(L),
                  m.AnimationGroup(steps, self.ptr.at(tn["cart"], m.RIGHT)),
                  m.FadeIn(indep),
                  self.ptr.at(tn["ca"], m.RIGHT),
                  m.AnimationGroup(m.Create(m.SurroundingRectangle(sub, color=BLUE, buff=0.15)), self.ptr.hide()),
                  m.FadeIn(auto, shift=0.2 * m.LEFT),
                  m.FadeIn(mem))

    # ---------- 9. comparison ----------
    def compare(self):
        self.header("9 · Side by side (average case)")
        cols = ["", "access", "search", "insert", "delete"]
        rows = [
            ["Array", "O(1)", "O(n)", "O(n)*", "O(n)"],
            ["Linked list", "O(n)", "O(n)", "O(1)†", "O(1)†"],
            ["Stack / queue", "O(1) end", "O(n)", "O(1)", "O(1)"],
            ["Hash table", "n/a", "O(1)", "O(1)", "O(1)"],
            ["Balanced BST", "O(log n)", "O(log n)", "O(log n)", "O(log n)"],
            ["Heap", "O(1) min", "O(n)", "O(log n)", "O(log n)"],
            ["Trie", "n/a", "O(L)", "O(L)", "O(L)"],
        ]

        def color(s):
            return GOOD if s.startswith("O(1)") else BAD if s.startswith("O(n)") else BLUE if "log" in s else DIM if s == "n/a" else FG

        xs = [-4.6, -1.6, 0.6, 2.8, 5.0]
        hdr = m.VGroup(*[T(c, 24, DIM).move_to([x, 2.35, 0]) for c, x in zip(cols, xs)])
        grid = []
        for r, row in enumerate(rows):
            y = 1.65 - 0.62 * r
            grid.append([T(s, 22, FG if c == 0 else color(s)).move_to([x, y, 0]) for c, (s, x) in enumerate(zip(row, xs))])
        rowsg = [m.VGroup(*g) for g in grid]
        foot = T("* append: O(1) amortized     † at a node you already hold", 18, DIM).move_to([0, -2.9, 0])
        self.beat("cm1", m.AnimationGroup(m.FadeIn(hdr), m.LaggedStart(*[m.FadeIn(r, shift=0.15 * m.UP) for r in rowsg], lag_ratio=0.15), m.FadeIn(foot)),
                  m.Create(m.SurroundingRectangle(grid[0][1], color=GOOD, buff=0.1)),
                  m.Create(m.SurroundingRectangle(grid[3][2], color=GOOD, buff=0.1)))

        bst = m.SurroundingRectangle(rowsg[4], color=BLUE, buff=0.1)
        sorted_ = T("sorted", 22, BLUE).next_to(bst, m.LEFT, buff=0.12)
        self.beat("cm2", m.Create(bst),
                  m.FadeIn(sorted_),
                  m.Create(m.SurroundingRectangle(grid[5][1], color=GOOD, buff=0.1)),
                  m.Create(m.SurroundingRectangle(m.VGroup(*grid[1][3:], *grid[2][3:]), color=GOOD, buff=0.1)))

    # ---------- 10. choosing ----------
    def choose(self):
        self.header("10 · How to choose")
        q = T("What does the problem do over and over?", 28, ACCENT).move_to(2.5 * m.UP)
        pairs = [("access by position", "array"), ("lookup by key / seen it before?", "hash map / set"),
                 ("sorted order, ranges, next larger", "balanced tree"), ("smallest / largest, repeatedly", "heap"),
                 ("last in, first out", "stack"), ("first in, first out", "queue"),
                 ("prefixes of strings", "trie"), ("connections, paths, dependencies", "graph")]
        rows = []
        for i, (a, b) in enumerate(pairs):
            y = 1.7 - 0.52 * i
            rows.append(m.VGroup(T(a, 24, FG).move_to([-0.9, y, 0], aligned_edge=m.RIGHT),
                                 T("→", 26, DIM).move_to([-0.45, y, 0]),
                                 T(b, 24, GOOD).move_to([0.0, y, 0], aligned_edge=m.LEFT)))
        right = m.VGroup(*[r[2] for r in rows])
        self.beat("ch1", m.FadeIn(q, shift=0.2 * m.DOWN),
                  self.ptr.sweep(q),
                  m.FadeIn(rows[0], shift=0.2 * m.RIGHT),
                  m.FadeIn(rows[1], shift=0.2 * m.RIGHT))
        self.beat("ch2", *[m.FadeIn(rows[i], shift=0.2 * m.RIGHT) for i in range(2, 6)])
        most = T("naming the right structure is often most of the solution", 24, ACCENT).move_to(3.0 * m.DOWN)
        self.beat("ch3", m.FadeIn(rows[6], shift=0.2 * m.RIGHT),
                  m.FadeIn(rows[7], shift=0.2 * m.RIGHT),
                  m.AnimationGroup(m.Indicate(right, color=ACCENT), self.ptr.hide()),
                  m.FadeIn(most, shift=0.2 * m.UP))
        hold(self, m.Indicate(most, color=ACCENT), seconds=1.0)

    # ---------- 11. quiz ----------
    def quiz(self):
        self.header("11 · Can you explain…")
        qs = ["1.  why appending to a dynamic array is O(1) amortized?",
              "2.  when a hash table becomes O(n)?",
              "3.  why sorted inserts ruin a plain binary search tree?",
              "4.  why heapify is O(n), not O(n log n)?"]
        rows = m.VGroup(*[T(s, 26) for s in qs]).arrange(m.DOWN, buff=0.45, aligned_edge=m.LEFT).move_to(0.6 * m.UP)
        lead = T("before your interview", 22, DIM).next_to(rows, m.UP, buff=0.45)
        self.beat("qz1", m.FadeIn(lead), *[m.FadeIn(r, shift=0.2 * m.RIGHT) for r in rows[:3]])
        end = card("then you know these data structures well", GOOD, 26).move_to(2.6 * m.DOWN)
        self.beat("qz2", m.FadeIn(rows[3], shift=0.2 * m.RIGHT), m.FadeIn(end, shift=0.2 * m.UP))
        self.wait(1.5)
