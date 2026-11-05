"""Keeping the screen in step with the voice: a laser pointer, and a check for speech over nothing.

    from stage import Pointer, say_synced, chrome
    self.ptr = Pointer()                                     # once, in construct()
    say_synced(self, "beat-key", N["beat-key"], self.ptr.at(formula[2]), ...)

The pointer is a red laser dot (as in Edito's recorder) that the narration can move: `at` flies to a
mobject and pulses a ring there, `sweep` underlines one from left to right, `circle` rings it, `hide`
puts it away. Each is an animation, so it takes a [bracket] in the line like any other.

`say_synced` is `scene.say` plus a check. It reports, on stderr and in `sync_report.txt` beside the
scene, every beat that
  - starts talking over an empty screen (only the header and the pointer on it) for more than
    LEAD seconds before its first animation: the viewer hears about something they cannot see;
  - talks for more than STILL seconds with nothing moving: the viewer loses the place.
Silence is never flagged: a pause after a line, to let a point land, is fine (see `hold`).
"""
import atexit
import inspect
import sys
from pathlib import Path

import numpy as np

import manimgx as m
from manimgx.audio import spans

LEAD = 0.75  # seconds of speech allowed over an empty screen before the first animation
STILL = 4.0  # seconds of speech allowed with nothing moving
RED = "#FF2D3D"
GAP = 0.34  # how far outside its target the dot rests: clear of the glyphs


def chrome(mob):
    """Mark a mobject as furniture (a header, the pointer): it doesn't count as content."""
    mob.is_chrome = True
    return mob


# ---------- the pointer ----------
class Pointer(m.VGroup):
    """A laser dot. Starts hidden; the first gesture brings it in where it points."""

    PARTS = ((0.30, 0.08), (0.20, 0.18), (0.11, 1.0))  # (radius, opacity): glow, glow, dot

    def __init__(self, color=RED):
        body = [m.Circle(radius=r, stroke_width=0, fill_color=color, fill_opacity=0) for r, _ in self.PARTS]
        hot = m.Circle(radius=0.045, stroke_width=0, fill_color="#FFD0D4", fill_opacity=0)
        ring = m.Circle(radius=1.0, stroke_color=color, stroke_width=5, stroke_opacity=0, fill_opacity=0)
        super().__init__(*body, hot, ring)
        self.set_z_index(100)
        chrome(self)
        self.on = False
        self.pos = np.zeros(3)

    def draw(self, pos, vis=1.0, ring=None):
        """Put the dot at `pos` with visibility `vis`; `ring` in [0, 1) is how far a pulse has spread."""
        *body, hot, rg = self.submobjects
        for c, (_, o) in zip(body, self.PARTS):
            c.move_to(pos).set_fill(opacity=o * vis)
        hot.move_to(pos).set_fill(opacity=vis)
        if ring is None or not 0 <= ring < 1:
            rg.set_stroke(opacity=0)
        else:
            rg.scale_to_fit_width(2 * (0.14 + 0.16 * ring)).move_to(pos).set_stroke(opacity=(1 - ring) * vis, width=5 * (1 - ring) + 1)
        return self

    # gestures: each returns an animation
    def at(self, target, edge=m.DOWN, **kw):
        """Fly to `target` and pulse. It rests just outside the `edge` side (below, by default), so it
        never hides what it points at; `edge=None` lands on the centre. `target` may be a point."""
        return Gesture(self, lambda: [_point(target, edge)], **kw)

    def sweep(self, target, **kw):
        """Underline `target` from left to right, taking the whole span."""
        def path():
            b = target.get_bottom() + GAP * m.DOWN
            return [np.array([target.get_left()[0], b[1], 0]), np.array([target.get_right()[0], b[1], 0])]
        return Gesture(self, path, glide=True, **kw)

    def circle(self, target, **kw):
        """Ring `target` once, from the top (usually the emptiest side), taking the whole span."""
        def path():
            c, w, h = target.get_center(), target.width / 2 + GAP, target.height / 2 + GAP
            return [c + np.array([w * np.cos(a), h * np.sin(a), 0]) for a in np.linspace(np.pi / 2, np.pi / 2 - 2 * np.pi, 25)]
        return Gesture(self, path, glide=True, pulse=False, **kw)

    def hide(self, **kw):
        return Gesture(self, None, **{"run_time": 0.3, **kw})


def _point(target, edge):
    if isinstance(target, m.Mobject):
        if edge is None:
            return target.get_center()
        return target.get_critical_point(edge) + GAP * np.array(edge, dtype=float)
    return np.array(target, dtype=float)


