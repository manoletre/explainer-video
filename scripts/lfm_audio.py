"""Thin wrapper around Liquid's llama-liquid-audio-cli (LFM2.5-Audio-1.5B GGUF) for TTS and ASR.

The GGUFs live in $LFM_AUDIO_CKPT (default: the LM Studio download folder,
~/.lmstudio/models/LiquidAI/LFM2.5-Audio-1.5B-GGUF/), with the platform's runner unzipped into
its runner/ subfolder. scripts/fetch_model.sh sets this up.
"""
import os
import platform
import re
import subprocess
from pathlib import Path

CKPT = Path(os.environ.get("LFM_AUDIO_CKPT", Path.home() / ".lmstudio/models/LiquidAI/LFM2.5-Audio-1.5B-GGUF"))
_PLATFORM = {("Darwin", "arm64"): "macos-arm64", ("Linux", "x86_64"): "ubuntu-x64",
             ("Linux", "aarch64"): "ubuntu-arm64"}.get((platform.system(), platform.machine()), "macos-arm64")
CLI = Path(os.environ.get("LFM_AUDIO_RUNNER",
                          CKPT / f"runner/llama-liquid-audio-{_PLATFORM}/llama-liquid-audio-cli"))
QUANT = os.environ.get("LFM_AUDIO_QUANT", "Q8_0")


def _base():
    return [
        str(CLI),
        "-m", str(CKPT / f"LFM2.5-Audio-1.5B-{QUANT}.gguf"),
        "-mm", str(CKPT / "mmproj-LFM2.5-Audio-1.5B-F16.gguf"),
        "-mv", str(CKPT / f"vocoder-LFM2.5-Audio-1.5B-{QUANT}.gguf"),
        "--tts-speaker-file", str(CKPT / f"tokenizer-LFM2.5-Audio-1.5B-{QUANT}.gguf"),
    ]


def tts(text, out, voice="US male", extra=()):
    out = Path(out)
    out.unlink(missing_ok=True)
    cmd = _base() + ["-sys", f"Perform TTS. Use the {voice} voice.", "-p", text, "--output", str(out), *extra]
    for _ in range(3):  # the runner sometimes aborts in Metal teardown before writing the file
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        if out.exists():
            break
    if not out.exists():
        raise RuntimeError(f"TTS failed for {text[:40]!r}:\n{r.stderr[-2000:]}")
    return out


def asr(wav):
    r = subprocess.run(_base() + ["-sys", "Perform ASR.", "--audio", str(wav)], capture_output=True, text=True, errors="replace")
    return r.stdout.strip()


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
