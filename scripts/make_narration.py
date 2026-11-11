"""Speak every narration line with Kokoro, then check and time it with Whisper.

    python3 make_narration.py path/to/narration.py           # all missing clips; written to path/to/audio/
    python3 make_narration.py path/to/narration.py sb2 dr6   # redo these

Writes audio/<key>.wav, audio/report.json (word error rate and transcript per line),
audio/words.json (every heard word with its start and end, which the Remotion timeline uses) and
audio/durations.json. Kokoro is deterministic, so a line comes out the same every time: a line flagged
`<-- check` is fixed by rewriting it, not by running it again.
Runs itself in the voice environment from setup_voice.sh when this Python lacks the packages.
"""
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import voice as V  # noqa: E402

if V.missing():
    py = V.python()
    if py is None or Path(py).resolve() == Path(sys.executable).resolve():
        sys.exit("The voice is not set up: " + "; ".join(V.missing()) + f"\nRun {HERE / 'setup_voice.sh'}")
    os.execv(py, [py, *sys.argv])

FLAG = 0.15  # word error rate above which a line is flagged


def load(script):
    spec = importlib.util.spec_from_file_location("narration", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def plain(line):
    """The words as spoken: without the [brackets]."""
    return " ".join(line.replace("[", "").replace("]", "").split())


def _json(path):
    return json.loads(path.read_text()) if path.exists() else {}


def main(script, keys):
    mod = load(script)
    lines, voice, speed = mod.LINES, getattr(mod, "VOICE", "am_michael"), getattr(mod, "SPEED", 1.0)
    out = script.parent / "audio"
    out.mkdir(exist_ok=True)
    keys = keys or [k for k in lines if not (out / f"{k}.wav").exists()]
    report, timed = _json(out / "report.json"), _json(out / "words.json")
    print(f"voice {V.voice_id(voice)} ({V.MODEL_FILE.name}), {len(keys)} lines", flush=True)
    t0, spoken = time.time(), 0.0
    for key in keys:
        text = plain(lines[key])
        wav = V.tts(text, out / f"{key}.wav", voice, speed)
        hyp, ws = V.asr(wav, voice)
        err, secs = V.wer(text, hyp), V.duration(wav)
        spoken += secs
        report[key] = {"wer": round(err, 3), "words_per_sec": round(len(V.words(text)) / secs, 2), "asr": hyp}
        timed[key] = ws
        flag = "  <-- check" if err > FLAG else ""
        print(f"{key:6s} wer={err:.2f} {secs:5.1f}s  {hyp[:90]}{flag}", flush=True)
        (out / "report.json").write_text(json.dumps(report, indent=1))
        (out / "words.json").write_text(json.dumps(timed, indent=1))
    durs = {k: round(V.duration(out / f"{k}.wav"), 3) for k in lines if (out / f"{k}.wav").exists()}
    (out / "durations.json").write_text(json.dumps(durs, indent=1))
    took = time.time() - t0
    if spoken:
        print(f"spoke {spoken:.0f}s of audio in {took:.0f}s ({took / spoken:.2f}x real time)")
    print(f"total narration: {sum(durs.values()):.0f}s over {len(durs)} clips")
    bad = [k for k in lines if report.get(k, {}).get("wer", 0) > FLAG]
    if bad:
        print("flagged (read the transcript, rewrite the line in plainer spoken words, redo it): " + " ".join(bad))


if __name__ == "__main__":
    args = sys.argv[1:]
    script = Path(args.pop(0)) if args and args[0].endswith(".py") else Path.cwd() / "narration.py"
    main(script.resolve(), args)
