"""Generate narration clips with LFM2.5-Audio and check each one by transcribing it back.

Each line is synthesized up to TRIES times; the take whose ASR transcript is closest to the script wins.
Writes audio/<key>.wav and audio/durations.json.

    python make_narration.py path/to/narration.py           # all missing clips; written to path/to/audio/
    python make_narration.py path/to/narration.py sb2 dr6   # redo these
"""
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import lfm_audio as L

SCRIPT = Path(sys.argv.pop(1)) if len(sys.argv) > 1 and sys.argv[1].endswith(".py") else Path(__file__).parent / "narration.py"
_spec = importlib.util.spec_from_file_location("narration", SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
LINES, VOICE = _mod.LINES, _mod.VOICE

OUT = SCRIPT.parent / "audio"
TRIES = 3
GOOD = 0.08  # stop retrying below this word error rate


def transcript(wav):
    out = L.asr(wav)
    return out.split("=== GENERATED TEXT ===")[-1].strip().splitlines()[0] if "=== GENERATED TEXT ===" in out else ""


def main(keys):
    OUT.mkdir(exist_ok=True)
    report_path = OUT / "report.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    for key in keys:
        text = " ".join(LINES[key].replace("[", "").replace("]", "").split())  # say() brackets are not spoken
        best = None
        for t in range(TRIES):
            take = OUT / f"_{key}_{t}.wav"
            L.tts(text, take, VOICE)
            hyp = transcript(take)
            err = L.wer(text, hyp)
            # a take that is far longer than the text needs usually means babbling or a long silence
            secs = L.duration(take)
            rate = len(L.words(text)) / secs
            if best is None or (err, -rate) < (best[0], -best[3]):
                best = (err, take, hyp, rate)
            if err <= GOOD:
                break
        err, take, hyp, rate = best
        shutil.copy(take, OUT / f"{key}.wav")
        for f in OUT.glob(f"_{key}_*.wav"):
            f.unlink()
        report[key] = {"wer": round(err, 3), "words_per_sec": round(rate, 2), "asr": hyp}
        flag = "  <-- check" if err > 0.15 else ""
        print(f"{key:6s} wer={err:.2f} {rate:.1f} w/s  {hyp[:90]}{flag}", flush=True)
        report_path.write_text(json.dumps(report, indent=1))

    durs = {k: round(L.duration(OUT / f"{k}.wav"), 3) for k in LINES if (OUT / f"{k}.wav").exists()}
    (OUT / "durations.json").write_text(json.dumps(durs, indent=1))
    print(f"total narration: {sum(durs.values()):.0f}s over {len(durs)} clips")


if __name__ == "__main__":
    keys = sys.argv[1:] or [k for k in LINES if not (OUT / f"{k}.wav").exists()]
    main(keys)
