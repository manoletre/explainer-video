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
import difflib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "templates" / "remotion"
sys.path.insert(0, str(HERE))
import style  # noqa: E402
import voice as V  # noqa: E402

# files `new` copies from the template every time (Video.tsx is never overwritten)
OWNED = ["package.json", "package-lock.json", "tsconfig.json", ".gitignore", "src/index.tsx", "src/kit.tsx",
         "tools/inspect.mjs", "tools/render.mjs"]
WPS = 2.6  # words per second, for the estimate before the voice exists
LEAD_OK = 0.75  # seconds of speech allowed over an empty screen
STILL = 4.0  # seconds of speech allowed with nothing new on screen


def load(d):
    spec = importlib.util.spec_from_file_location("narration", d / "narration.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _need_node():
    if not shutil.which("node") or not shutil.which("npm"):
        sys.exit("Remotion needs Node.js 18+ with npm: https://nodejs.org (see python3 scripts/hardware.py)")


def script_words(text):
    """[(word as written, bracket index or None)], punctuation kept on its word."""
    out, span, inside = [], -1, False
    for part in re.split(r"(\[|\])", text):
        if part == "[":
            span, inside = span + 1, True
        elif part == "]":
            inside = False
        else:
            for w in part.split():
                if out and not re.search(r"\w", w):
                    out[-1] = (out[-1][0] + w, out[-1][1])
                else:
                    out.append((w, span if inside else None))
    return out


def align(sw, heard, dur):
    """(start, end) of every script word, from Whisper's heard words; unheard words are interpolated."""
    s_tok, s_of, h_tok, h_t = [], [], [], []
    for i, (w, _) in enumerate(sw):
        for t in V.words(w):
            s_tok.append(t)
            s_of.append(i)
    for h in heard:
        for t in V.words(h["w"]):
            h_tok.append(t)
            h_t.append((h["start"], h["end"]))
    times = [None] * len(sw)

    def put(i, st, en):
        times[i] = (min(times[i][0], st), max(times[i][1], en)) if times[i] else (st, en)

    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, s_tok, h_tok, autojunk=False).get_opcodes():
        if op == "equal":
            for k in range(a2 - a1):
                put(s_of[a1 + k], *h_t[b1 + k])
        elif op == "replace":
            st, en = h_t[b1][0], h_t[b2 - 1][1]
            for k in range(a2 - a1):
                put(s_of[a1 + k], st + (en - st) * k / (a2 - a1), st + (en - st) * (k + 1) / (a2 - a1))
    # words nobody heard: share the gap between their known neighbours
    i = 0
    while i < len(times):
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < len(times) and times[j] is None:
            j += 1
        lo = times[i - 1][1] if i else 0.0
        hi = times[j][0] if j < len(times) else dur
        n = j - i
        for k in range(n):
            times[i + k] = (lo + (hi - lo) * k / n, lo + (hi - lo) * (k + 1) / n)
        i = j
    return times


def cues_of(words):
    """Caption cues from timed words: a sentence or about 70 characters each."""
    cues, cur = [], []
    for w in words:
        if cur and len(" ".join(x["w"] for x in cur + [w])) > 70:
            cues.append(cur)
            cur = []
        cur.append(w)
        if re.search(r"[.?!:;]$", w["w"]):
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)
    return [{"start": c[0]["start"], "end": c[-1]["end"] + 0.25, "text": " ".join(x["w"] for x in c)} for c in cues]


def build(d):
    mod = load(d)
    lines = mod.LINES
    sections = getattr(mod, "SECTIONS", None) or {next(iter(lines)): ""}
    gap, pause, lead, tail = (getattr(mod, k, v) for k, v in (("GAP", 0.5), ("PAUSE", 1.0), ("LEAD", 1.0), ("TAIL", 2.0)))
    fps = getattr(mod, "FPS", 30)
    width, height = getattr(mod, "SIZE", (1920, 1080))
    audio = d / "audio"
    durs = json.loads((audio / "durations.json").read_text()) if (audio / "durations.json").exists() else {}
    heard = json.loads((audio / "words.json").read_text()) if (audio / "words.json").exists() else {}
    t, out, secs, cues, estimated = 0.5, [], [], [], []
    for key, text in lines.items():
        if key in sections:
            if secs:
                t += pause
                secs[-1]["end"] = round(t, 3)
            secs.append({"title": sections[key], "first": key, "start": round(t, 3), "end": None})
            t += lead
        sw = script_words(text)
        wav = audio / f"{key}.wav"
        if key in durs and key in heard and wav.exists():
            dur = durs[key]
            times = align(sw, heard[key], dur)
        else:
            estimated.append(key)
            dur = max(1.5, len(sw) / WPS)
            times = [(dur * i / len(sw), dur * (i + 1) / len(sw)) for i in range(len(sw))] if sw else []
        words = [{"w": w, "start": round(t + a, 3), "end": round(t + b, 3), "span": s}
                 for (w, s), (a, b) in zip(sw, times)]
        n_spans = max([s for _, s in sw if s is not None], default=-1) + 1
        spans = []
        for i in range(n_spans):
            ws = [w for w in words if w["span"] == i]
            spans.append({"i": i, "text": " ".join(w["w"] for w in ws), "start": ws[0]["start"], "end": ws[-1]["end"]})
        out.append({"key": key, "start": round(t, 3), "end": round(t + dur, 3), "text": text, "spans": spans,
                    "words": words})
        cues += cues_of(words)
        t += dur + gap
    total = round(t - gap + tail, 3)
    secs[-1]["end"] = total
    for a, b in zip(cues, cues[1:]):
        a["end"] = min(a["end"], b["start"])
    return {"fps": fps, "width": width, "height": height, "duration": total,
            "captions": bool(getattr(mod, "CAPTIONS", False)), "theme": style.palette(mod),
            "estimated": estimated, "lines": out, "sections": secs, "cues": cues}


