#!/usr/bin/env bash
# Set up the narration voice: a Python environment with Kokoro (TTS) and faster-whisper (ASR), and
# Kokoro's model files. About 1 GB on disk, in $EXPLAINER_HOME (default ~/.cache/explainer-video).
#   scripts/setup_voice.sh                    # the full model (325 MB)
#   KOKORO_MODEL=int8 scripts/setup_voice.sh  # the 92 MB model, for machines with under 2 GB of RAM
# Running it again only fetches what is missing.
set -euo pipefail
HOME_DIR="${EXPLAINER_HOME:-$HOME/.cache/explainer-video}"
VENV="$HOME_DIR/venv"
MODELS="$HOME_DIR/kokoro"
URL=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
if [ "${KOKORO_MODEL:-fp32}" = int8 ]; then MODEL=kokoro-v1.0.int8.onnx; else MODEL=kokoro-v1.0.onnx; fi
mkdir -p "$MODELS"

if ! command -v uv >/dev/null; then
  echo "uv is needed (https://docs.astral.sh/uv/): curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi
[ -x "$VENV/bin/python" ] || uv venv -q --python 3.12 "$VENV"
VIRTUAL_ENV="$VENV" uv pip install -q "kokoro-onnx==0.6.1" "soundfile==0.14.0" "faster-whisper==1.2.1" "av==16.1.0"

for f in "$MODEL" voices-v1.0.bin; do
  if [ ! -s "$MODELS/$f" ]; then
    echo "downloading $f"
    curl -fL --retry 3 -o "$MODELS/$f.part" "$URL/$f" && mv "$MODELS/$f.part" "$MODELS/$f"
  fi
done

# speak a sentence and hear it back (this also downloads Whisper's model, about 150 MB)
cd "$(dirname "$0")"
"$VENV/bin/python" - <<'PY'
import tempfile, time
from pathlib import Path
import voice as V
out = Path(tempfile.mkdtemp()) / "hello.wav"
t = time.time(); V.tts("Hello from explainer video.", out, "am_michael"); took = time.time() - t
text, _ = V.asr(out)
print(f"voice ok: spoke {V.duration(out):.1f} s of audio in {took:.1f} s; heard: {text}")
PY
