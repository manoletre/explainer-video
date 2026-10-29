"""LFM3-Audio as a ManimGX voice: `class MyScene(m.Scene): voice = staticmethod(lfm_voice(script))`.

A line already generated (and ASR-checked) by make_narration.py is reused from the script's audio/ folder;
any other text is spoken here, best of three takes by ASR word error rate.
"""
import importlib.util
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import lfm_audio as L  # noqa: E402

import manimgx as m  # noqa: E402


def plain(line):
    """The words as spoken: without say()'s [brackets]."""
    return re.sub(r"\s+", " ", line.replace("[", "").replace("]", "")).strip()


def load_script(path):
    spec = importlib.util.spec_from_file_location("narration", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def lfm_voice(script_path):
    script_path = Path(script_path)
    mod = load_script(script_path)
    clips = {plain(t): script_path.parent / "audio" / f"{k}.wav" for k, t in mod.LINES.items()}

    def speak(text):
        wav = clips.get(plain(text))
        if wav is None or not wav.exists():
            wav = Path(tempfile.mkdtemp()) / "line.wav"
            L.best(plain(text), wav, mod.VOICE)
        return m.Speech(wav.read_bytes(), text=text)

    speak.__qualname__ = f"lfm_voice[{mod.VOICE}]"
    return speak
