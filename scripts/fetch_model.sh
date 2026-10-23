#!/usr/bin/env bash
# Download LFM2.5-Audio-1.5B (Q8_0 GGUFs) and this platform's runner from Hugging Face.
#   scripts/fetch_model.sh            # into ~/.lmstudio/models/LiquidAI/LFM2.5-Audio-1.5B-GGUF
#   LFM_AUDIO_CKPT=/some/dir scripts/fetch_model.sh
set -euo pipefail

DIR="${LFM_AUDIO_CKPT:-$HOME/.lmstudio/models/LiquidAI/LFM2.5-Audio-1.5B-GGUF}"
QUANT="${LFM_AUDIO_QUANT:-Q8_0}"
BASE="https://huggingface.co/LiquidAI/LFM2.5-Audio-1.5B-GGUF/resolve/main"

case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) PLAT=macos-arm64 ;;
  Linux-x86_64) PLAT=ubuntu-x64 ;;
  Linux-aarch64) PLAT=ubuntu-arm64 ;;
  *) echo "No LFM audio runner for $(uname -s) $(uname -m)" >&2; exit 1 ;;
esac

mkdir -p "$DIR/runner"
for f in "LFM2.5-Audio-1.5B-$QUANT.gguf" "mmproj-LFM2.5-Audio-1.5B-F16.gguf" \
         "vocoder-LFM2.5-Audio-1.5B-$QUANT.gguf" "tokenizer-LFM2.5-Audio-1.5B-$QUANT.gguf"; do
  [ -f "$DIR/$f" ] || curl -L --fail -o "$DIR/$f" "$BASE/$f"
done

ZIP="llama-liquid-audio-$PLAT.zip"
[ -f "$DIR/$ZIP" ] || curl -L --fail -o "$DIR/$ZIP" "$BASE/runners/$ZIP"
unzip -oq "$DIR/$ZIP" -d "$DIR/runner"
chmod +x "$DIR"/runner/*/llama-liquid-audio-cli 2>/dev/null || true
echo "LFM2.5-Audio ready in $DIR"
