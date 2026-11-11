"""Choose the framework for a video: the fastest one that shows what the video needs, on this machine.

    python3 scripts/pick.py diagram chart text        # the needs of the visualization you planned
    python3 scripts/pick.py math-animation formula --json
    python3 scripts/pick.py --list                    # the framework table and the needs

First decide what the video should show (the needs below), then run this. It checks the hardware
(hardware.py), and picks the first framework, fastest first, that does every need well and runs here.
When the hardware rules out the framework that would do the job best, or makes it or the voice slow,
it prints NOTICE lines: tell the user, and ask for feedback at hi@manoletre.com.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hardware  # noqa: E402

FEEDBACK = hardware.FEEDBACK

# what a video can need, and the frameworks that do it well, fastest first
NEEDS = {
    "text": ("titles, labels, short on-screen text, captions", ["remotion", "manimgx"]),
    "diagram": ("boxes, arrows, flows, pipelines, architectures, trees, graphs of nodes", ["remotion", "manimgx"]),
    "chart": ("bar, line, scatter and pie charts of data, growing or updating", ["remotion", "manimgx"]),
    "plot": ("a function's curve drawn on axes, static or traced", ["remotion", "manimgx"]),
    "formula": ("equations shown and highlighted, one step per line (KaTeX in Remotion)", ["remotion", "manimgx"]),
    "code": ("code with highlighted lines, typed or stepped through", ["remotion"]),
    "ui": ("screens, terminals, app mockups, chat transcripts", ["remotion"]),
    "image": ("photos, screenshots, logos, figures from a paper", ["remotion"]),
    "timeline": ("events and phases along a time axis", ["remotion", "manimgx"]),
    "math-animation": (("an equation transforming term by term, curves and shapes morphing, geometric "
                        "constructions, vector fields, linear maps acting on a grid"), ["manimgx"]),
    "3d": ("3D surfaces, solids and camera moves around them", ["manimgx"]),
}

# the framework table. "ready": this skill sets it up and renders it; the others are listed so the
# agent can recommend them when one is clearly the right tool, but the skill doesn't drive them.
FRAMEWORKS = {
    "remotion": {
        "ready": True,
        "what": "React + SVG/CSS, rendered frame by frame in headless Chrome",
        "good": "diagrams, charts, text and typography, code, UI mockups, images, static formulas (KaTeX), "
                "everything 2D",
        "weak": "morphing equations and shapes, real 3D math",
        "hardware": "CPU only; 2 GB RAM, about 1 GB per Chrome worker; Node 18+",
        "speed": "8 min of 1080p30 in about 5 min on 8 CPU cores, no GPU",
    },
    "manimgx": {
        "ready": True,
        "what": "Manim's Python API on a wgpu (Metal/Vulkan) renderer",
        "good": "math: equations transforming, function graphs, geometry, linear algebra, 3D surfaces and cameras",
        "weak": "UI, images, dense text layout; slow without a GPU",
        "hardware": "a GPU with Metal or Vulkan; without one, Mesa's lavapipe on the CPU",
        "speed": "GPU: 1080p60 in minutes. CPU (8 cores): 8 min of video in 41 min at 1080p30, 9 min at 540p",
    },
    "motion-canvas": {
        "ready": False,
        "what": "TypeScript generators on a canvas, rendered in a browser",
        "good": "Manim-style vector tweening, code animations, LaTeX",
        "weak": "few agent examples; render through its editor or a headless browser",
        "hardware": "CPU (browser)",
        "speed": "close to Remotion",
    },
    "manim-ce": {
        "ready": False,
        "what": "Manim Community, drawn with Cairo on the CPU",
        "good": "the same math as ManimGX, with the most examples online",
        "weak": "slow at 1080p60; no GPU path",
        "hardware": "CPU",
        "speed": "minutes per minute of video at 1080p",
    },
    "three": {
        "ready": False,
        "what": "three.js / React Three Fiber, inside Remotion through @remotion/three",
        "good": "3D that isn't math: models, molecules, scenes, product shots",
        "weak": "needs WebGL; on the CPU Chrome falls back to SwiftShader, which is slow",
        "hardware": "a GPU for anything big",
        "speed": "GPU: fast; CPU: slow",
    },
    "blender": {
        "ready": False,
        "what": "Blender (Eevee/Cycles), scripted in Python",
        "good": "photoreal 3D, physics, cinematic shots",
        "weak": "slow to write and render; overkill for explainers",
        "hardware": "a GPU",
        "speed": "minutes per second of video on the CPU",
    },
}
ORDER = [n for n in FRAMEWORKS if FRAMEWORKS[n]["ready"]]  # fastest first


def table():
    rows = ["| framework | set up by the skill | good for | weak at | hardware | speed |", "|---|---|---|---|---|---|"]
    for n, f in FRAMEWORKS.items():
        rows.append(f"| {n} | {'yes' if f['ready'] else 'no'} | {f['good']} | {f['weak']} | {f['hardware']} | {f['speed']} |")
    rows += ["", "| need | what it covers | done well by |", "|---|---|---|"]
    rows += [f"| {k} | {d} | {', '.join(fs)} |" for k, (d, fs) in NEEDS.items()]
    return "\n".join(rows)


def choose(needs, p=None):
    p = p or hardware.profile()
    fw = hardware.frameworks(p)
    unknown = [n for n in needs if n not in NEEDS]
    if unknown:
        raise SystemExit(f"unknown needs {unknown}; choose from: {', '.join(NEEDS)}")
    able = [f for f in ORDER if all(f in NEEDS[n][1] for n in needs)]
    best = able[0] if able else "manimgx"  # nothing does all of it: ManimGX does the most
    notices, fix = [], []
    choice = best
    b = fw[best]
    hard = [n for n in needs if best not in NEEDS[n][1]]
    if b["status"] == "unavailable":
        others = [f for f in ORDER if f != best and fw[f]["status"] != "unavailable"]
        if others:
            choice = others[0]
            lost = [n for n in needs if choice not in NEEDS[n][1]]
            notices.append(f"{best} would do this video best, but this machine can't run it: {b['why']}. "
                           f"Using {choice} instead" + (f"; {', '.join(lost)} will be approximated "
                           "(successive frames instead of morphs, flat instead of 3D)" if lost else "") + ".")
        else:
            notices.append(f"No framework can render on this machine: {b['why']}.")
            choice = None
    elif b["status"] == "slow":
        alt = next((f for f in ORDER if f != best and fw[f]["status"] in ("fast", "setup")), None)
        msg = f"{best} is needed for {', '.join(n for n in needs if NEEDS[n][1] == [best]) or 'this video'}, but " \
              f"this machine is slow for it: {b['why']}."
        if best == "manimgx":
            msg += (" By default render.py picks the best format that finishes in 10 minutes (lower resolution). "
                    "Options: a longer render at a higher resolution, rendering on a machine with a GPU (the "
                    "user's laptop, or a small rented cloud GPU)")
            if alt:
                msg += f", or {alt} at full resolution, approximating the math animation with successive frames"
            msg += ". Let the user choose; use the default if they don't answer."
        notices.append(msg)
    if hard:
        notices.append(f"No framework set up by this skill does {', '.join(hard)} well; it will be approximated.")
    if choice:
        fix += fw[choice]["fix"]
    v = fw["voice"]
    fix += v["fix"] if v["status"] in ("setup", "unavailable") else []
    if v["status"] == "unavailable":
        notices.append(f"Kokoro can't narrate on this machine: {v['why']}. Options: the 92 MB int8 model "
                       "(KOKORO_MODEL=int8), generating the narration on another machine and copying its audio/ "
                       "folder here, or a silent video with captions.")
    elif v["status"] == "slow":
        notices.append(f"Narration will be slow here: {v['why']}. Generate it in the background while you build "
                       "the scene.")
    return {"needs": needs, "best": best, "choice": choice, "frameworks": fw, "fix": fix,
            "notices": [f"{n} Tell the user, and ask for feedback at {FEEDBACK}." for n in notices]}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--list" in sys.argv or not args:
        print(table())
        return 0
    r = choose(args, hardware.profile(probe="--no-probe" not in sys.argv))
    if "--json" in sys.argv:
        print(json.dumps(r, indent=1))
        return 0 if r["choice"] else 2
    print(f"needs     {', '.join(r['needs'])}")
    print(f"best      {r['best']}: {FRAMEWORKS[r['best']]['good']}")
    for name, f in r["frameworks"].items():
        print(f"{name:9s} {f['status']}: {f['why']}")
    print(f"CHOICE    {r['choice'] or 'none'}")
    for s in r["fix"]:
        print(f"FIX       {s}")
    for s in r["notices"]:
        print(f"NOTICE    {s}")
    return 0 if r["choice"] else 2


if __name__ == "__main__":
    sys.exit(main())
