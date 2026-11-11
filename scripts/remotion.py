"""Remotion explainers: set up the project, time it to the narration, check it, render it.

    python3 scripts/remotion.py new <dir>       # <dir> holds narration.py: makes <dir>/remotion/ and installs it
    python3 scripts/remotion.py timeline <dir>  # src/timeline.json and public/narration.wav from the narration
    python3 scripts/remotion.py check <dir>     # storyboard sheets, layout report and sync report
    python3 scripts/remotion.py render <dir> [--budget 10] [--plan] [--scale S] [--captions]

The video is <dir>/remotion/src/Video.tsx, written with the blocks in kit.tsx. Every time in it comes
from the narration: at("bi1", 2) is when bracket 2 of line bi1 is spoken, measured from the audio by
Whisper's word timestamps (audio/words.json from make_narration.py). Before the voice exists the
timeline is estimated from the word count, so the scene can be built while the voice is generated.
narration.py can set SECTIONS = {first_key: "2 · Title"}, THEME ("dark"/"light"), CAPTIONS (burn
captions in), GAP (seconds between lines, 0.5), PAUSE (extra between sections, 1.0), LEAD (title
alone before a section's first line, 1.0), TAIL (2.0), FPS (30).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "templates" / "remotion"
sys.path.insert(0, str(HERE))
import timeline as TL  # noqa: E402
from timeline import load, script_words, srt  # noqa: E402

# files `new` copies from the template every time (Video.tsx is never overwritten)
OWNED = ["package.json", "package-lock.json", "tsconfig.json", ".gitignore", "src/index.tsx", "src/kit.tsx", "src/three.tsx",
         "tools/inspect.mjs", "tools/render.mjs"]


def _need_node():
    if not shutil.which("node") or not shutil.which("npm"):
        sys.exit("Remotion needs Node.js 18+ with npm: https://nodejs.org (see python3 scripts/hardware.py)")


def timeline(d, quiet=False):
    p = d / "remotion"
    if not (p / "src").exists():
        sys.exit(f"no Remotion project in {p}: python3 {HERE / 'remotion.py'} new {d}")
    return TL.prepare(d, p / "src" / "timeline.json", p / "public" / "narration.wav", quiet)


def starter(mod):
    """A Video.tsx to start from: one Section per section, the lines and brackets listed in comments."""
    sections = getattr(mod, "SECTIONS", None) or {next(iter(mod.LINES)): ""}
    out = ["import React from 'react';",
           "import {Arrow, Box, C, Formula, Pointer, Section, Text, at, done} from './kit';", "",
           "// at(key, i) is when bracket i of line `key` starts being spoken; done(key, i) when it ends.",
           "export const Scenes: React.FC = () => <>"]
    keys = list(mod.LINES)
    starts = [k for k in keys if k in sections]
    for n, first in enumerate(starts):
        upto = keys.index(starts[n + 1]) if n + 1 < len(starts) else len(keys)
        out.append(f"  <Section id=\"{first}\">")
        for k in keys[keys.index(first):upto]:
            spans = [" ".join(w for w, s in script_words(mod.LINES[k]) if s == i)
                     for i in range(max([s for _, s in script_words(mod.LINES[k]) if s is not None], default=-1) + 1)]
            out.append(f"    {{/* {k}: " + " | ".join(f"{i} {t[:50]}" for i, t in enumerate(spans)).replace("*/", "* /") + " */}")
        first_span = script_words(mod.LINES[first])
        at = f"at('{first}', 0)" if any(s is not None for _, s in first_span) else "undefined"
        out.append(f"    <Text x={{960}} y={{540}} size={{64}} at={{{at}}}>{sections[first] or first}</Text>")
        out.append("  </Section>")
    out += ["</>;", ""]
    return "\n".join(out)


def new(d):
    _need_node()
    p = d / "remotion"
    for f in OWNED:
        src = TEMPLATE / f
        if src.exists():
            (p / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, p / f)
    (p / "public").mkdir(exist_ok=True)
    video = p / "src" / "Video.tsx"
    if not video.exists():
        video.write_text(starter(load(d)))
    timeline(d)
    subprocess.run(["npm", "ci" if (p / "package-lock.json").exists() else "install", "--no-audit", "--no-fund"],
                   cwd=p, check=True)
    subprocess.run(["npx", "remotion", "browser", "ensure"], cwd=p, check=True)
    print(f"Remotion project ready: {p}  (write the video in {video})")


def check(d, times=None):
    _need_node()
    tl = timeline(d)
    p = d / "remotion"
    sb = p / "storyboard"
    env = {**os.environ, **({"EXPLAINER_GL": gl_flag(d)} if gl_flag(d) else {})}
    subprocess.run(["node", "tools/inspect.mjs", str(sb)] + ([times] if times else []), cwd=p, check=True, env=env)
    data = json.loads((sb / "check.json").read_text())
    sheets = TL.sheets(sb)
    print(f"storyboard: {len(data['frames'])} stills, {len(sheets)} sheets of 9 in {sb}")
    layout = [f"{f['t']:7.2f}s  {prob}" for f in data["frames"] for prob in f["problems"]]
    if times:
        for x in layout:
            print("  " + x)
        return len(layout)
    return TL.check_reports(d, tl, data["used"], layout)


def gl_flag(d):
    """WebGL for a video that uses src/three.tsx: ANGLE on a GPU, SwiftShader (the CPU) without one."""
    video = d / "remotion" / "src" / "Video.tsx"
    if not video.exists() or "./three" not in video.read_text():
        return None
    import hardware
    return "angle" if hardware.gpu_hint() else "swangle"


def render(d, a):
    _need_node()
    tl = timeline(d)
    if tl["estimated"]:
        print(f"warning: no voice yet for {' '.join(tl['estimated'])}: run make_narration.py first", flush=True)
    video = (d / f"{a.name or d.name}.mp4").resolve()
    cmd = ["node", "tools/render.mjs", str(video), "--budget", str(a.budget)]
    cmd += ["--plan"] if a.plan else []
    cmd += ["--scale", str(a.scale)] if a.scale else []
    cmd += ["--concurrency", str(a.concurrency)] if a.concurrency else []
    cmd += ["--captions"] if a.captions else []
    cmd += ["--gl", gl_flag(d)] if gl_flag(d) else []
    subprocess.run(cmd, cwd=d / "remotion", check=True)
    if a.plan:
        return
    srt(tl, video.with_suffix(".srt"))
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                         capture_output=True, text=True, check=False).stdout.strip()
    print(f"video: {video} ({float(dur) / 60:.1f} min)\nsubtitles: {video.with_suffix('.srt')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["new", "timeline", "check", "render"])
    ap.add_argument("dir", type=Path, help="the folder with narration.py")
    ap.add_argument("--budget", type=float, default=10, help="minutes the render may take (default 10)")
    ap.add_argument("--plan", action="store_true", help="only estimate the render")
    ap.add_argument("--scale", type=float, help="force a size: 1 is 1920x1080, 0.6667 is 1280x720")
    ap.add_argument("--concurrency", type=int, help="Chrome workers (default: one per core, 1 GB of RAM each)")
    ap.add_argument("--captions", action="store_true", help="burn captions into the video")
    ap.add_argument("--times", help="check: only these seconds, comma-separated")
    ap.add_argument("--name", help="render: file name of the video (default: the folder's name)")
    a = ap.parse_args()
    d = a.dir.resolve()
    if not (d / "narration.py").exists():
        sys.exit(f"no narration.py in {d}")
    if a.cmd == "new":
        new(d)
    elif a.cmd == "timeline":
        timeline(d)
    elif a.cmd == "check":
        sys.exit(1 if check(d, a.times) else 0)
    else:
        render(d, a)


if __name__ == "__main__":
    main()
