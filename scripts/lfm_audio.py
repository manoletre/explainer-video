"""Thin wrapper around llama.cpp's llama-tts and llama-mtmd-cli (LFM3-Audio-2B GGUF) for TTS and ASR.

The GGUFs live in $LFM_AUDIO_CKPT (default: the LM Studio download folder,
~/.lmstudio/models/LiquidAI/LFM3-Audio-2B-GGUF/), with a llama.cpp release unpacked into
runner/<build>/. scripts/fetch_model.sh sets this up.
"""
import os
import re
import subprocess
from pathlib import Path

CKPT = Path(os.environ.get("LFM_AUDIO_CKPT", Path.home() / ".lmstudio/models/LiquidAI/LFM3-Audio-2B-GGUF"))
BIN = Path(os.environ.get("LFM_AUDIO_RUNNER", CKPT / f"runner/{os.environ.get('LFM_LLAMA_BUILD', 'b11985')}"))
QUANT = os.environ.get("LFM_AUDIO_QUANT", "Q8_0")

# VOICE strings in narration.py, e.g. "US male", "UK female", "es male": a locale and a gender
LOCALES = {"us": "en", "american": "en", "uk": "en-gb", "british": "en-gb", "gb": "en-gb"}


def _model():
    return ["-m", str(CKPT / f"LFM3-Audio-2B-{QUANT}.gguf"), "-mm", str(CKPT / "mmproj-LFM3-Audio-2B-Q8_0.gguf")]


def voice_args(voice):
    ws = voice.lower().split()
    gender = "female" if "female" in ws else "male"
    lang = next((LOCALES.get(w, w) for w in ws if w not in ("male", "female", "voice")), "en")
    return ["--tts-lang", lang, "--tts-voice", gender]


def tts(text, out, voice="US male"):
    out = Path(out)
    out.unlink(missing_ok=True)
    r = subprocess.run([str(BIN / "llama-tts"), *_model(), *voice_args(voice), "-p", text, "-o", str(out)],
                       capture_output=True, text=True, errors="replace")
    if not out.exists():
        raise RuntimeError(f"TTS failed for {text[:40]!r}:\n{r.stderr[-2000:]}")
    return out


def asr(wav, language="English"):
    """The transcript of wav (llama-mtmd-cli prints only the answer to stdout, its logs go to stderr)."""
    r = subprocess.run([str(BIN / "llama-mtmd-cli"), *_model(), "--audio", str(wav),
                        "-sys", f"Perform ASR in {language}.", "-p", "<__media__>", "--temp", "0"],
                       capture_output=True, text=True, errors="replace")
    return " ".join(r.stdout.split())


def best(text, out, voice="US male", tries=3, good=0.08):
    """Speak text up to `tries` times and keep the take whose transcript is closest; returns its WER."""
    out = Path(out)
    top = None
    for i in range(tries):
        take = tts(text, out.with_name(f"_{out.stem}_{i}.wav"), voice)
        err = wer(text, asr(take))
        if top is None or err < top[0]:
            top = (err, take)
        if err <= good:
            break
    top[1].replace(out)
    for f in out.parent.glob(f"_{out.stem}_*.wav"):
        f.unlink()
    return top[0]


DIGITS = "zero one two three four five six seven eight nine".split()


def words(s):
    """Lowercase words with digits spelled out, so "Nf3" and "f three" compare as close as they can."""
    s = re.sub(r"\d", lambda m: f" {DIGITS[int(m.group())]} ", s.lower().replace("-", " "))
    return re.findall(r"[a-z]+", s)


def wer(ref, hyp):
    """Word error rate of hyp against ref (Levenshtein over words)."""
    a, b = words(ref), words(hyp)
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, y in enumerate(b, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (x != y))
    return d[len(b)] / max(1, len(a))


def duration(wav):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)],
                         capture_output=True, text=True).stdout
    return float(out)
