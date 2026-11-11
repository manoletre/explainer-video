"""The Kokoro narration as a ManimGX voice: `class MyScene(m.Scene): voice = staticmethod(kokoro_voice(script))`.

Lines made by make_narration.py are reused from the script's audio/ folder. A line without a clip
is spoken by running make_narration.py for it in the voice environment (ManimGX's own Python doesn't
have Kokoro).
"""
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import manimgx as m

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import voice as V  # noqa: E402


def plain(line):
    """The words as spoken: without say()'s [brackets]."""
    return re.sub(r"\s+", " ", line.replace("[", "").replace("]", "")).strip()


def load_script(path):
    spec = importlib.util.spec_from_file_location("narration", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def kokoro_voice(script_path):
    script_path = Path(script_path).resolve()
    mod = load_script(script_path)
    keys = {plain(t): k for k, t in mod.LINES.items()}
    audio = script_path.parent / "audio"

    def speak(text):
        key = keys.get(plain(text))
        if key is None:
            raise KeyError(f"not a line of {script_path.name}: {plain(text)[:60]!r}. Add it to LINES.")
        wav = audio / f"{key}.wav"
        if not wav.exists():
            py = V.python()
            if py is None:
                sys.exit(f"The voice is not set up: run {HERE / 'setup_voice.sh'}")
            subprocess.run([py, str(HERE / "make_narration.py"), str(script_path), key], check=True)
        return m.Speech(wav.read_bytes(), text=text)

    speak.__qualname__ = f"kokoro_voice[{V.voice_id(getattr(mod, 'VOICE', 'am_michael'))}]"
    return speak
