"""Render a scene at the best quality this machine finishes in time, with progress on stdout.

    python3 scripts/render.py <dir>/<slug>.py                 # plan, then render
    python3 scripts/render.py <dir>/<slug>.py --plan          # only the plan
    python3 scripts/render.py <dir>/<slug>.py --budget 30     # minutes the render may take (default 45)
    python3 scripts/render.py <dir>/<slug>.py -r 1280x720 --fps 30   # force a format, still with progress

A plain `manimgx render` uses the scene's format, 1920x1080 at 60 fps, and prints nothing until it
ends when its output is not a terminal. With a GPU that is fine. Without one (ManimGX then draws on
the CPU through Mesa's lavapipe) a changed frame costs 0.1–0.3 s, and an 8 minute video at 1080p60
takes hours. So this script:
  1. runs the scene without drawing, to count the frames that change (a held frame is drawn once);
  2. draws SAMPLE of its changing frames, spread over the whole scene, at each candidate format, to
     time them;
  3. picks the first format on the ladder whose estimate fits the budget;
  4. renders it with `manimgx render`'s own machinery (storyboard, layout report, .srt), printing
     progress and an ETA every 20 s.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hardware  # noqa: E402

try:
    import manimgx  # noqa: F401
except ImportError:  # run again in the interpreter uv installed ManimGX into
    py = hardware.manimgx_python()
    if py is None:
        sys.exit("manimgx is not installed: uv tool install manimgx")
    os.execv(py, [py, *sys.argv])

GPU_LADDER = [(1920, 1080, 60), (1920, 1080, 30), (1280, 720, 30)]
CPU_LADDER = [(1920, 1080, 30), (1280, 720, 30), (1280, 720, 24), (960, 540, 24), (854, 480, 15)]
SAMPLE = 120  # changing frames timed per format, spread over the scene
OVERHEAD = 1.15  # storyboard, layout checks and muxing on top of the frames


def _scene(file, name):
    from manimgx.cli.scenes import scene
    return scene(Path(file), name)


def _take(file, name, w, h, fps, every=0):
    """Run the scene at this format. every=0: draw nothing; every=k: draw only every k-th changing
    frame (into a throwaway video), dropping the rest. Returns its counts and wall time."""
    import tempfile
    from manimgx.cli.scenes import Format, take
    from manimgx.rendering import film

    sent = [0, 0]  # changing frames, frames drawn
    original = film.Film._send

    def sending(self):
        if self._pending is None:
            return original(self)
        sent[0] += 1
        if every and (sent[0] - 1) % every == 0:
            sent[1] += 1
            return original(self)
        self._pending = None  # not drawn: the scene's state, not the previous frame, makes the next

    film.Film._send = sending
    kind = _scene(file, name)
    with tempfile.TemporaryDirectory() as tmp:
        start = time.perf_counter()
        made, f = take(kind, Format(w, h, fps), video=Path(tmp) / "sample.mp4" if every else None,
                       preset="veryfast")
        wall = time.perf_counter() - start
    return {"seconds": float(made.clock), "frames": f.frame_count, "changing": sent[0], "drawn": sent[1],
            "wall": wall}


def count(file, name, fps):
    """Run the scene without drawing: its seconds, frames, and the frames that change (a held frame
    is drawn once)."""
    from manimgx.config import config
    return _take(file, name, config.pixel_width, config.pixel_height, fps)


def sample(file, name, w, h, fps, changing, idle):
    """Seconds per changing frame at this format, timed on SAMPLE frames spread over the whole scene
    (its title frames are cheaper than its busy middle); idle is the wall time of a run that draws
    nothing, which is subtracted."""
    every = max(1, changing // SAMPLE)
    r = _take(file, name, w, h, fps, every)
    if r["drawn"] < 3:
        return None
    return max(0.0, r["wall"] - idle) / r["drawn"]


def _child(*args):
    """Run count/sample in a fresh interpreter: a scene's helpers keep state between runs."""
    r = subprocess.run([sys.executable, __file__, *args], check=False, capture_output=True, text=True, errors="replace")
    out = [x for x in r.stdout.splitlines() if x.startswith("{")]
    if r.returncode or not out:
        raise RuntimeError(f"{' '.join(args[:2])} failed:\n{r.stderr[-3000:]}")
    return json.loads(out[-1])


