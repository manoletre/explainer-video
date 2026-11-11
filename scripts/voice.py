"""The narration voice: Kokoro for speech (TTS), faster-whisper to check it and time every word (ASR).

Both run on the CPU, offline, in the voice environment that scripts/setup_voice.sh makes
($EXPLAINER_HOME/venv, default ~/.cache/explainer-video/venv). Kokoro (82M parameters, ONNX) speaks
about 4 times faster than real time on 8 cores and about real time on one, in under 700 MB of RAM;
KOKORO_MODEL=int8 is the 92 MB model, a little rougher, in about 400 MB.

VOICE in narration.py is a Kokoro voice id ("am_michael", "af_heart", "bf_emma", ...; the first letter
is the language, the second the gender) or the older "US male" / "UK female" / "es male" form.
"""
import os
import re
import sys
from pathlib import Path

HOME = Path(os.environ.get("EXPLAINER_HOME", Path.home() / ".cache/explainer-video"))
VENV = HOME / "venv"
MODELS = HOME / "kokoro"
MODEL = os.environ.get("KOKORO_MODEL", "fp32")  # fp32 (325 MB) or int8 (92 MB)
MODEL_FILE = MODELS / ("kokoro-v1.0.int8.onnx" if MODEL == "int8" else "kokoro-v1.0.onnx")
VOICES_FILE = MODELS / "voices-v1.0.bin"
ASR_MODEL = os.environ.get("EXPLAINER_ASR_MODEL", "")  # default: base.en for English, base otherwise

# "US male" style names -> Kokoro voices (the best-rated voice of each kind)
NAMED = {("us", "female"): "af_heart", ("us", "male"): "am_michael", ("uk", "female"): "bf_emma",
         ("uk", "male"): "bm_george", ("es", "female"): "ef_dora", ("es", "male"): "em_alex",
         ("fr", "female"): "ff_siwis", ("it", "female"): "if_sara", ("it", "male"): "im_nicola",
         ("pt", "female"): "pf_dora", ("pt", "male"): "pm_alex", ("hi", "female"): "hf_alpha",
         ("hi", "male"): "hm_omega", ("ja", "female"): "jf_alpha", ("ja", "male"): "jm_kumo",
         ("zh", "female"): "zf_xiaoxiao", ("zh", "male"): "zm_yunxi"}
LOCALES = {"us": "us", "american": "us", "en": "us", "english": "us", "uk": "uk", "british": "uk", "gb": "uk",
           "es": "es", "spanish": "es", "fr": "fr", "french": "fr", "it": "it", "italian": "it", "pt": "pt",
           "portuguese": "pt", "br": "pt", "hi": "hi", "hindi": "hi", "ja": "ja", "japanese": "ja",
           "zh": "zh", "chinese": "zh", "mandarin": "zh"}
# first letter of a voice id -> (Kokoro/espeak language, Whisper language)
LANGS = {"a": ("en-us", "en"), "b": ("en-gb", "en"), "e": ("es", "es"), "f": ("fr-fr", "fr"), "h": ("hi", "hi"),
         "i": ("it", "it"), "p": ("pt-br", "pt"), "j": ("ja", "ja"), "z": ("cmn", "zh")}


def voice_id(voice):
    v = voice.strip().lower()
    if re.fullmatch(r"[a-z][fm]_[a-z]+", v):
        return v
    ws = v.replace("-", " ").split()
    gender = "female" if "female" in ws or "woman" in ws else "male"
    loc = next((LOCALES[w] for w in ws if w in LOCALES), "us")
    return NAMED.get((loc, gender)) or NAMED[(loc, "female" if gender == "male" else "male")]


def langs(voice):
    return LANGS.get(voice_id(voice)[0], ("en-us", "en"))


def missing():
    """What the voice still needs on this machine, as a list of strings (empty when ready)."""
    out = []
    for mod in ("kokoro_onnx", "faster_whisper", "soundfile"):
        try:
            __import__(mod)
        except ImportError:
            out.append(f"python package {mod}")
    for f in (MODEL_FILE, VOICES_FILE):
        if not f.exists():
            out.append(str(f))
    return out


_kokoro = None
_whisper = {}


def _tts_model():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(str(MODEL_FILE), str(VOICES_FILE))
    return _kokoro


def tts(text, out, voice="am_michael", speed=1.0):
    """Speak text into the WAV file out (24 kHz mono, 16 bit)."""
    import soundfile as sf
    samples, sr = _tts_model().create(text, voice=voice_id(voice), speed=speed, lang=langs(voice)[0])
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), samples, sr, subtype="PCM_16")
    return out


def asr(wav, voice="am_michael"):
    """(transcript, words): what Whisper hears in wav, and every word with its start and end in seconds."""
    lang = langs(voice)[1]
    name = ASR_MODEL or ("base.en" if lang == "en" else "base")
    if name not in _whisper:
        from faster_whisper import WhisperModel
        _whisper[name] = WhisperModel(name, device="cpu", compute_type="int8")
    segs, _ = _whisper[name].transcribe(str(wav), language=lang, word_timestamps=True, beam_size=5)
    ws = [{"w": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)} for s in segs for w in s.words]
    return " ".join(w["w"] for w in ws), ws


ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
        "seventeen eighteen nineteen").split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def number(n):
    """An integer in words, the way Whisper's digits are read: 23 -> twenty three, 1500 -> one thousand five hundred."""
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    for size, name in ((10**9, "billion"), (10**6, "million"), (1000, "thousand"), (100, "hundred")):
        if n >= size:
            return number(n // size) + " " + name + ("" if n % size == 0 else " " + number(n % size))
    return str(n)


def _spell(m):
    s = m.group().replace(",", "")
    whole, _, frac = s.partition(".")
    out = number(int(whole)) if len(whole) < 13 else " ".join(ONES[int(d)] for d in whole)
    if frac:
        out += " point " + " ".join(ONES[int(d)] for d in frac)
    return f" {out} "


def words(s):
    """Lowercase words with numbers spelled out, so "20" and "twenty" compare equal."""
    s = s.lower().replace("%", " percent ").replace("-", " ").replace("’", "'")
    s = re.sub(r"\d[\d,]*(\.\d+)?", _spell, s)
    return re.findall(r"[a-z\u00c0-\u024f']+", s)


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
    import wave
    with wave.open(str(wav)) as w:
        return w.getnframes() / w.getframerate()


def python():
    """The interpreter of the voice environment, or this one if it already has the packages."""
    try:
        import kokoro_onnx  # noqa: F401
        return sys.executable
    except ImportError:
        exe = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        return str(exe) if exe.exists() else None
