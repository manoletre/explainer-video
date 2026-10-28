"""Self-Evolving Curriculum (Chen et al., arXiv 2505.14970), explained in ManimGX with LFM3-Audio narration.

    manimgx inspect sec_explainer.py      # layout report + storyboard
    manimgx render sec_explainer.py       # SECExplainer.mp4 beside this file

Narration lines live in narration.py; each [bracket] there is the span one animation plays on.
"""
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
LEVEL = ["#5FAFFF", "#FFD75F", "#D787FF"]  # level 1 (easy) .. 3 (hard)
FONT = "Avenir Next"


# ---------- drawing helpers ----------
def T(s, size=28, color=FG):
    return m.Text(s, font=FONT, font_size=size, color=color)


def M(tex, scale=1.0, color=FG):
    return m.MathTex(tex, color=color).scale(scale)


def card(text, color=FG, size=24, width=None, height=None, fill=PANEL):
    lab = m.VGroup(*[T(line, size, color if i == 0 else DIM) for i, line in enumerate(text.split("\n"))])
    lab.arrange(m.DOWN, buff=0.12)
    box = m.RoundedRectangle(
        corner_radius=0.12,
        width=width or lab.width + 0.6,
        height=height or lab.height + 0.45,
        stroke_color=color,
        stroke_width=3,
        fill_color=fill,
        fill_opacity=1,
    )
    lab.move_to(box)
    return m.VGroup(box, lab)


def dots(pattern, r=0.17, buff=0.16):
    """A row of rollout dots: 1 green (correct), 0 red (wrong), None grey."""
    color = {1: GOOD, 0: BAD, None: "#444444"}
    return m.VGroup(*[m.Circle(radius=r, stroke_width=0, fill_color=color[p], fill_opacity=1) for p in pattern]).arrange(
        m.RIGHT, buff=buff
    )


def recolor(row, pattern):
    color = {1: GOOD, 0: BAD}
    return m.AnimationGroup(*[d.animate.set_fill(color[p], 1) for d, p in zip(row, pattern)])


def machine(label, color=FG, label_color=None):
    body = m.RoundedRectangle(corner_radius=0.15, width=1.5, height=1.9, stroke_color=color, stroke_width=3,
                              fill_color=PANEL, fill_opacity=1)
    window = m.Rectangle(width=1.05, height=0.55, stroke_color=DIM, stroke_width=2).move_to(body.get_top() + 0.5 * m.DOWN)
    q = T("?", 30, ACCENT).move_to(window)
    slot = m.Rectangle(width=0.7, height=0.12, stroke_width=0, fill_color=DIM, fill_opacity=1).move_to(body.get_bottom() + 0.45 * m.UP)
    lever = m.Line(body.get_right() + 0.3 * m.UP, body.get_right() + 0.35 * m.RIGHT + 0.9 * m.UP, color=DIM, stroke_width=4)
    knob = m.Dot(lever.get_end(), radius=0.11, color=BAD)
    lab = T(label, 22, label_color or color).next_to(body, m.DOWN, buff=0.2)
    return m.VGroup(body, window, q, slot, lever, knob, lab)


def bar(value, color, scale=1.0, width=0.6):
    return m.Rectangle(width=width, height=max(value * scale, 0.02), stroke_width=0, fill_color=color, fill_opacity=0.9)


def g(p):
    return 2 * np.sqrt(np.clip(p * (1 - p), 0, None))


def simulate(steps=121, seed=0):
    """Toy SEC run: 3 levels, a model whose skill grows with the learning gain it samples."""
    rng = np.random.default_rng(seed)
    d, a, s = np.array([0.0, 2.0, 4.0]), 1.3, 0.2
    Q, tau, alpha = np.zeros(3), 0.3, 0.5
    P, QS, PR, MD = [], [], [], []
    for _ in range(steps):
        p = 1 / (1 + np.exp(-a * (s - d)))
        pr = np.exp(Q / tau)
        pr /= pr.sum()
        P.append(p), QS.append(Q.copy()), PR.append(pr), MD.append(float(pr @ np.arange(1, 4)))
        cats = rng.choice(3, 64, p=pr)
        gain = 0.0
        for c in range(3):
            n = int((cats == c).sum())
            if n:
                r = g(p[c]) + rng.normal(0, 0.03)
                Q[c] = alpha * r + (1 - alpha) * Q[c]
                gain += n * r
        s += 0.00055 * gain
    return np.array(P), np.array(QS), np.array(PR), np.array(MD)


