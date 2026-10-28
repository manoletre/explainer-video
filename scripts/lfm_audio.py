# /// script
# requires-python = ">=3.10"
# dependencies = ["transformers>=5.20.2", "torch", "accelerate", "librosa", "soundfile"]
# ///
"""LFM3-Audio-2B (Hugging Face Transformers) for TTS and ASR.

The model loads once per process, on the Apple GPU (MPS) or CUDA when there is one, else the CPU.
Weights (4 GB) go to the Hugging Face cache on first use; `uv run lfm_audio.py fetch` downloads them ahead.
The words/wer/duration helpers need no torch, so lfm_voice.py can import this module from manimgx.

    uv run lfm_audio.py fetch
    uv run lfm_audio.py best "Text to speak." out.wav "US male"   # best of 3 takes by ASR word error rate
"""
import os
import re
import subprocess
import sys
from functools import cache
from pathlib import Path

MODEL = "LiquidAI/LFM3-Audio-2B"
# the checkpoint ships its own modeling code (trust_remote_code), so pin the revision it was tested with
REVISION = os.environ.get("LFM_AUDIO_REVISION", "9d49701c372d6011d900f6abb40c6b296fb706dd")

# VOICE strings in narration.py, e.g. "US male", "UK female", "es male": a locale and a gender
LANGS = {"us": "American English", "en": "American English", "uk": "British English", "gb": "British English",
         "en-gb": "British English", "ar": "Arabic", "da": "Danish", "de": "German", "el": "Greek",
         "es": "Spanish", "fi": "Finnish", "fr": "French", "he": "Hebrew", "it": "Italian", "ja": "Japanese",
         "ko": "Korean", "nl": "Dutch", "pl": "Polish", "pt": "Portuguese", "sv": "Swedish", "tr": "Turkish",
         "zh": "Chinese"}


def tts_prompt(voice):
    ws = voice.lower().split()
    gender = "female" if "female" in ws else "male"
    rest = [w for w in voice.split() if w.lower() not in ("male", "female", "voice")]
    lang = LANGS.get(rest[0].lower(), " ".join(rest)) if rest else "American English"
    return f"Perform TTS in {lang} using a {gender} voice."


@cache
def _load():
    import torch
    from transformers import AutoModelForMultimodalLM, AutoProcessor

    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float32 if device == "cpu" else torch.bfloat16
    model = AutoModelForMultimodalLM.from_pretrained(MODEL, revision=REVISION, dtype=dtype, device_map=device,
                                                     trust_remote_code=True).eval()
    processor = AutoProcessor.from_pretrained(MODEL, revision=REVISION, trust_remote_code=True)
    codec = processor.audio_tokenizer.to(device=device).eval()
    return model, processor, codec, device


def tts(text, out, voice="US male"):
    import soundfile as sf
    import torch

    model, processor, codec, device = _load()
    conv = [{"role": "system", "content": tts_prompt(voice)},
            {"role": "user", "content": text},
            {"role": "assistant", "content": "<|audio_start|>"}]
    inputs = processor.apply_chat_template(conv, continue_final_message=True, tokenize=True, return_dict=True,
                                           return_tensors="pt").to(device)
    with torch.no_grad():  # audio sampling settings from the model card
        o = model.generate(**inputs, max_new_tokens=4096, audio_temperature=1.0, audio_top_k=128,
                           audio_repetition_penalty=1.1, audio_repetition_window=4096, return_dict_in_generate=True)
        wav = codec.decode(o.audio_codes[:1, :, :o.audio_lengths[0]]).audio_values[0]
    out = Path(out)
    sf.write(out, wav.float().cpu().numpy().squeeze(), 24_000)
    return out


def asr(wav, language="English"):
    import torch

    model, processor, codec, device = _load()
    conv = [{"role": "system", "content": f"Perform ASR in {language}."},
            {"role": "user", "content": [{"type": "audio", "audio": str(wav)}]}]
    inputs = processor.apply_chat_template(conv, add_generation_prompt=True, tokenize=True, return_dict=True,
                                           return_tensors="pt").to(device)
    with torch.no_grad():
        o = model.generate(**inputs, max_new_tokens=1024, suppress_mixed=True, suppress_audio_out=True,
                           return_dict_in_generate=True)
    return processor.decode(o.sequences[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()


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


if __name__ == "__main__":
    if sys.argv[1:2] == ["fetch"]:
        _load()
        print(f"{MODEL} ready")
    elif sys.argv[1:2] == ["best"]:
        print(best(sys.argv[2], sys.argv[3], *sys.argv[4:5]))
    else:
        sys.exit(__doc__)
