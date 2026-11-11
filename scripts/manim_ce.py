"""Manim Community explainers: check and render a scene written with manim_ce_kit.

    python3 scripts/manim_ce.py check <dir>/<scene>.py    # storyboard sheets, layout and sync reports
    python3 scripts/manim_ce.py render <dir>/<scene>.py [--budget 10] [--plan] [-r 1280x720 --fps 30]

Manim Community draws with Cairo on the CPU (no GPU needed, one core per render). `check` renders a
quick 854x480 at 15 fps preview, takes a still just after every [bracket] starts, and times it; `render`
scales that time to each format and renders the best one that fits the budget.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import timeline as TL  # noqa: E402

HOME = Path(os.environ.get("EXPLAINER_HOME", Path.home() / ".cache/explainer-video"))
MANIM = HOME / "manim-ce" / "bin" / "manim"
LADDER = [(1920, 1080, 30), (1280, 720, 30), (960, 540, 24), (854, 480, 15)]
PREVIEW = (854, 480, 15)


def _manim():
    if not MANIM.exists():
        sys.exit(f"Manim Community is not set up: {HERE / 'setup_manim_ce.sh'}")
    return str(MANIM)


def _scene_name(scene):
    import ast
    tree = ast.parse(scene.read_text())
    names = [n.name for n in tree.body if isinstance(n, ast.ClassDef)
             and any(getattr(b, "id", getattr(b, "attr", "")) == "Explainer" for b in n.bases)]
    if not names:
        sys.exit(f"no Explainer subclass in {scene}")
    return names[0]


def run(scene, w, h, fps, out):
    work = scene.parent / "manim-ce" / "media"
    cmd = [_manim(), "render", str(scene), _scene_name(scene), "--resolution", f"{w},{h}", "--frame_rate", str(fps),
           "--media_dir", str(work), "-o", "explainer", "--disable_caching", "--progress_bar", "none"]
    t = time.time()
    r = subprocess.run(cmd, cwd=scene.parent, capture_output=True, text=True, check=False)
    if r.returncode:
        sys.exit(r.stdout[-3000:] + r.stderr[-3000:])
    made = sorted(work.rglob("explainer.mp4"), key=lambda p: p.stat().st_mtime)[-1]
    shutil.move(str(made), out)
    return time.time() - t


def check(scene):
    d = scene.parent
    sb = d / "manim-ce" / "storyboard"
    shutil.rmtree(sb, ignore_errors=True)
    sb.mkdir(parents=True)
    preview = d / "manim-ce" / "preview.mp4"
    took = run(scene, *PREVIEW, preview)
    (d / "manim-ce" / "timing.json").write_text(json.dumps({"preview": PREVIEW, "seconds": took}))
    tl = json.loads((d / "manim-ce" / "timeline.json").read_text())
    for i, t in enumerate(TL.stills_at(tl)):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(preview), "-frames:v", "1",
                        "-vf", f"drawtext=text='{t:.2f}s':x=8:y=8:fontsize=16:fontcolor=red",
                        str(sb / f"{i:03d}_{t:.2f}s.png")], check=False)
    sheets = TL.sheets(sb)
    print(f"preview: {preview} (rendered in {took:.0f} s); storyboard: {len(sheets)} sheets in {sb}")
    data = json.loads((d / "manim-ce" / "check.json").read_text())
    return TL.check_reports(d, tl, data["used"], data["problems"])


def render(scene, a):
    d = scene.parent
    timing = d / "manim-ce" / "timing.json"
    if not timing.exists():
        print("timing the scene with a quick preview first")
        check(scene)
    tm = json.loads(timing.read_text())
    pw, ph, pf = tm["preview"]
    est = {f: tm["seconds"] * (f[0] * f[1] * f[2]) / (pw * ph * pf) / 60 for f in LADDER}
    if a.r:
        w, h = map(int, a.r.split("x"))
        pick = (w, h, a.fps or 30)
    else:
        pick = next((f for f in LADDER if est[f] <= a.budget), LADDER[-1])
    print(f"plan: {pick[0]}x{pick[1]} at {pick[2]} fps, about {est.get(pick, 0):.1f} min (budget {a.budget} min)")
    better = [f for f in LADDER if f[0] * f[1] * f[2] > pick[0] * pick[1] * pick[2]]
    if better and not a.r:
        print("limits:")
        for f in better:
            print(f"  {f[0]}x{f[1]} at {f[2]} fps: about {est[f]:.0f} min (--budget {int(est[f]) + 1})")
    if a.plan:
        return
    out = d / f"{a.name or scene.stem}.mp4"
    took = run(scene, *pick, out)
    tl = json.loads((d / "manim-ce" / "timeline.json").read_text())
    TL.srt(tl, out.with_suffix(".srt"))
    print(f"video: {out}  {pick[0]}x{pick[1]} at {pick[2]} fps (rendered in {took / 60:.1f} min)\n"
          f"subtitles: {out.with_suffix('.srt')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["check", "render"])
    ap.add_argument("scene", type=Path)
    ap.add_argument("--budget", type=float, default=10)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("-r", help="force a size, e.g. 1280x720")
    ap.add_argument("--fps", type=int)
    ap.add_argument("--name")
    a = ap.parse_args()
    scene = a.scene.resolve()
    if a.cmd == "check":
        sys.exit(1 if check(scene) else 0)
    render(scene, a)


if __name__ == "__main__":
    main()
