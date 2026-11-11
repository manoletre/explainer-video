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

# what a video can need, and the frameworks that do it well
W = ["remotion", "three"]  # three is Remotion with 3D blocks, so it does everything Remotion does
NEEDS = {
    "text": ("titles, labels, short on-screen text, captions", W + ["motion-canvas", "manimgx", "manim-ce"]),
    "diagram": ("boxes, arrows, flows, pipelines, architectures, trees, graphs of nodes",
                W + ["motion-canvas", "manimgx", "manim-ce"]),
    "chart": ("bar, line, scatter and pie charts of data, growing or updating", W + ["manimgx", "manim-ce"]),
    "plot": ("a function's curve drawn on axes, static or traced", W + ["manimgx", "manim-ce"]),
    "formula": ("equations shown and highlighted, one step per line (KaTeX in Remotion)", W + ["manimgx", "manim-ce"]),
    "code": ("code with highlighted lines, typed or stepped through", W + ["motion-canvas"]),
    "ui": ("screens, terminals, app mockups, chat transcripts", W),
    "image": ("photos, screenshots, logos, figures from a paper", W),
    "timeline": ("events and phases along a time axis", W + ["motion-canvas", "manimgx", "manim-ce"]),
    "vector-tween": ("2D shapes and paths moving, re-linking and re-arranging with smooth tweens (a node "
                     "inserted, pointers retargeted, a layout reflowing)", ["motion-canvas", "manimgx", "manim-ce"]),
    "math-animation": (("an equation transforming term by term, curves and shapes morphing, geometric "
                        "constructions, vector fields, linear maps acting on a grid"), ["manimgx", "manim-ce"]),
    "3d-math": ("3D surfaces, solids of revolution, 3D vector fields, with camera moves around them", ["manimgx"]),
    "3d": ("3D objects that aren't math: molecules, models, products, rooms, with camera moves",
           ["three", "blender", "manimgx"]),
    "photoreal": ("realistic lighting, materials and shadows, physics, cinematic shots", ["blender"]),
}

# the framework table; the skill sets up and renders all of them. ORDER: preferred first, when the
# hardware runs them equally well (choose() prefers fast over setup over slow).
FRAMEWORKS = {
    "remotion": {
        "what": "React + SVG/CSS, rendered frame by frame in headless Chrome",
        "good": "diagrams, charts, text and typography, code, UI mockups, images, static formulas (KaTeX), "
                "everything 2D",
        "weak": "morphing equations and shapes, real 3D math",
        "hardware": "CPU only; 2 GB RAM, about 1 GB per Chrome worker; Node 18+",
        "speed": "8 min of 1080p30 in about 5 min on 8 CPU cores, no GPU",
        "run": "scripts/remotion.py new|check|render <dir>",
    },
    "motion-canvas": {
        "what": "TypeScript generators on a 2D canvas, rendered in headless Chrome",
        "good": "Manim-style vector tweening: shapes and arrows moving and re-linking, code animations",
        "weak": "charts, images and dense layout (no HTML/CSS); fewer agent examples than Remotion",
        "hardware": "CPU only; Node 18+, about 300 MB of packages per project",
        "speed": "18 s of 1080p30 in 14 s on 8 CPU cores",
        "run": "scripts/motion_canvas.py new|check|render <dir>",
    },
    "three": {
        "what": "three.js (React Three Fiber) inside the Remotion project, through @remotion/three",
        "good": "3D that isn't math: molecules, models, objects, camera moves; mixed with any Remotion 2D block",
        "weak": "photoreal lighting; on the CPU WebGL falls back to SwiftShader, which is slow for heavy scenes",
        "hardware": "a GPU for heavy scenes; simple ones render on the CPU",
        "speed": "GPU: fast. CPU (8 cores): a simple 20 s 3D shot at 1080p30 in 39 s",
        "run": "scripts/remotion.py (import from './three' in Video.tsx)",
    },
    "manimgx": {
        "what": "Manim's Python API on a wgpu (Metal/Vulkan) renderer",
        "good": "math: equations transforming, function graphs, geometry, linear algebra, 3D surfaces and cameras",
        "weak": "UI, images, dense text layout; slow without a GPU",
        "hardware": "a GPU with Metal or Vulkan; without one, Mesa's lavapipe on the CPU",
        "speed": "GPU: 1080p60 in minutes. CPU (8 cores): 8 min of video in 41 min at 1080p30, 9 min at 540p",
        "run": "scripts/render.py <scene>.py",
    },
    "manim-ce": {
        "what": "Manim Community, drawn with Cairo on the CPU",
        "good": "the same 2D math as ManimGX (transforms, graphs, geometry), with the most examples online",
        "weak": "3D (slow in Cairo); UI and images",
        "hardware": "CPU only, one core per render; Cairo/Pango, LaTeX + dvisvgm for formulas",
        "speed": "27 s of 1080p30 with a formula transform in 12 s",
        "run": "scripts/manim_ce.py check|render <scene>.py",
    },
    "blender": {
        "what": "Blender 4.2, scripted in Python (blender_kit.py); Eevee on a GPU, Cycles on the CPU",
        "good": "photoreal 3D: lighting, materials, shadows, physics, cinematic shots",
        "weak": "slow to render without a GPU; overkill for diagrams and text",
        "hardware": "a GPU; on the CPU about 1.7 s per 960x540 frame on 8 cores",
        "speed": "GPU: minutes. CPU (8 cores): about 15 min per 30 s of 960x540",
        "run": "scripts/blender.py check|render <scene>.py",
    },
}
ORDER = ["remotion", "motion-canvas", "three", "manimgx", "manim-ce", "blender"]
RANK = {"fast": 0, "setup": 1, "slow": 2, "unavailable": 3}


