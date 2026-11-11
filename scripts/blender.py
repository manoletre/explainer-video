"""Blender explainers: check and render a scene script written with blender_kit.

    python3 scripts/blender.py check <dir>/<scene>.py     # stills just after every [bracket], sync report
    python3 scripts/blender.py render <dir>/<scene>.py [--budget 10] [--plan] [--scale S]

Blender renders with Eevee on a GPU (fast) and with Cycles on the CPU (a few samples, denoised;
about a second per 960x540 frame on 8 cores for a simple scene, so keep 3D shots short there).
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


def blender_bin():
    for c in [os.environ.get("BLENDER"), shutil.which("blender"), "/Applications/Blender.app/Contents/MacOS/Blender",
              *sorted(map(str, (HOME / "blender").glob("blender-*/blender")))]:
        if c and Path(c).exists():
            return c
    return None


def _run(scene, out, scale, stills=None):
    exe = blender_bin()
    if not exe:
        sys.exit(f"Blender is not installed: {HERE / 'setup_blender.sh'}")
    import hardware
    env = {**os.environ, "EXPLAINER_TIMELINE": str(scene.parent / "blender" / "timeline.json"),
           "EXPLAINER_OUT": str(out), "EXPLAINER_SCALE": str(scale),
           "EXPLAINER_BLENDER_GPU": "1" if hardware.gpu_hint() else "0"}
    if stills:
        env["EXPLAINER_STILLS"] = ",".join(f"{t:.3f}" for t in stills)
    t = time.time()
    r = subprocess.run([exe, "-b", "--python", str(scene)], env=env, capture_output=True, text=True, check=False)
    if r.returncode or "Error" in r.stderr[-2000:] and not list(out.glob("*.png")):
        sys.exit(r.stdout[-3000:] + r.stderr[-3000:])
    return time.time() - t


def prepare(scene):
    d = scene.parent
    return TL.prepare(d, d / "blender" / "timeline.json", d / "blender" / "narration.wav")


def check(scene):
    tl = prepare(scene)
    d = scene.parent
    sb = d / "blender" / "storyboard"
    shutil.rmtree(sb, ignore_errors=True)
    times = TL.stills_at(tl)
    took = _run(scene, sb, 0.5, times)
    (d / "blender" / "timing.json").write_text(json.dumps({"scale": 0.5, "per_frame": took / len(times)}))
    sheets = TL.sheets(sb)
    print(f"storyboard: {len(times)} stills at half size in {took:.0f} s ({took / len(times):.1f} s each); "
          f"{len(sheets)} sheets in {sb}")
    used = json.loads((sb / "check.json").read_text())["used"]
    return TL.check_reports(d, tl, used, [])


def render(scene, a):
    tl = prepare(scene)
    d = scene.parent
    timing = d / "blender" / "timing.json"
    if not timing.exists():
        check(scene)
    tm = json.loads(timing.read_text())
    n = round(tl["duration"] * tl["fps"])
    ladder = [1, 2 / 3, 1 / 2]
    est = {s: tm["per_frame"] * (s / tm["scale"]) ** 2 * n / 60 for s in ladder}
    pick = a.scale or next((s for s in ladder if est[s] <= a.budget), ladder[-1])
    size = lambda s: f"{round(tl['width'] * s)}x{round(tl['height'] * s)}"  # noqa: E731
    print(f"plan: {size(pick)} at {tl['fps']} fps, about {est.get(pick, 0):.0f} min for {n} frames (budget {a.budget} min)")
    if pick != 1 and not a.scale:
        print("limits:\n" + "".join(f"  {size(s)}: about {est[s]:.0f} min (--scale {s:.3f})\n" for s in ladder if s > pick)
              + "  a GPU renders with Eevee instead, many times faster")
    if a.plan:
        return
    frames = d / "blender" / "frames"
    shutil.rmtree(frames, ignore_errors=True)
    took = _run(scene, frames, pick)
    video = d / f"{a.name or scene.stem}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(tl["fps"]), "-start_number", "1", "-i",
                    str(frames / "frame_%04d.png"), "-i", str(d / "blender" / "narration.wav"), "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-shortest", str(video)],
                   check=True)
    TL.srt(tl, video.with_suffix(".srt"))
    print(f"video: {video}  {size(pick)} at {tl['fps']} fps (rendered in {took / 60:.1f} min)\n"
          f"subtitles: {video.with_suffix('.srt')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["check", "render"])
    ap.add_argument("scene", type=Path)
    ap.add_argument("--budget", type=float, default=10)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--scale", type=float)
    ap.add_argument("--name")
    a = ap.parse_args()
    scene = a.scene.resolve()
    if a.cmd == "check":
        sys.exit(1 if check(scene) else 0)
    render(scene, a)


if __name__ == "__main__":
    main()
