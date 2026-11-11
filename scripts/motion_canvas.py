"""Motion Canvas explainers: set up the project, time it to the narration, check it, render it.

    python3 scripts/motion_canvas.py new <dir>      # <dir> holds narration.py: makes <dir>/motion-canvas/
    python3 scripts/motion_canvas.py check <dir>    # storyboard sheets and sync report
    python3 scripts/motion_canvas.py render <dir> [--budget 10] [--plan] [--scale S]

The video is <dir>/motion-canvas/src/scenes/video.tsx, a generator that waits for the narration:
`yield* beat('bi1', 2, box().opacity(1, 0.5))` plays when bracket 2 of line bi1 is spoken. Frames are
drawn on a 2D canvas in headless Chrome (CPU, no GPU needed), written as PNGs, then joined with the
narration by ffmpeg.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "templates" / "motion-canvas"
sys.path.insert(0, str(HERE))
import timeline as TL  # noqa: E402

OWNED = ["package.json", "package-lock.json", "tsconfig.json", ".gitignore", "vite.config.ts", "render.html",
         "render.ts", "motion-canvas.d.ts", "src/project.ts", "src/kit.tsx", "tools/render.mjs"]
STARTER = """import {makeScene2D, Txt} from '@motion-canvas/2d';
import {C, beat, finish, section} from '../kit';

export default makeScene2D(function* (view) {
  view.fill(C.bg);
%s  yield* finish();
});
"""


def _need_node():
    if not shutil.which("node") or not shutil.which("npm"):
        sys.exit("Motion Canvas needs Node.js 18+ with npm: https://nodejs.org (see python3 scripts/hardware.py)")


def timeline(d, quiet=False):
    p = d / "motion-canvas"
    return TL.prepare(d, p / "src" / "timeline.json", p / "public" / "narration.wav", quiet)


def new(d):
    _need_node()
    p = d / "motion-canvas"
    for f in OWNED:
        (p / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(TEMPLATE / f, p / f)
    video = p / "src" / "scenes" / "video.tsx"
    if not video.exists():
        mod = TL.load(d)
        secs = getattr(mod, "SECTIONS", None) or {next(iter(mod.LINES)): ""}
        body = "".join(f"  yield* section(view, '{k}');\n" for k in secs)
        video.parent.mkdir(parents=True, exist_ok=True)
        video.write_text(STARTER % body)
    timeline(d)
    subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=p, check=True)
    print(f"Motion Canvas project ready: {p}  (write the video in {video})")


def _render(d, name, scale, fps=None):
    p = d / "motion-canvas"
    shutil.rmtree(p / "output" / name, ignore_errors=True)
    r = subprocess.run(["node", "tools/render.mjs", name, str(scale)] + ([str(fps)] if fps else []), cwd=p,
                       capture_output=True, text=True, check=False)
    sys.stderr.write("".join(ln + "\n" for ln in r.stderr.splitlines() if "render:" in ln or "error" in ln.lower()))
    if r.returncode or not r.stdout.strip():
        sys.exit(f"Motion Canvas render failed:\n{r.stdout[-2000:]}\n{r.stderr[-3000:]}")
    out = json.loads(r.stdout.strip().splitlines()[-1])
    if out["result"] != 0:
        sys.exit(f"Motion Canvas render did not finish (result {out['result']}); see the errors above")
    return out


def check(d):
    _need_node()
    tl = timeline(d)
    p = d / "motion-canvas"
    out = _render(d, "preview", 0.5)
    (p / "timing.json").write_text(json.dumps({"scale": 0.5, "seconds": out["seconds"], "frames": out["frames"]}))
    sb = p / "storyboard"
    shutil.rmtree(sb, ignore_errors=True)
    sb.mkdir()
    frames = sorted((p / "output" / "preview").glob("*.png"))
    for i, t in enumerate(TL.stills_at(tl)):
        k = min(len(frames) - 1, round(t * tl["fps"]))
        shutil.copy(frames[k], sb / f"{i:03d}_{t:.2f}s.png")
    sheets = TL.sheets(sb)
    print(f"preview: {out['frames']} frames at half size in {out['seconds']:.0f} s; {len(sheets)} sheets in {sb}")
    return TL.check_reports(d, tl, out["used"], [])


def render(d, a):
    _need_node()
    tl = timeline(d)
    p = d / "motion-canvas"
    if not (p / "timing.json").exists():
        check(d)
    tm = json.loads((p / "timing.json").read_text())
    ladder = [1, 2 / 3, 1 / 2]
    est = {s: tm["seconds"] * (s / tm["scale"]) ** 2 * 1.2 / 60 for s in ladder}
    pick = a.scale or next((s for s in ladder if est[s] <= a.budget), ladder[-1])
    size = lambda s: f"{round(tl['width'] * s)}x{round(tl['height'] * s)}"  # noqa: E731
    print(f"plan: {size(pick)} at {tl['fps']} fps, about {est.get(pick, 0):.1f} min (budget {a.budget} min)")
    if pick != 1 and not a.scale:
        print("limits:\n" + "".join(f"  {size(s)}: about {est[s]:.0f} min (--scale {s:.3f})\n" for s in ladder if s > pick))
    if a.plan:
        return
    out = _render(d, "video", pick)
    video = d / f"{a.name or d.name}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(tl["fps"]), "-i",
                    str(p / "output" / "video" / "%06d.png"), "-i", str(p / "public" / "narration.wav"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", str(video)], check=True)
    shutil.rmtree(p / "output", ignore_errors=True)
    TL.srt(tl, video.with_suffix(".srt"))
    print(f"video: {video}  {size(pick)} at {tl['fps']} fps (frames drawn in {out['seconds'] / 60:.1f} min)\n"
          f"subtitles: {video.with_suffix('.srt')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["new", "timeline", "check", "render"])
    ap.add_argument("dir", type=Path)
    ap.add_argument("--budget", type=float, default=10)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--scale", type=float)
    ap.add_argument("--name")
    a = ap.parse_args()
    d = a.dir.resolve()
    if not (d / "narration.py").exists():
        sys.exit(f"no narration.py in {d}")
    if a.cmd == "new":
        new(d)
    elif a.cmd == "timeline":
        timeline(d)
    elif a.cmd == "check":
        sys.exit(1 if check(d) else 0)
    else:
        render(d, a)


if __name__ == "__main__":
    main()