class SECExplainer(m.Scene):
    voice = staticmethod(lfm_voice(HERE / "narration.py"))

    def construct(self) -> None:
        self.intro()
        self.why_order()
        self.bandits()
        self.mapping()
        self.advantage()
        self.gradient()
        self.peak()
        self.score_update()
        self.softmax()
        self.loop()
        self.simulation()
        self.results()
        self.questions()

    # ---------- scene helpers ----------
    def beat(self, key, *anims):
        self.say(N[key], *anims)

    def clear_all(self):
        if self.mobjects:
            self.play(*[m.FadeOut(x) for x in self.mobjects], run_time=0.6)

    def header(self, text):
        self.clear_all()
        h = T(text, 34).to_edge(m.UP, buff=0.35)
        self.play(m.FadeIn(h, shift=0.2 * m.DOWN), run_time=0.6)
        return h

    # ---------- intro ----------
    def intro(self):
        title = T("Self-Evolving Curriculum for LLM Reasoning", 46)
        sub = T("Chen, Lu, Kim, Zhang, Tang, Piché, Gontier, Bengio, Kamalloo  ·  Mila & ServiceNow  ·  arXiv 2505.14970", 20, DIM)
        m.VGroup(title, sub).arrange(m.DOWN, buff=0.3).move_to(2.3 * m.UP)
        self.beat("in1", m.Write(title), m.FadeIn(sub))

        idea = card("RL fine-tuning  +  a bandit that picks what to train on next", ACCENT, 28).move_to(0.9 * m.UP)
        items = [
            "1  Why the order matters", "2  Multi-armed bandits", "3  Arms = problem categories",
            "4  The advantage", "5  Why |Â| measures learning", "6  |Â| peaks at p = ½",
            "7  Keeping score: TD(0)", "8  Picking arms: softmax", "9  The whole algorithm",
            "10  Watch it run", "11  Results", "12  Questions for the discussion",
        ]
        cols = m.VGroup(*[
            m.VGroup(*[T(s, 22, DIM) for s in items[i:i + 6]]).arrange(m.DOWN, aligned_edge=m.LEFT, buff=0.16)
            for i in (0, 6)
        ]).arrange(m.RIGHT, buff=1.4, aligned_edge=m.UP).move_to(1.6 * m.DOWN)
        self.beat("in2", m.FadeIn(idea, shift=0.2 * m.UP),
                  m.LaggedStart(*[m.FadeIn(s, shift=0.15 * m.RIGHT) for col in cols for s in col], lag_ratio=0.12))

    # ---------- 1. why order matters ----------
    def why_order(self):
        self.header("1 · Why the order of problems matters")
        pats = [[1, 1, 0, 1, 1, 1, 0, 1], [0, 0, 1, 0, 0, 0, 0, 0], [1, 0, 1, 1, 0, 0, 1, 0]]
        boxes = m.VGroup(*[card(f"problem {i + 1}", FG, 22, width=2.2, height=0.7) for i in range(3)])
        rows = m.VGroup(*[dots([None] * 8) for _ in range(3)])
        grid = m.VGroup(*[m.VGroup(b, r).arrange(m.RIGHT, buff=0.6) for b, r in zip(boxes, rows)])
        grid.arrange(m.DOWN, buff=0.45).move_to(0.2 * m.UP)
        legend = m.VGroup(dots([1], 0.12), T("correct → reward 1", 22, DIM), dots([0], 0.12), T("wrong → reward 0", 22, DIM))
        legend.arrange(m.RIGHT, buff=0.2).next_to(grid, m.DOWN, buff=0.6)
        legend[2].shift(0.5 * m.RIGHT), legend[3].shift(0.5 * m.RIGHT)
        self.beat("cu1",
                  m.LaggedStart(*[m.FadeIn(b, shift=0.2 * m.RIGHT) for b in boxes], lag_ratio=0.2),
                  m.LaggedStart(*[m.FadeIn(d, scale=0.5) for r in rows for d in r], lag_ratio=0.03),
                  m.AnimationGroup(*[recolor(r, p) for r, p in zip(rows, pats)], m.FadeIn(legend)))
        self.play(m.FadeOut(grid), m.FadeOut(legend), run_time=0.5)

        bins = m.VGroup(*[card(n, LEVEL[i], 24, width=2.4, height=0.75) for i, n in enumerate(["Easy", "Medium", "Hard"])])
        bins.arrange(m.RIGHT, buff=0.8).move_to(2.15 * m.UP)
        batch = card("training batch", FG, 24, width=3.0, height=0.7).move_to(0.75 * m.UP)
        arrows = m.VGroup(*[m.Arrow(b.get_bottom(), batch.get_top(), buff=0.1, color=DIM) for b in bins])
        ax = m.Axes(x_range=[0, 10, 10], y_range=[0, 1, 1], x_length=6.5, y_length=2.2,
                    axis_config={"color": DIM, "include_ticks": False}).move_to(1.85 * m.DOWN)
        axl = m.VGroup(T("training steps", 18, DIM).next_to(ax, m.DOWN, buff=0.12),
                       T("test score", 18, DIM).rotate(np.pi / 2).next_to(ax, m.LEFT, buff=0.12),
                       T("shape of Fig. 1, not its numbers", 16, DIM).next_to(ax, m.RIGHT, buff=0.2).shift(0.9 * m.DOWN))
        rev = ax.plot(lambda x: 0.12 + 0.08 * (1 - np.exp(-x / 3)), x_range=[0, 10], color=BAD)
        rnd = ax.plot(lambda x: 0.85 * (1 - np.exp(-x / 2.5)), x_range=[0, 10], color=BLUE)
        rev_l = T("reverse: hard → easy", 20, BAD).next_to(rev.get_end(), m.RIGHT, buff=0.15)
        rnd_l = T("random mix", 20, BLUE).next_to(rnd.get_end(), m.RIGHT, buff=0.15)
        self.beat("cu2",
                  m.AnimationGroup(m.FadeIn(bins), m.FadeIn(batch), *[m.GrowArrow(a) for a in arrows]),
                  m.AnimationGroup(m.Create(ax), m.FadeIn(axl), m.Create(rev), m.FadeIn(rev_l)),
                  m.AnimationGroup(m.Create(rnd), m.FadeIn(rnd_l)))
        self.play(*[m.FadeOut(x) for x in (bins, batch, arrows, ax, axl, rev, rnd, rev_l, rnd_l)], run_time=0.5)

        def row(name, pat, color, note):
            return m.VGroup(T(name, 26, color), dots(pat), T(note, 20, DIM))

        easy = row("too easy", [1] * 8, LEVEL[0], "all the same: nothing to compare")
        hard = row("too hard", [0] * 8, LEVEL[2], "all the same: nothing to compare")
        mid = row("just right", [1, 0, 0, 1, 1, 0, 1, 0], LEVEL[1], "some right, some wrong: signal")
        for r in (easy, hard, mid):
            r.arrange(m.RIGHT, buff=0.5)
            r[0].set_x(-4.6), r[1].set_x(-0.6), r[2].next_to(r[1], m.RIGHT, buff=0.5)
        m.VGroup(easy, hard, mid).arrange(m.DOWN, buff=0.7).move_to(0.2 * m.DOWN)
        for r in (easy, hard, mid):
            r[0].set_x(-4.9)
        hl = m.SurroundingRectangle(mid, color=ACCENT, buff=0.18, stroke_width=3)
        self.beat("cu3", m.FadeIn(easy, shift=0.2 * m.RIGHT), m.FadeIn(hard, shift=0.2 * m.RIGHT),
                  m.AnimationGroup(m.FadeIn(mid, shift=0.2 * m.RIGHT), m.Create(hl)))
        self.play(*[m.FadeOut(x) for x in (easy, hard, mid, hl)], run_time=0.5)

        cards = m.VGroup(
            card("Hand-designed schedule\nneeds human heuristics", FG, 24),
            card("Online filtering\nextra rollouts: expensive", FG, 24),
            card("SEC (this paper)\nlearned during training, ~free", ACCENT, 24),
        ).arrange(m.DOWN, buff=0.5).move_to(0.2 * m.DOWN)
        self.beat("cu4", *[m.FadeIn(c, shift=0.2 * m.UP) for c in cards])

    # ---------- 2. bandits ----------
    def bandits(self):
        self.header("2 · Multi-armed bandits")
        term = T("multi-armed bandit", 40, ACCENT).move_to(2.7 * m.UP)
        one = machine("one-armed bandit", FG, DIM).move_to(0.4 * m.UP)
        row = m.VGroup(*[machine(f"arm {a}") for a in "ABC"]).arrange(m.RIGHT, buff=1.4).move_to(0.15 * m.UP)
        mus = m.VGroup(*[T("true mean = ?", 20, DIM).next_to(mc[0], m.UP, buff=0.2) for mc in row])
        self.beat("mb1", m.Write(term), m.FadeIn(one, shift=0.2 * m.UP),
                  m.AnimationGroup(m.ReplacementTransform(one, row[1]), m.FadeIn(row[0]), m.FadeIn(row[2])),
                  m.FadeIn(mus))

        pay = T("+0.7", 30, GOOD).next_to(row[1][0], m.UP, buff=0.65)
        qs = [0.45, 0.7, 0.3]
        bars = m.VGroup(*[bar(q, FG, 1.6).move_to(np.array([mc.get_x(), -2.9, 0]), aligned_edge=m.DOWN) for mc, q in zip(row, qs)])
        qlab = m.VGroup(*[T(f"{q:.2f}", 20, DIM).next_to(b, m.RIGHT, buff=0.12) for b, q in zip(bars, qs)])
        qname = M(r"Q(a)", 1.0, ACCENT).next_to(bars, m.LEFT, buff=0.8)
        self.beat("mb2", m.Indicate(row[1], color=ACCENT), m.FadeIn(pay, shift=0.3 * m.UP),
                  m.AnimationGroup(*[m.GrowFromEdge(b, m.DOWN) for b in bars], m.FadeIn(qlab)), m.Write(qname))

        exploit = T("exploit", 24, GOOD).next_to(row[1][0], m.UP, buff=0.65)
        explore = m.VGroup(*[T("explore", 24, BLUE).next_to(row[i][0], m.UP, buff=0.65) for i in (0, 2)])
        bal = T("exploration  ⟷  exploitation", 26, ACCENT).move_to(np.array([0, -3.45, 0]))
        self.beat("mb3", m.AnimationGroup(m.FadeOut(pay), m.Indicate(bars[1], color=GOOD), m.FadeIn(exploit)),
                  m.AnimationGroup(m.Indicate(row[0], color=BLUE), m.Indicate(row[2], color=BLUE), m.FadeIn(explore)),
                  m.FadeIn(bal))

        drift = m.VGroup(*[T(s, 20, c).move_to(mu) for s, c, mu in
                           zip(["mean drifts ↓", "mean drifts ↓", "mean drifts ↑"], [BAD, BAD, GOOD], mus)])
        ns = card("non-stationary bandit", ACCENT, 24).move_to(2.7 * m.UP)
        forget = T("→ forget old observations", 26, ACCENT).move_to(3.45 * m.DOWN)
        self.beat("mb4", m.AnimationGroup(m.FadeOut(exploit), m.FadeOut(explore), m.ReplacementTransform(mus, drift)),
                  m.ReplacementTransform(term, ns),
                  m.AnimationGroup(bars.animate.set_opacity(0.35), qlab.animate.set_opacity(0.35), m.FadeOut(bal), m.FadeIn(forget)))
        self.clear_all()

        rl = card("Full RL\nstate → action → new state → …", FG, 26)
        bandit = card("Bandit\naction → reward.  No state.", ACCENT, 26)
        m.VGroup(rl, bandit).arrange(m.RIGHT, buff=0.8).move_to(0.8 * m.UP)
        note = card("SEC: training does change the model (a hidden state),\nbut the paper treats it as a bandit anyway", FG, 24)
        note.move_to(1.6 * m.DOWN)
        self.beat("mb5", m.AnimationGroup(m.FadeIn(rl), m.FadeIn(bandit)), m.FadeIn(note, shift=0.2 * m.UP))

    # ---------- 3. mapping ----------
    def mapping(self):
        self.header("3 · Arms = problem categories")
        row = m.VGroup(*[machine(f"category {i + 1}", LEVEL[i]) for i in range(3)]).arrange(m.RIGHT, buff=1.5)
        row.scale(0.85).move_to(1.0 * m.UP)
        names = ["level 1 (easy)", "level 2", "level 3 (hard)"]
        new = m.VGroup(*[T(n, 22, LEVEL[i]).move_to(row[i][6]) for i, n in enumerate(names)])
        batch = card("training batch", FG, 24, width=3.2, height=0.75).move_to(2.0 * m.DOWN)
        arrows = m.VGroup(*[m.Arrow(n.get_bottom(), batch.get_top(), buff=0.15, color=DIM) for n in new])
        payout = T("payout = how much the model learned?", 24, ACCENT).next_to(batch, m.DOWN, buff=0.35)
        self.beat("mp1", m.FadeIn(row, shift=0.2 * m.UP),
                  m.AnimationGroup(*[m.ReplacementTransform(mc[6], n) for mc, n in zip(row, new)]),
                  m.AnimationGroup(m.FadeIn(batch), *[m.GrowArrow(a) for a in arrows]),
                  m.FadeIn(payout, shift=0.2 * m.UP))
        self.clear_all()

        goal = m.VGroup(T("final test accuracy", 30), T("only known after training ends", 22, BAD)).arrange(m.DOWN, buff=0.15)
        need = m.VGroup(T("a payout measurable", 30), T("at every training step", 22, GOOD)).arrange(m.DOWN, buff=0.15)
        m.VGroup(goal, need).arrange(m.RIGHT, buff=1.6).move_to(1.3 * m.UP)
        ans = m.VGroup(M(r"|\hat{A}|", 2.2, ACCENT), T("absolute advantage", 28, ACCENT)).arrange(m.DOWN, buff=0.3)
        ans.move_to(1.5 * m.DOWN)
        self.beat("mp2", m.FadeIn(goal), m.FadeIn(need), m.FadeIn(ans, scale=0.8))

    # ---------- 4. advantage ----------
    def advantage(self):
        self.header("4 · Math piece 1: the advantage (GRPO)")
        prob = card("one problem", FG, 22, width=2.2, height=0.65).move_to(np.array([-4.9, 1.45, 0]))
        row = dots([None] * 8, 0.24, 0.32).move_to(np.array([0.9, 1.45, 0]))
        pat = [1, 1, 0, 0, 0, 0, 0, 0]
        rs = m.VGroup(*[T(str(p), 22, DIM).next_to(d, m.DOWN, buff=0.15) for d, p in zip(row, pat)])
        rname = M(r"r_i", 0.75, DIM).next_to(rs, m.LEFT, buff=0.35)
        mean = M(r"\mathrm{mean}(r) = \tfrac{2}{8} = 0.25", 0.9).move_to(np.array([0, -0.35, 0]))
        self.beat("ad1", m.FadeIn(prob), m.LaggedStart(*[m.FadeIn(d, scale=0.5) for d in row], lag_ratio=0.08),
                  m.AnimationGroup(recolor(row, pat), m.FadeIn(rs), m.FadeIn(rname)), m.Write(mean))

        adv = M(r"\hat{A}_i = \frac{r_i - \mathrm{mean}(r)}{\mathrm{std}(r)}", 1.0).move_to(np.array([-3.2, -1.9, 0]))
        std = M(r"\mathrm{std}(r) = \sqrt{0.25 \cdot 0.75} \approx 0.433", 0.85).move_to(np.array([3.2, -1.9, 0]))
        self.beat("ad2", m.Write(adv), m.Write(std))

        up = m.VGroup(*[T("+1.73", 20, GOOD).next_to(row[i], m.UP, buff=0.2) for i in (0, 1)])
        dn = m.VGroup(*[T("−0.58", 20, BAD).next_to(row[i], m.UP, buff=0.2) for i in range(2, 8)])
        avg = M(r"\mathrm{mean}\,|\hat{A}| = \frac{2(1.73) + 6(0.58)}{8} \approx 0.87", 0.85, ACCENT).move_to(std)
        self.beat("ad3", m.FadeIn(up, shift=0.2 * m.UP), m.FadeIn(dn, shift=0.2 * m.DOWN),
                  m.AnimationGroup(m.FadeOut(std), m.Write(avg)))

        rs1 = m.VGroup(*[T("1", 22, DIM).move_to(r) for r in rs])
        zeros = m.VGroup(*[T("0", 20, DIM).move_to(lab) for lab in [*up, *dn]])
        note = T("all equal → every Â = 0 → no learning signal  (GRPO adds a tiny ε to the std)", 22, BAD)
        note.move_to(3.3 * m.DOWN)
        self.beat("ad4",
                  m.AnimationGroup(recolor(row, [1] * 8), m.ReplacementTransform(rs, rs1), m.FadeOut(mean), avg.animate.set_opacity(0.3)),
                  m.AnimationGroup(m.ReplacementTransform(m.VGroup(*up, *dn), zeros), m.FadeIn(note)))

    # ---------- 5. gradient ----------
    def gradient(self):
        self.header("5 · Math piece 2: why |Â| measures learning")
        loss = M(r"L_{PG}(\theta) = -\,\mathbb{E}\left[ \log \pi_\theta(a_t \mid s_t)\; \hat{A}_t \right]", 0.95).move_to(2.2 * m.UP)
        self.beat("gr1", m.Write(loss))

        grad = M(r"\nabla_\theta L_{PG} = -\,\mathbb{E}\left[ \hat{A}_t \; \nabla_\theta \log \pi_\theta(a_t \mid s_t) \right]", 0.95)
        grad.move_to(1.05 * m.UP)
        norm = M(r"\| \nabla_\theta L_{PG} \| \approx |\hat{A}_t| \cdot \| \nabla_\theta \log \pi_\theta(a_t \mid s_t) \|", 0.95, ACCENT)
        norm.move_to(0.1 * m.DOWN)
        self.beat("gr2", m.Write(grad), m.Write(norm))

        big = T("big |Â|  →  big update", 24, GOOD)
        zero = T("Â = 0  →  no update", 24, BAD)
        m.VGroup(big, zero).arrange(m.RIGHT, buff=1.5).move_to(1.25 * m.DOWN)
        rc = M(r"r(c) = \mathbb{E}_{x \sim c}\left[\, |\hat{A}| \,\right]", 1.0, ACCENT)
        rbox = m.SurroundingRectangle(rc, color=ACCENT, buff=0.2)
        payout = m.VGroup(rc, rbox, T("payout of category c", 20, DIM).next_to(rbox, m.RIGHT, buff=0.3)).move_to(2.35 * m.DOWN)
        free = T("free: GRPO already computed every Â", 22, DIM).move_to(3.4 * m.DOWN)
        self.beat("gr3", m.FadeIn(big), m.FadeIn(zero), m.FadeIn(payout, shift=0.2 * m.UP), m.FadeIn(free))

    # ---------- 6. peak at 1/2 ----------
    def peak(self):
        h = self.header("6 · Math piece 3: |Â| peaks at p = ½")
        p_def = m.VGroup(M(r"p", 1.0, ACCENT), T("= the problem's success rate", 26)).arrange(m.RIGHT, buff=0.25).move_to(2.35 * m.UP)
        cols = [-4.2, -1.2, 2.6]
        head = m.VGroup(*[T(s, 22, DIM).move_to(np.array([x, 1.35, 0])) for s, x in zip(["attempt", "probability", "|Â|"], cols)])
        r1 = m.VGroup(T("correct", 26, GOOD).move_to(np.array([cols[0], 0.4, 0])), M(r"p", 1.0).move_to(np.array([cols[1], 0.4, 0])))
        a1 = M(r"\frac{1-p}{\sqrt{p(1-p)}}", 0.95).move_to(np.array([cols[2], 0.4, 0]))
        self.beat("pk1", m.FadeIn(p_def), m.AnimationGroup(m.FadeIn(head), m.FadeIn(r1)), m.Write(a1))

        r2 = m.VGroup(T("wrong", 26, BAD).move_to(np.array([cols[0], -1.05, 0])), M(r"1-p", 1.0).move_to(np.array([cols[1], -1.05, 0])))
        a2 = M(r"\frac{p}{\sqrt{p(1-p)}}", 0.95).move_to(np.array([cols[2], -1.05, 0]))
        self.beat("pk2", m.FadeIn(r2), m.Write(a2))

        res = M(r"\mathbb{E}|\hat{A}| = p\,\frac{1-p}{\sqrt{p(1-p)}} + (1-p)\,\frac{p}{\sqrt{p(1-p)}} = 2\sqrt{p(1-p)}", 0.9, ACCENT)
        res.move_to(2.55 * m.DOWN)
        self.beat("pk3", m.Write(res))

        self.play(*[m.FadeOut(x) for x in (p_def, head, r1, r2, a1, a2)], run_time=0.5)
        short = M(r"\mathbb{E}|\hat{A}| = 2\sqrt{p(1-p)}", 0.95, ACCENT).move_to(2.45 * m.UP)
        self.play(m.ReplacementTransform(res, short), run_time=0.8)
        ax = m.Axes(x_range=[0, 1, 0.25], y_range=[0, 1.1, 0.5], x_length=7.5, y_length=3.6,
                    axis_config={"color": DIM, "include_numbers": True, "font_size": 22}).move_to(0.55 * m.DOWN)
        xl = T("success rate p", 20, DIM).next_to(ax, m.DOWN, buff=0.15)
        curve = ax.plot(g, x_range=[0, 1, 0.005], color=ACCENT, stroke_width=5)
        d0 = m.Dot(ax.c2p(0, 0), radius=0.12, color=BAD)
        d1 = m.Dot(ax.c2p(1, 0), radius=0.12, color=GOOD)
        top = m.Dot(ax.c2p(0.5, 1), radius=0.12, color=ACCENT)
        dash = m.DashedLine(ax.c2p(0.5, 0), ax.c2p(0.5, 1), color=ACCENT)
        toplab = T("p = 0.5 → max", 22, ACCENT).next_to(top, m.UP, buff=0.15)
        zone = m.Rectangle(width=abs(ax.c2p(0.7, 0)[0] - ax.c2p(0.3, 0)[0]), height=3.4, stroke_width=0,
                           fill_color=ACCENT, fill_opacity=0.12).move_to(ax.c2p(0.5, 0.55))
        zlab = T("zone of proximal development", 22, ACCENT).next_to(ax, m.RIGHT, buff=-1.6).shift(1.35 * m.UP + 0.4 * m.RIGHT)
        self.beat("pk4", m.AnimationGroup(m.Create(ax), m.FadeIn(xl), m.Create(curve)),
                  m.FadeIn(d0, scale=2), m.FadeIn(d1, scale=2),
                  m.AnimationGroup(m.Create(dash), m.FadeIn(top), m.FadeIn(toplab)),
                  m.AnimationGroup(m.FadeIn(zone), m.FadeIn(zlab)))

    # ---------- 7. score update ----------
    def score_update(self):
        self.header("7 · Math piece 4: keeping score")
        upd = M(r"Q_{t+1}(c) = \alpha\, r_t(c) + (1-\alpha)\, Q_t(c)", 1.0).move_to(2.3 * m.UP)
        q0 = M(r"Q_0(c) = 0", 0.8, DIM).move_to(1.45 * m.UP)
        sampled = T("for every category sampled this step", 20, DIM)
        m.VGroup(q0, sampled).arrange(m.RIGHT, buff=0.8).move_to(1.45 * m.UP)
        self.beat("up1", m.FadeIn(sampled), m.Write(upd), m.FadeIn(q0))

        ema = T("TD(0) on a bandit = exponential moving average", 24, ACCENT).move_to(0.75 * m.UP)
        unroll = M(r"Q_{t+1}(c) = \sum_{k \ge 0} \alpha (1-\alpha)^k \; r_{t-k}(c)", 0.95).move_to(0.25 * m.DOWN)
        ws = [0.5 * 0.5 ** k for k in range(8)]
        bars = m.VGroup(*[bar(w, BLUE, 2.6, 0.5) for w in ws]).arrange(m.RIGHT, buff=0.25, aligned_edge=m.DOWN)
        bars.move_to(np.array([-2.3, -2.85, 0]), aligned_edge=m.DOWN)
        klab = m.VGroup(*[T(f"k={k}", 16, DIM).next_to(b, m.DOWN, buff=0.08) for k, b in enumerate(bars)])
        wlab = T("weight of the payout from k steps ago (α = 0.5)", 20, DIM).next_to(bars, m.UP, buff=0.15)
        self.beat("up2", m.FadeIn(ema), m.Write(unroll),
                  m.AnimationGroup(*[m.GrowFromEdge(b, m.DOWN) for b in bars], m.FadeIn(klab), m.FadeIn(wlab)))

        k5 = T("1.6%", 20, ACCENT).next_to(bars[5], m.UP, buff=0.12)
        fast = card("fast forgetting\n= right for a non-stationary bandit", ACCENT, 22).next_to(bars, m.RIGHT, buff=0.6)
        self.beat("up3", m.AnimationGroup(m.Indicate(bars[5], color=ACCENT), m.FadeIn(k5)), m.FadeIn(fast, shift=0.2 * m.LEFT))

    # ---------- 8. softmax ----------
    def softmax(self):
        self.header("8 · Math piece 5: picking arms with a softmax")
        f = M(r"p(c) = \frac{e^{Q_t(c)/\tau}}{\sum_{i=1}^{N} e^{Q_t(c_i)/\tau}}", 1.0).move_to(np.array([-1.0, 2.05, 0]))
        tau = T("τ = temperature", 24, ACCENT).next_to(f, m.RIGHT, buff=0.8)
        self.beat("sm1", m.Write(f), m.AnimationGroup(m.Circumscribe(f, color=ACCENT), m.FadeIn(tau)))

        qs = np.array([0.3, 0.8, 0.5])
        qrow = T("scores:  level 1 = 0.3   ·   level 2 = 0.8   ·   level 3 = 0.5", 22, DIM).move_to(0.75 * m.UP)

        def group(t, x):
            pr = np.exp(qs / t) / np.exp(qs / t).sum()
            bs = m.VGroup(*[bar(p, LEVEL[i], 2.6, 0.7) for i, p in enumerate(pr)]).arrange(m.RIGHT, buff=0.35, aligned_edge=m.DOWN)
            bs.move_to(np.array([x, -2.3, 0]), aligned_edge=m.DOWN)
            pct = m.VGroup(*[T(f"{round(p * 100)}%", 20, FG).next_to(b, m.UP, buff=0.1) for b, p in zip(bs, pr)])
            name = M(rf"\tau = {t}", 0.8, DIM).next_to(bs, m.DOWN, buff=0.2)
            return bs, pct, name

        b1, p1, n1 = group(1, -3.0)
        b2, p2, n2 = group(0.2, 3.0)
        self.beat("sm2", m.FadeIn(qrow),
                  m.AnimationGroup(*[m.GrowFromEdge(b, m.DOWN) for b in b1], m.FadeIn(p1), m.FadeIn(n1)))

        exploit = T("exploit", 24, GOOD).next_to(n2, m.RIGHT, buff=0.4)
        explore = T("explore", 24, BLUE).next_to(n1, m.RIGHT, buff=0.4)
        fill = T("fill the batch: level ~ p(c), then a random problem from it", 22).move_to(3.45 * m.DOWN)
        times = T("× 256", 24, ACCENT).next_to(fill, m.RIGHT, buff=0.3)
        m.VGroup(fill, times).move_to(3.45 * m.DOWN)
        self.beat("sm3", m.AnimationGroup(*[m.GrowFromEdge(b, m.DOWN) for b in b2], m.FadeIn(p2), m.FadeIn(n2)),
                  m.FadeIn(exploit), m.FadeIn(explore), m.FadeIn(fill), m.FadeIn(times, scale=1.4))

    # ---------- 9. loop ----------
    def loop(self):
        self.header("9 · The whole algorithm")
        boxes = [
            card("1 · Sample the batch\nlevel ~ softmax(Q / τ)", LEVEL[0], 24, width=5.9, height=1.3),
            card("2 · Normal GRPO step\nrollouts → rewards → Â → update", FG, 24, width=5.9, height=1.3),
            card("3 · Payout per level\nr(c) = mean |Â| of its rollouts", ACCENT, 24, width=5.9, height=1.3),
            card("4 · Update the scores\nQ ← α r + (1 − α) Q", LEVEL[2], 24, width=5.9, height=1.3),
        ]
        pos = [(-3.35, 1.2), (3.35, 1.2), (3.35, -1.4), (-3.35, -1.4)]
        for b, (x, y) in zip(boxes, pos):
            b.move_to(np.array([x, y, 0]))
        ar = [
            m.Arrow(boxes[0].get_right(), boxes[1].get_left(), buff=0.1, color=DIM),
            m.Arrow(boxes[1].get_bottom(), boxes[2].get_top(), buff=0.1, color=DIM),
            m.Arrow(boxes[2].get_left(), boxes[3].get_right(), buff=0.1, color=DIM),
            m.Arrow(boxes[3].get_top(), boxes[0].get_bottom(), buff=0.1, color=ACCENT),
        ]
        rep = T("repeat", 20, ACCENT).next_to(ar[3], m.LEFT, buff=0.15)
        self.beat("lp1", m.FadeIn(boxes[0]), m.AnimationGroup(m.GrowArrow(ar[0]), m.FadeIn(boxes[1])),
                  m.AnimationGroup(m.GrowArrow(ar[1]), m.FadeIn(boxes[2])),
                  m.AnimationGroup(m.GrowArrow(ar[2]), m.FadeIn(boxes[3])),
                  m.AnimationGroup(m.GrowArrow(ar[3]), m.FadeIn(rep)))
        hp = m.VGroup(T("two new hyperparameters:", 22, DIM),
                      M(r"\alpha \in \{0.2,\ 0.5\} \qquad \tau \in [0.2,\ 1]", 0.85, ACCENT)).arrange(m.RIGHT, buff=0.3)
        hp.move_to(3.15 * m.DOWN)
        self.beat("lp2", m.FadeIn(hp, shift=0.2 * m.UP))

    # ---------- 10. simulation ----------
    def simulation(self):
        self.header("10 · Watch it run")
        P, QS, PR, MD = simulate()
        t = m.ValueTracker(0)

        def at(arr, k=None):
            x = t.get_value()
            i = int(np.clip(np.floor(x), 0, len(arr) - 2))
            v = arr[i] + (arr[i + 1] - arr[i]) * (x - i)
            return v if k is None else v[k]

        tag = T("toy simulation for intuition · not the paper's data", 20, DIM).move_to(2.75 * m.UP)
        ax = m.Axes(x_range=[0, 1, 0.5], y_range=[0, 1.1, 0.5], x_length=5.6, y_length=3.6,
                    axis_config={"color": DIM, "include_numbers": True, "font_size": 28}).move_to(np.array([-3.4, -0.4, 0]))
        xl = T("success rate p", 18, DIM).next_to(ax, m.DOWN, buff=0.12)
        curve = ax.plot(g, x_range=[0, 1, 0.005], color=ACCENT, stroke_width=4)
        dots_ = m.VGroup(*[
            m.always_redraw(lambda k=k: m.Dot(ax.c2p(at(P, k), g(at(P, k))), radius=0.13, color=LEVEL[k]))
            for k in range(3)
        ])
        legend = m.VGroup(*[m.VGroup(m.Dot(radius=0.09, color=LEVEL[k]), T(f"level {k + 1}", 18, LEVEL[k])).arrange(m.RIGHT, buff=0.1)
                            for k in range(3)]).arrange(m.RIGHT, buff=0.35).next_to(ax, m.UP, buff=0.15)

        # right: sampling probabilities and mean sampled difficulty
        base = np.array([2.4, 0.35, 0])
        plab = T("sampling probability", 20, DIM).move_to(base + np.array([0.9, 1.9, 0]))
        pbars = m.always_redraw(lambda: m.VGroup(*[
            bar(at(PR, k), LEVEL[k], 1.6, 0.55).move_to(base + np.array([k * 0.9, 0, 0]), aligned_edge=m.DOWN)
            for k in range(3)
        ]))
        pnames = m.VGroup(*[T(f"L{k + 1}", 18, LEVEL[k]).move_to(base + np.array([k * 0.9, -0.2, 0])) for k in range(3)])
        dax = m.Axes(x_range=[0, 120, 60], y_range=[1, 3, 1], x_length=4.0, y_length=1.9,
                     axis_config={"color": DIM, "include_numbers": True, "font_size": 26}).move_to(np.array([3.5, -2.2, 0]))
        dlab = T("mean sampled level", 18, DIM).next_to(dax, m.UP, buff=0.08)
        mean_line = m.DashedLine(dax.c2p(0, 2), dax.c2p(120, 2), color=DIM)
        mean_lab = T("dataset mean", 20, DIM).next_to(dax.c2p(120, 2), m.DOWN + m.LEFT, buff=0.08)
        path = m.always_redraw(lambda: m.VMobject(color=ACCENT, stroke_width=4).set_points_as_corners(
            [dax.c2p(i, MD[i]) for i in range(int(t.get_value()) + 1)] + [dax.c2p(t.get_value(), at(MD))]))
        right = m.VGroup(plab, pnames, dax, dlab, mean_line, mean_lab)

        self.beat("si1", m.FadeIn(tag), m.AnimationGroup(m.Create(ax), m.FadeIn(xl), m.Create(curve)),
                  m.AnimationGroup(m.FadeIn(legend), m.FadeIn(dots_), m.FadeIn(right), m.FadeIn(pbars), m.FadeIn(path)))
        self.beat("si2", t.animate(rate_func=m.linear).set_value(14), t.animate(rate_func=m.linear).set_value(120))

        fig3 = T("paper, Fig. 3: same pattern on every task", 22, ACCENT).move_to(np.array([-3.4, -3.05, 0]))
        big = T("7B gets harder problems than 3B", 22, ACCENT).move_to(np.array([-3.4, -3.55, 0]))
        self.beat("si3", m.FadeIn(fig3), m.Circumscribe(m.VGroup(dax, dlab), color=ACCENT), m.FadeIn(big))

    # ---------- 11. results ----------
    def results(self):
        self.header("11 · Results")
        models = m.VGroup(*[card(s, FG, 24) for s in ["Qwen2.5-3B", "Qwen2.5-7B"]]).arrange(m.RIGHT, buff=0.5)
        tasks = m.VGroup(*[card(s, BLUE, 22) for s in ["Countdown", "Zebra puzzles", "ARC-1D", "MATH"]]).arrange(m.RIGHT, buff=0.35)
        lv = m.VGroup(*[card(f"level {i}", LEVEL[min(i, 3) - 1] if i < 4 else ACCENT, 22) for i in range(1, 5)]).arrange(m.RIGHT, buff=0.35)
        train = T("train", 22, DIM).next_to(lv[1], m.DOWN, buff=0.2)
        ood = T("out-of-distribution test", 22, ACCENT).next_to(lv[3], m.DOWN, buff=0.2)
        m.VGroup(models, tasks, m.VGroup(lv, train, ood)).arrange(m.DOWN, buff=0.6).move_to(0.3 * m.DOWN)
        train.next_to(lv[1], m.DOWN, buff=0.2), ood.next_to(lv[3], m.DOWN, buff=0.2)
        self.beat("rs1", m.FadeIn(models), m.LaggedStart(*[m.FadeIn(x) for x in tasks], lag_ratio=0.2),
                  m.AnimationGroup(*[m.FadeIn(x) for x in lv[:3]], m.FadeIn(train)), m.AnimationGroup(m.FadeIn(lv[3]), m.FadeIn(ood)))
        self.play(*[m.FadeOut(x) for x in (models, tasks, lv, train, ood)], run_time=0.5)

        def table(title, rows, x):
            cx = [-1.9, -0.3, 0.9, 2.1]
            head = m.VGroup(T(title, 24), *[T(s, 20, c) for s, c in zip(["Random", "Ordered", "SEC"], [BLUE, DIM, ACCENT])])
            head[0].move_to(np.array([x, 2.45, 0]))
            for s, cxi in zip(head[1:], cx[1:]):
                s.move_to(np.array([x + cxi, 1.75, 0]))
            body = m.VGroup()
            for r, (name, *vals) in enumerate(rows):
                y = 1.05 - r * 0.75
                best = int(np.argmax(vals))
                cells = m.VGroup(T(name, 22, DIM).move_to(np.array([x + cx[0], y, 0])))
                for j, v in enumerate(vals):
                    cells.add(T(f"{v:.3f}", 22, ACCENT if j == best else FG).move_to(np.array([x + cx[j + 1], y, 0])))
                body.add(cells)
            return head, body

        h3, b3 = table("Qwen2.5-3B · OOD", [("Countdown", .479, .321, .542), ("Zebra", .285, .329, .345),
                                             ("ARC-1D", .313, .363, .381), ("AIME24", .075, .054, .100)], -3.5)
        h7, b7 = table("Qwen2.5-7B · OOD", [("Countdown", .566, .442, .555), ("Zebra", .321, .311, .355),
                                             ("ARC-1D", .436, .428, .418), ("AIME24", .138, .150, .175)], 3.6)
        ordered = m.SurroundingRectangle(m.VGroup(h3[2], *[r[2] for r in b3[:3]]), color=DIM, buff=0.12)
        self.beat("rs2", m.FadeIn(h3), m.FadeIn(b3[0]), m.FadeIn(b3[1]), m.AnimationGroup(m.FadeIn(b3[2]), m.FadeIn(b3[3])),
                  m.Create(ordered))

        flips = m.VGroup(*[m.SurroundingRectangle(m.VGroup(b7[i][1], b7[i][3]), color=BAD, buff=0.1) for i in (0, 2)])
        harder = T("harder Countdown (7B, OOD):  random 0.373  →  SEC 0.439", 24, ACCENT).move_to(2.6 * m.DOWN)
        self.beat("rs3", m.AnimationGroup(m.FadeOut(ordered), m.FadeIn(h7), m.FadeIn(b7)), m.Create(flips), m.FadeIn(harder))
        self.clear_all()

        h = T("More results", 34).to_edge(m.UP, buff=0.35)
        grid = m.VGroup(*[card(f"{task} · L{lvl}", LEVEL[lvl - 1], 18, width=2.6, height=0.6)
                          for task in ["Countdown", "Zebra", "ARC"] for lvl in (1, 2, 3)]).arrange_in_grid(3, 3, buff=0.2)
        cap = T("9 arms (task × level): random collapses mid-training on Countdown OOD; SEC stays stable", 20, DIM)
        multi = m.VGroup(grid, cap).arrange(m.DOWN, buff=0.3).move_to(0.75 * m.UP)
        algos = m.VGroup(T("Countdown OOD, Qwen2.5-3B:", 22, DIM),
                         T("PPO  0.159 → 0.224", 24, ACCENT), T("RLOO  0.465 → 0.494", 24, ACCENT)).arrange(m.RIGHT, buff=0.6)
        algos.move_to(2.6 * m.DOWN)
        self.add(h)
        self.beat("rs4", m.FadeIn(multi), m.FadeIn(algos, shift=0.2 * m.UP))

    # ---------- 12. questions ----------
    def questions(self):
        self.header("12 · Questions for the reading group")

        def item(title, color=FG):
            return T(title, 26, color)

        q1 = item("1. Is SEC just “prefer levels near 50% accuracy”?")
        q1m = m.VGroup(M(r"\mathbb{E}|\hat{A}| = 2\sqrt{p(1-p)}", 0.75, ACCENT), T("depends only on p", 20, DIM)).arrange(m.RIGHT, buff=0.3)
        q2 = item("2. Noise: AIME24 has 30 problems")
        q2m = M(r"(0.100 - 0.075) \times 30 = 0.75 \text{ problems}", 0.75, ACCENT)
        q2n = T("no error bars · best checkpoint reported", 20, DIM)
        q3 = item("3. α and τ tuned per task and model (Table S2); random has nothing to tune")
        q4 = item("4. Big gradient ≠ useful learning")
        q4n = T("Teacher-Student Curriculum Learning (Matiisen et al. 2020) used measured progress", 20, DIM)
        col = m.VGroup(q1, q1m, q2, m.VGroup(q2m, q2n).arrange(m.RIGHT, buff=0.4), q3, q4, q4n)
        col.arrange(m.DOWN, aligned_edge=m.LEFT, buff=0.22).move_to(0.35 * m.DOWN)
        for sub in (q1m, col[3], q4n):
            sub.shift(0.5 * m.RIGHT)
        self.beat("q1", m.FadeIn(q1, shift=0.2 * m.RIGHT), m.Write(q1m))
        self.beat("q2", m.FadeIn(q2, shift=0.2 * m.RIGHT), m.Write(q2m), m.FadeIn(q2n))
        self.beat("q3", m.FadeIn(q3, shift=0.2 * m.RIGHT), m.FadeIn(q4, shift=0.2 * m.RIGHT), m.FadeIn(q4n))
        self.clear_all()

        h = T("For chessLLM", 34).to_edge(m.UP, buff=0.35)
        bands = m.VGroup(*[machine(s, LEVEL[min(i, 2)] if i < 3 else ACCENT) for i, s in
                           enumerate(["< 1200", "1200–1600", "1600–2000", "2000+"])]).arrange(m.RIGHT, buff=1.2)
        bands.scale(0.75).move_to(1.0 * m.UP)
        sampler = card("SEC sampler\nlevel ~ softmax(Q / τ)", ACCENT, 26).move_to(1.85 * m.DOWN)
        arrows = m.VGroup(*[m.Arrow(b[6].get_bottom(), sampler.get_top(), buff=0.12, color=DIM) for b in bands])
        feed = T("payout = mean |Â| from the GRPO run you already have", 22, DIM).next_to(sampler, m.DOWN, buff=0.3)
        self.add(h)
        self.beat("q4", m.FadeIn(bands, shift=0.2 * m.UP),
                  m.AnimationGroup(*[m.GrowArrow(a) for a in arrows], m.FadeIn(sampler)), m.FadeIn(feed))
        self.wait(1.0)
        self.clear_all()