def table():
    rows = ["| framework | good for | weak at | hardware | speed | run |", "|---|---|---|---|---|---|"]
    for n in ORDER:
        f = FRAMEWORKS[n]
        rows.append(f"| {n} | {f['good']} | {f['weak']} | {f['hardware']} | {f['speed']} | `{f['run']}` |")
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
    if not able:  # nothing does all of it: the one that does the most
        able = sorted(ORDER, key=lambda f: -sum(f in NEEDS[n][1] for n in needs))[:1]
    best = able[0]
    usable = [f for f in able if fw[f]["status"] != "unavailable"]
    choice = min(usable, key=lambda f: (RANK[fw[f]["status"]], ORDER.index(f))) if usable else None
    notices, fix = [], []
    hard = [n for n in needs if best not in NEEDS[n][1]]
    b = fw[best]
    if choice is None:
        others = [f for f in ORDER if fw[f]["status"] != "unavailable"]
        if others:
            choice = min(others, key=lambda f: (RANK[fw[f]["status"]], -sum(f in NEEDS[n][1] for n in needs)))
            lost = [n for n in needs if choice not in NEEDS[n][1]]
            notices.append(f"{best} would do this video best, but this machine can't run it: {b['why']}. Using "
                           f"{choice} instead; {', '.join(lost)} will be approximated (successive frames instead of "
                           "morphs, flat instead of 3D).")
        else:
            notices.append(f"No framework can render on this machine: {b['why']}.")
    elif choice != best and b["status"] in ("slow", "unavailable"):
        notices.append(f"{best} would do this video best, but {'it is slow' if b['status'] == 'slow' else 'it cannot run'}"
                       f" here: {b['why']}. Using {choice} instead: {fw[choice]['why']}.")
    if choice and fw[choice]["status"] == "slow":
        msg = f"{choice} is the framework for {', '.join(needs)}, but this machine is slow for it: {fw[choice]['why']}."
        if choice == "manimgx":
            msg += (" By default render.py picks the best format that finishes in 10 minutes (lower resolution). "
                    "Options: a longer render at a higher resolution, or rendering on a machine with a GPU (the "
                    "user's laptop, or a small rented cloud GPU)")
        else:
            msg += (" The render picks the best size that finishes in 10 minutes (--budget to change it). Options: "
                    "a longer render, a machine with a GPU, or fewer/shorter 3D shots")
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