def plan(file, name, budget_min, quiet=False):
    say = (lambda *a: None) if quiet else (lambda *a: print(*a, flush=True))
    import manimgx._engine as e
    try:
        g = e.adapter_info()
    except Exception as err:  # noqa: BLE001
        sys.exit(f"No GPU adapter for ManimGX: {err}\nRun python3 {HERE / 'hardware.py'} for the fix.")
    on_gpu = g.get("device_type") in hardware.GPU_TYPES
    ladder = GPU_LADDER if on_gpu else CPU_LADDER
    say(f"adapter: {g.get('name')} [{g.get('device_type')}, {g.get('backend')}] -> {'GPU' if on_gpu else 'CPU'} ladder")
    counts = {}
    spf = {}
    chosen = None
    for w, h, fps in ladder:
        if fps not in counts:
            counts[fps] = _child("--_count", str(file), name or "", str(fps))
        c = counts[fps]
        if (w, h) not in spf:
            spf[(w, h)] = _child("--_sample", str(file), name or "", f"{w}x{h}", str(fps),
                                 str(c["changing"]), str(c["wall"]))["spf"]
        s = spf[(w, h)] or 0.0
        est = c["changing"] * s * OVERHEAD / 60
        say(f"  {w}x{h}@{fps}: {c['changing']} of {c['frames']} frames change, {s:.3f} s each -> ~{est:.0f} min")
        if chosen is None and est <= budget_min:
            chosen = (w, h, fps, est)
            break
    if chosen is None:
        w, h, fps = ladder[-1]
        chosen = (w, h, fps, counts[fps]["changing"] * (spf[(w, h)] or 0) * OVERHEAD / 60)
        say(f"nothing fits {budget_min} min; using the smallest format. Split the video into several scenes "
            "or raise --budget.")
    c = counts[chosen[2]]
    say(f"plan: {chosen[0]}x{chosen[1]} at {chosen[2]} fps, about {chosen[3]:.0f} min for {c['seconds']:.0f} s of video")
    return chosen, c


def render(file, name, w, h, fps, preset, crf, seconds=None):
    """`manimgx render`, with a progress line every 20 s whether or not stdout is a terminal."""
    from manimgx.cli import export
    from manimgx.cli.scenes import Size

    original = export.take
    start, last = time.perf_counter(), [0.0]

    def take(kind, look, *, plays=None, **kw):
        def hook(made, play, did):
            now = time.perf_counter() - start
            if now - last[0] >= 20:
                last[0] = now
                t = float(play.end)
                line = f"render: {t:.0f} s of scene"
                if seconds:
                    frac = min(t / seconds, 1)
                    eta = now / frac - now if frac > 0.02 else None
                    line += f" / {seconds:.0f} s ({100 * frac:.0f}%)"
                    line += f", {now / 60:.1f} min in" + (f", ~{eta / 60:.0f} min left" if eta else "")
                print(line, flush=True)
            if plays is not None:
                plays(made, play, did)
        return original(kind, look, plays=hook, **kw)

    export.take = take
    print(f"rendering {Path(file).name} at {w}x{h}, {fps} fps, preset {preset}", flush=True)
    export.render(Path(file), name, output=None, resolution=Size(w, h), fps=fps, preset=preset, crf=crf)


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--_count", "--_sample"):
        mode, file, name, a = sys.argv[1:5]
        name = name or None
        if mode == "--_count":
            print(json.dumps(count(file, name, float(a))))
        else:
            w, h = map(int, a.split("x"))
            fps, changing, idle = float(sys.argv[5]), int(sys.argv[6]), float(sys.argv[7])
            print(json.dumps({"spf": sample(file, name, w, h, fps, changing, idle)}))
        return
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("scene", nargs="?")
    ap.add_argument("--budget", type=float, default=45, help="minutes the render may take (default 45)")
    ap.add_argument("--plan", action="store_true", help="only estimate and print the plan")
    ap.add_argument("-r", "--resolution", help="WxH: skip the plan and render at this size")
    ap.add_argument("--fps", type=int)
    ap.add_argument("--preset", default=None, help="x264 preset (default: veryfast on the CPU, medium on a GPU)")
    ap.add_argument("--crf", type=float, default=23.0)
    args = ap.parse_args()
    file = Path(args.file).resolve()
    if args.resolution:
        w, h = map(int, args.resolution.lower().split("x"))
        fps, seconds = args.fps or 30, None
    else:
        (w, h, fps, _), c = plan(file, args.scene, args.budget)
        seconds = c["seconds"]
        if args.plan:
            return
    preset = args.preset or ("medium" if (w, h, fps) == GPU_LADDER[0] else "veryfast")
    render(file, args.scene, w, h, fps, preset, args.crf, seconds)


if __name__ == "__main__":
    main()