def write_track(d, tl, out):
    """One WAV of the whole narration: every clip at its start, silence between."""
    clips = [(ln["start"], d / "audio" / f"{ln['key']}.wav") for ln in tl["lines"]]
    first = next((c for _, c in clips if c.exists()), None)
    params = (1, 2, 24000)
    if first:
        with wave.open(str(first)) as w:
            params = (w.getnchannels(), w.getsampwidth(), w.getframerate())
    ch, sw, rate = params
    frame = ch * sw
    tmp = Path(tempfile.mkdtemp())
    with wave.open(str(out), "wb") as o:
        o.setnchannels(ch)
        o.setsampwidth(sw)
        o.setframerate(rate)
        written = 0
        for start, clip in clips:
            if not clip.exists():
                continue
            with wave.open(str(clip)) as w:
                same = (w.getnchannels(), w.getsampwidth(), w.getframerate()) == params
            if not same:
                conv = tmp / clip.name
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(clip), "-ac", str(ch), "-ar", str(rate),
                                "-sample_fmt", "s16", str(conv)], check=True)
                clip = conv
            with wave.open(str(clip)) as w:
                data = w.readframes(w.getnframes())
            at = round(start * rate)
            if at > written:
                o.writeframes(b"\0" * frame * (at - written))
                written = at
            o.writeframes(data)
            written += len(data) // frame
        end = round(tl["duration"] * rate)
        if end > written:
            o.writeframes(b"\0" * frame * (end - written))
    shutil.rmtree(tmp, ignore_errors=True)


def timeline(d, quiet=False):
    p = d / "remotion"
    if not (p / "src").exists():
        sys.exit(f"no Remotion project in {p}: python3 {HERE / 'remotion.py'} new {d}")
    tl = build(d)
    (p / "src" / "timeline.json").write_text(json.dumps(tl, indent=1))
    (p / "public").mkdir(exist_ok=True)
    write_track(d, tl, p / "public" / "narration.wav")
    if not quiet:
        print(f"timeline: {len(tl['lines'])} lines in {len(tl['sections'])} sections, {tl['duration'] / 60:.1f} min, "
              f"theme {tl['theme']['name']}")
        if tl["estimated"]:
            print(f"  estimated from the word count (no voice yet): {' '.join(tl['estimated'])}")
    return tl


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


def sync_report(tl, used):
    out = []
    sec_first = {s["first"] for s in tl["sections"]}
    for ln in tl["lines"]:
        k = ln["key"]
        on = sorted(s["start"] for s in ln["spans"] if f"{k}:{s['i']}" in used)
        for s in ln["spans"]:
            if f"{k}:{s['i']}" not in used:
                out.append(f"unused   {k} [{s['text']}]: no animation plays on these words; animate it or drop the brackets")
        if k in sec_first:
            first = on[0] if on else ln["end"]
            if first - ln["start"] > LEAD_OK:
                said = " ".join(w["w"] for w in ln["words"] if w["start"] < first)
                out.append(f"dead air {k} {ln['start']:.1f}s: \"{said[:80]}\" is spoken over an empty screen; "
                           "bracket the opening words")
        marks = [ln["start"]] + on + [ln["end"]]
        for a, b in zip(marks, marks[1:]):
            if b - a > STILL and not (k in sec_first and a == ln["start"] and not on):
                said = " ".join(w["w"] for w in ln["words"] if a <= w["start"] < b)
                out.append(f"still    {k} {a:.1f}-{b:.1f}s: \"{said[:80]}\" plays with nothing new on screen; "
                           "bracket the words it refers to and point at or reveal it")
    return out


def check(d, times=None):
    _need_node()
    tl = timeline(d)
    p = d / "remotion"
    sb = p / "storyboard"
    cmd = ["node", "tools/inspect.mjs", str(sb)] + ([times] if times else [])
    subprocess.run(cmd, cwd=p, check=True)
    data = json.loads((sb / "check.json").read_text())
    stills = sorted(sb.glob("[0-9]*.png"))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-pattern_type", "glob", "-i", str(sb / "[0-9]*.png"),
                    "-vf", "scale=640:-1,tile=3x3:padding=6:color=0x444444", str(sb / "sheet_%02d.png")], check=True)
    layout = []
    for f in data["frames"]:
        for prob in f["problems"]:
            layout.append(f"{f['t']:7.2f}s  {prob}")
    sync = [] if times else sync_report(tl, set(data["used"]))
    (d / "layout_report.txt").write_text("\n".join(layout) + ("\n" if layout else ""))
    if not times:
        (d / "sync_report.txt").write_text("\n".join(sync) + ("\n" if sync else ""))
    sheets = sorted(sb.glob("sheet_*.png"))
    print(f"storyboard: {len(stills)} stills ({sb}), {len(sheets)} sheets of 9: {sheets[0] if sheets else ''} ...")
    print(f"layout: {len(layout)} problems ({d / 'layout_report.txt'})")
    for s in layout[:30]:
        print("  " + s)
    if not times:
        print(f"sync: {len(sync)} problems ({d / 'sync_report.txt'})")
        for s in sync[:30]:
            print("  " + s)
    if tl["estimated"]:
        print("note: timing is estimated for lines without voice; check again after make_narration.py")
    return len(layout) + len(sync)


def srt(tl, out):
    def ts(s):
        ms = round(s * 1000)
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    out.write_text("".join(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n\n"
                           for i, c in enumerate(tl["cues"], 1)))


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
