"""The narration timeline every framework animates to, shared by remotion.py and the others.

build(d) reads <d>/narration.py and <d>/audio/ (clips, durations.json, words.json from
make_narration.py) and lays the lines out in time: sections (a title alone for LEAD seconds), lines,
GAP between lines and PAUSE between sections. Each [bracket] gets the start and end of its words,
aligned to Whisper's word timestamps, so a scene says "when bracket 2 of line bi1 is spoken" instead
of a number of seconds. Lines without a voice yet are estimated from the word count.
narration.py can set SECTIONS = {first_key: "2 · Title"}, THEME, CAPTIONS, GAP (0.5), PAUSE (1.0),
LEAD (1.0), TAIL (2.0), FPS (30), SIZE ((1920, 1080)).
"""
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
sys.path.insert(0, str(HERE))
import style  # noqa: E402
import voice as V  # noqa: E402

WPS = 2.6  # words per second, for the estimate before the voice exists
LEAD_OK = 0.75  # seconds of speech allowed over an empty screen
STILL = 4.0  # seconds of speech allowed with nothing new on screen


def load(d):
    spec = importlib.util.spec_from_file_location("narration", d / "narration.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def srt(tl, out):
    def ts(s):
        ms = round(s * 1000)
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    out.write_text("".join(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n\n"
                           for i, c in enumerate(tl["cues"], 1)))


def prepare(d, json_path, wav_path, quiet=False):
    """Write the timeline to json_path and the narration track to wav_path; return the timeline."""
    tl = build(d)
    Path(json_path).parent.mkdir(parents=True, exist_ok=True)
    Path(json_path).write_text(json.dumps(tl, indent=1))
    Path(wav_path).parent.mkdir(parents=True, exist_ok=True)
    write_track(d, tl, wav_path)
    if not quiet:
        print(f"timeline: {len(tl['lines'])} lines in {len(tl['sections'])} sections, {tl['duration'] / 60:.1f} min, "
              f"theme {tl['theme']['name']}")
        if tl["estimated"]:
            print(f"  estimated from the word count (no voice yet): {' '.join(tl['estimated'])}")
    return tl


def check_reports(d, tl, used, layout):
    """Write layout_report.txt and sync_report.txt beside narration.py, print them; return the count."""
    sync = sync_report(tl, set(used))
    (d / "layout_report.txt").write_text("\n".join(layout) + ("\n" if layout else ""))
    (d / "sync_report.txt").write_text("\n".join(sync) + ("\n" if sync else ""))
    print(f"layout: {len(layout)} problems ({d / 'layout_report.txt'})")
    for x in layout[:30]:
        print("  " + x)
    print(f"sync: {len(sync)} problems ({d / 'sync_report.txt'})")
    for x in sync[:30]:
        print("  " + x)
    if tl["estimated"]:
        print("note: timing is estimated for lines without voice; check again after make_narration.py")
    return len(layout) + len(sync)


def sheets(folder, pattern="[0-9]*.png"):
    """Tile the stills in folder into sheet_NN.png, 9 per sheet; return the sheets."""
    for old in Path(folder).glob("sheet_*.png"):
        old.unlink()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-pattern_type", "glob", "-i",
                    str(Path(folder) / pattern), "-vf", "scale=640:-1,tile=3x3:padding=6:color=0x444444",
                    str(Path(folder) / "sheet_%02d.png")], check=True)
    return sorted(Path(folder).glob("sheet_*.png"))


def mux(video, wav, out):
    """Add the narration track to a silent video."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(wav), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)], check=True)


def stills_at(tl):
    """The default storyboard moments: just after each section title and each [bracket] starts."""
    ts = [s["start"] + 0.9 for s in tl["sections"]]
    for ln in tl["lines"]:
        ts += [min(s["start"] + 0.8, ln["end"]) for s in ln["spans"]]
        ts.append(ln["end"] - 0.05)
    return sorted({round(t * 4) / 4 for t in ts})