class Gesture(m.Animation):
    """A pointer move. It travels in its first `travel` seconds whatever its run time, so a long
    bracketed span doesn't make it crawl; then it pulses and rests. A `glide` uses the whole span."""

    def __init__(self, ptr, path, *, travel=0.45, glide=False, pulse=True, run_time=1.2, **kw):
        super().__init__(ptr, run_time=run_time, introducer=True, **kw)
        self.ptr, self.path, self.travel, self.glide, self.pulse = ptr, path, travel, glide, pulse

    def begin(self):
        super().begin()
        p = self.ptr
        scene = getattr(self, "_scene", None)
        if scene is not None and p not in scene.mobjects:
            p.on = False  # faded out with everything else since its last gesture
        self.was_on, self.start = p.on, p.pos.copy()
        self.points = None if self.path is None else self.path()
        p.on = self.points is not None
        if p.on:
            p.pos = self.points[-1].copy()

    def interpolate_mobject(self, alpha):
        p, t, rt = self.ptr, alpha * self.run_time, max(self.run_time, 1e-6)
        if self.points is None:  # hide
            p.draw(self.start, vis=0.0 if not self.was_on else 1 - alpha)
            return
        pts = self.points
        if not self.was_on:
            pts = [pts[0]] + list(pts)
        else:
            pts = [self.start] + list(pts)
        if self.glide:  # quick hop to the path's start, then trace it over the rest of the span
            arrive = min(self.travel, 0.25 * rt)
            if t < arrive:
                pos = _lerp(pts[0], pts[1], m.smooth(t / arrive))
            else:
                pos = _along(pts[1:], m.smooth(min((t - arrive) / max(rt - arrive, 1e-6), 1)))
        else:
            arrive = min(self.travel, 0.6 * rt)
            pos = _lerp(pts[0], pts[-1], m.smooth(min(t / arrive, 1)))
        vis = min(t / 0.25, 1) if not self.was_on else 1.0
        p.draw(pos, vis, (t - arrive) / 0.7 if self.pulse else None)


def _lerp(a, b, k):
    return a + (b - a) * k


def _along(pts, k):
    seg = np.array([np.linalg.norm(b - a) for a, b in zip(pts, pts[1:])])
    if seg.sum() == 0:
        return pts[-1]
    d, i = k * seg.sum(), 0
    while i < len(seg) - 1 and d > seg[i]:
        d -= seg[i]
        i += 1
    return _lerp(pts[i], pts[i + 1], d / seg[i] if seg[i] else 1)


# ---------- the check ----------
_report: list[str] = []
_report_path: list[Path] = []


def _write():
    if _report_path:
        _report_path[0].write_text("\n".join(_report) + ("\n" if _report else "no problems\n"))


atexit.register(_write)


def _track(scene):
    """Remember where the report goes, so a clean run overwrites an old report with "no problems"."""
    if not _report_path:
        _report_path.append(Path(inspect.getfile(type(scene))).parent / "sync_report.txt")


def _flag(scene, msg):
    _track(scene)
    _report.append(msg)
    print(f"SYNC {msg}", file=sys.stderr)


def _quote(words, a, b):
    said = [w.text for w in words if w.end > a and w.start < b]
    s = " ".join(said)
    return s if len(s) < 90 else s[:87] + "..."


def say_synced(scene, key, script, *anims):
    """`scene.say(script, *anims)`, after checking the beat for speech over an empty or frozen screen."""
    _track(scene)
    text, found = spans(script)
    speech = scene.speech(text)
    words, dur = speech.words, speech.duration
    if found:
        from manimgx.audio import times

        wins = []
        for a, sp in zip(anims, found):
            s, e = times(speech, sp)
            wins.append((s, s + max(a.run_time, e - s)))
    else:
        wins = [(0.0, max(a.run_time for a in anims))] if anims else []
    content = [x for x in scene.mobjects if not getattr(x, "is_chrome", False)]
    first = min((s for s, _ in wins), default=dur)
    dead = not content and first > LEAD
    if dead:
        _flag(scene, f"{key}: dead air, {first:.1f}s of speech over an empty screen before anything appears: "
                     f'"{_quote(words, 0, first)}". Bracket the opening words, or show something first.')
    # stretches of speech with nothing moving
    t, busy = 0.0, sorted(wins)
    for s, e in busy + [(dur, dur)]:
        if s - t > STILL and _quote(words, t, s) and not (dead and t == 0):
            _flag(scene, f"{key}: still, {s - t:.1f}s of speech with nothing moving ({t:.1f}-{s:.1f}s): "
                         f'"{_quote(words, t, s)}". Point at what it talks about, or reveal it there.')
        t = max(t, e)
    return scene.say(script, *anims)


def hold(scene, *anims, seconds=1.2):
    """A silent beat for emphasis: play `anims` (an Indicate, a pointer pulse), then let it sit."""
    if anims:
        scene.play(*anims)
    scene.wait(seconds)
