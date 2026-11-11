"""Render a scene at the best quality this machine finishes in time, with progress on stdout.

    python3 scripts/render.py <dir>/<slug>.py                 # plan, then render
    python3 scripts/render.py <dir>/<slug>.py --plan          # only the plan
    python3 scripts/render.py <dir>/<slug>.py --budget 30     # minutes the render may take (default 10)
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

On the CPU, lavapipe's and ManimGX's worker threads race: the same frame comes out different from
run to run, with black patches over text and boxes missing. So there every process is pinned to one
thread (PIN), which draws each frame right but about 4.5 times slower, and the video is rendered as
JOBS segments in parallel processes (split so each draws as many changing frames), then joined
without re-encoding, with the scene's sound and subtitles added and its storyboard drawn.
"""
import argparse
import json
import math
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
PIN = {"LP_NUM_THREADS": "1", "RAYON_NUM_THREADS": "1"}  # one thread each: frames drawn right on the CPU


def jobs():
    """Parallel segment renders on the CPU: a core each, one left over; about 1.5 GB of RAM each."""
    cores = hardware._cpu()["cores"]
    ram = hardware._ram_gb() or 8
    return max(1, min(cores - 1, int(ram // 1.5)))


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
    starts = []
    original = film.Film._send

    def sending(self):
        if self._pending is None:
            return original(self)
        sent[0] += 1
        starts.append(self._first)
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
            "wall": wall, "starts": starts if not every else []}


def segment(file, name, w, h, fps, lo, hi, out, preset, crf):
    """Render frames [lo, hi) of the scene, silent, into out; the frames done so far go to out.n."""
    from manimgx.cli.scenes import Format, take
    from manimgx.rendering import film

    original = film.Film._send
    done, last = [0], [0.0]

    def sending(self):
        p = self._pending
        if p is None:
            return original(self)
        a, b = max(self._first, lo), min(self._first + p[3], hi)
        if a >= b:
            self._pending = None  # outside the segment: not drawn
            return None
        if self._first < lo:
            self._pending_key = True  # the segment's first frame begins it
        self._pending = (*p[:3], b - a)
        done[0] += b - a
        if time.perf_counter() - last[0] > 5:
            last[0] = time.perf_counter()
            Path(f"{out}.n").write_text(str(done[0]))
        return original(self)

    film.Film._send = sending
    film.Film.soundtrack = lambda self: None  # the sound is added once, to the joined video
    take(_scene(file, name), Format(w, h, fps), video=out, preset=preset, crf=crf)
    Path(f"{out}.n").write_text(str(done[0]))
    return {"frames": done[0]}


def extras(file, name, w, h, fps, wav, srt):
    """Run the scene without drawing: write its sound track (wav) and subtitles (srt)."""
    from manimgx.cli.scenes import Format, take
    from manimgx.rendering import film

    made, f = take(_scene(file, name), Format(w, h, fps))
    sound = f.soundtrack()
    if sound is not None:
        Path(wav).write_bytes(film._wav(sound))
    subs = f.subtitles()
    if subs:
        Path(srt).write_text(subs, encoding="utf-8")
    return {"name": type(made).__name__, "sound": sound is not None, "subtitles": bool(subs)}


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
    n = 1 if on_gpu else jobs()
    if not on_gpu:
        os.environ.update(PIN)  # the children time frames the way the render draws them
    say(f"adapter: {g.get('name')} [{g.get('device_type')}, {g.get('backend')}] -> {'GPU' if on_gpu else 'CPU'} ladder"
        + ("" if on_gpu else f", {n} parallel one-thread renders"))
    counts = {}
    spf = {}
    chosen = None
    tried = []
    for w, h, fps in ladder:
        if fps not in counts:
            counts[fps] = _child("--_count", str(file), name or "", str(fps))
        c = counts[fps]
        if (w, h) not in spf:
            spf[(w, h)] = _child("--_sample", str(file), name or "", f"{w}x{h}", str(fps),
                                 str(c["changing"]), str(c["wall"]))["spf"]
        s = spf[(w, h)] or 0.0
        est = c["changing"] * s * OVERHEAD / 60 / n
        say(f"  {w}x{h}@{fps}: {c['changing']} of {c['frames']} frames change, {s:.3f} s each -> ~{est:.0f} min")
        tried.append((w, h, fps, est))
        if chosen is None and est <= budget_min:
            chosen = (w, h, fps, est)
            break
    if chosen is None:
        w, h, fps = ladder[-1]
        chosen = (w, h, fps, counts[fps]["changing"] * (spf[(w, h)] or 0) * OVERHEAD / 60 / n)
        say(f"nothing fits {budget_min} min; using the smallest format. Split the video into several scenes "
            "or raise --budget.")
    c = counts[chosen[2]]
    say(f"plan: {chosen[0]}x{chosen[1]} at {chosen[2]} fps, about {chosen[3]:.0f} min for {c['seconds']:.0f} s of video")
    if not on_gpu:
        say("limits: no GPU here, so every frame is drawn on the CPU. Better quality costs time:")
        for w, h, fps, est in tried:
            if (w, h, fps) != chosen[:3]:
                say(f"  {w}x{h} at {fps} fps: about {est:.0f} min (--budget {math.ceil(est) + 1})")
        say("  on any GPU (Metal or Vulkan) 1920x1080 at 60 fps takes a few minutes: render there instead")
    return chosen, c, on_gpu


def on_cpu():
    import manimgx._engine as e
    try:
        return e.adapter_info().get("device_type") not in hardware.GPU_TYPES
    except Exception:  # noqa: BLE001
        return False


def render_cpu(file, name, w, h, fps, preset, crf, c):
    """Render in parallel one-thread segments, join them, add sound and subtitles, draw the storyboard."""
    import shutil
    import tempfile

    env = {**os.environ, **PIN}
    n, frames, starts = jobs(), c["frames"], c["starts"]
    cuts = [0] + [starts[len(starts) * k // n] for k in range(1, n)] + [frames]
    cuts = sorted(set(cuts))
    kind = _scene(file, name)
    video = Path(file).with_name(f"{kind.__name__}.mp4")
    print(f"rendering {Path(file).name} at {w}x{h}, {fps} fps, preset {preset}, in {len(cuts) - 1} "
          "parallel one-thread segments", flush=True)
    tmp = Path(tempfile.mkdtemp(prefix="render-", dir=video.parent))
    start = time.perf_counter()

    def spawn(*args, log):
        return log, subprocess.Popen([sys.executable, __file__, *map(str, args)], env=env,
                                     stdout=open(tmp / f"{log}.log", "w"), stderr=subprocess.STDOUT)

    parts = [tmp / f"part{k:02d}.mp4" for k in range(len(cuts) - 1)]
    procs = [spawn("--_segment", file, name or "", f"{w}x{h}", fps, lo, hi, part, preset, crf, log=part.stem)
             for lo, hi, part in zip(cuts, cuts[1:], parts)]
    procs.append(spawn("--_extras", file, name or "", f"{w}x{h}", fps, tmp / "sound.wav", tmp / "subs.srt",
                       log="extras"))
    while any(p.poll() is None for _, p in procs):
        time.sleep(20)
        done = sum(int(f.read_text() or 0) for f in tmp.glob("part*.mp4.n"))
        now, frac = time.perf_counter() - start, done / max(frames, 1)
        eta = f", ~{(now / frac - now) / 60:.0f} min left" if frac > 0.02 else ""
        print(f"render: {100 * frac:.0f}%, {now / 60:.1f} min in{eta}", flush=True)
    failed = [log for log, p in procs if p.returncode]
    if failed:
        logs = "\n".join(f"--- {log}\n" + (tmp / f"{log}.log").read_text()[-2000:] for log in failed)
        sys.exit(f"render failed ({tmp}):\n{logs}")
    (tmp / "parts.txt").write_text("".join(f"file '{p.name}'\n" for p in parts))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "parts.txt")]
    if (tmp / "sound.wav").exists():
        cmd += ["-i", str(tmp / "sound.wav"), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "224k"]
    subprocess.run([*cmd, "-c:v", "copy", "-movflags", "+faststart", str(video)], check=True)
    if (tmp / "subs.srt").exists():
        shutil.copy(tmp / "subs.srt", video.with_suffix(".srt"))
        print(f"subtitles: {video.with_suffix('.srt')}", flush=True)
    else:
        video.with_suffix(".srt").unlink(missing_ok=True)  # a previous render's, no longer true
    took = time.perf_counter() - start
    print(f"{video}  {w}x{h} at {fps} fps, {video.stat().st_size / 1e6:.1f} MB (rendered in {took / 60:.1f} min)",
          flush=True)
    shutil.rmtree(tmp)
    print("storyboard and layout report: manimgx inspect", flush=True)
    subprocess.run(["manimgx", "inspect", str(file), *([name] if name else [])], env=env, check=False)


def _progress(total, lo=0, hi=None, out=None, every=20):
    """Patch Film._send to report the frames done, on stdout (or into the file out) every `every` s."""
    from manimgx.rendering import film
    original = film.Film._send
    hi = total if hi is None else hi
    start, last = time.perf_counter(), [0.0]

    def sending(self):
        now = time.perf_counter() - start
        if self._pending is not None and now - last[0] >= every:
            last[0] = now
            done = min(max(self._first - lo, 0), hi - lo)
            if out:
                Path(out).write_text(str(done))
            else:
                frac = done / max(hi - lo, 1)
                eta = f", ~{(now / frac - now) / 60:.0f} min left" if frac > 0.02 else ""
                print(f"render: {100 * frac:.0f}%, {now / 60:.1f} min in{eta}", flush=True)
        return original(self)

    film.Film._send = sending


def render(file, name, w, h, fps, preset, crf, frames):
    """`manimgx render` (video, storyboard, layout report, .srt), with progress every 20 s."""
    from manimgx.cli import export
    from manimgx.cli.scenes import Size

    _progress(frames)
    print(f"rendering {Path(file).name} at {w}x{h}, {fps} fps, preset {preset}", flush=True)
    export.render(Path(file), name, output=None, resolution=Size(w, h), fps=fps, preset=preset, crf=crf)


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--_segment", "--_extras"):
        mode, file, name, size, fps = sys.argv[1:6]
        w, h = map(int, size.split("x"))
        if mode == "--_segment":
            lo, hi, out, preset, crf = sys.argv[6:11]
            print(json.dumps(segment(file, name or None, w, h, int(fps), int(lo), int(hi), out, preset, float(crf))))
        else:
            print(json.dumps(extras(file, name or None, w, h, int(fps), *sys.argv[6:8])))
        return
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
    ap.add_argument("--budget", type=float, default=10, help="minutes the render may take (default 10)")
    ap.add_argument("--plan", action="store_true", help="only estimate and print the plan")
    ap.add_argument("-r", "--resolution", help="WxH: skip the plan and render at this size")
    ap.add_argument("--fps", type=int)
    ap.add_argument("--preset", default=None, help="x264 preset (default: veryfast on the CPU, medium on a GPU)")
    ap.add_argument("--crf", type=float, default=23.0)
    args = ap.parse_args()
    file = Path(args.file).resolve()
    if args.resolution:
        w, h = map(int, args.resolution.lower().split("x"))
        fps = args.fps or 30
        cpu = on_cpu()
        if cpu:
            os.environ.update(PIN)
        c = _child("--_count", str(file), args.scene or "", str(fps))
    else:
        (w, h, fps, _), c, on_gpu = plan(file, args.scene, args.budget)
        cpu = not on_gpu
        if args.plan:
            return
    preset = args.preset or ("medium" if (w, h, fps) == GPU_LADDER[0] else "veryfast")
    if cpu:
        render_cpu(file, args.scene, w, h, fps, preset, args.crf, c)
    else:
        render(file, args.scene, w, h, fps, preset, args.crf, c["frames"])

if __name__ == "__main__":
    main()
