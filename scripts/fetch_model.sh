#!/usr/bin/env bash
# Download LFM3-Audio-2B (Q8_0 GGUF + audio projector) and a llama.cpp release that runs it.
#   scripts/fetch_model.sh            # into ~/.lmstudio/models/LiquidAI/LFM3-Audio-2B-GGUF
#   LFM_AUDIO_CKPT=/some/dir scripts/fetch_model.sh
#   LFM_AUDIO_QUANT=Q4_K_M scripts/fetch_model.sh     # smaller model, for machines with little RAM
#   LFM_LLAMA_FLAVOR=vulkan scripts/fetch_model.sh    # Linux with a GPU: llama.cpp's Vulkan build
set -euo pipefail

DIR="${LFM_AUDIO_CKPT:-$HOME/.lmstudio/models/LiquidAI/LFM3-Audio-2B-GGUF}"
QUANT="${LFM_AUDIO_QUANT:-Q8_0}"
BASE="https://huggingface.co/LiquidAI/LFM3-Audio-2B-GGUF/resolve/main"
# LFM3-Audio needs llama.cpp b11960 (v0.8.0) or newer; b11985 is the release this skill was tested with
LLAMA="${LFM_LLAMA_BUILD:-b11985}"
FLAVOR="${LFM_LLAMA_FLAVOR:-}"  # empty: the CPU build (Metal is built in on macOS)

case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) PLAT=macos-arm64 ;;
  Darwin-x86_64) PLAT=macos-x64 ;;
  Linux-x86_64) PLAT=ubuntu${FLAVOR:+-$FLAVOR}-x64 ;;
  Linux-aarch64) PLAT=ubuntu${FLAVOR:+-$FLAVOR}-arm64 ;;
  *) echo "No llama.cpp build for $(uname -s) $(uname -m)" >&2; exit 1 ;;
esac

mkdir -p "$DIR/runner"
for f in "LFM3-Audio-2B-$QUANT.gguf" "mmproj-LFM3-Audio-2B-Q8_0.gguf"; do
  [ -f "$DIR/$f" ] || curl -L --fail -o "$DIR/$f" "$BASE/$f"
done

TAR="llama-$LLAMA-bin-$PLAT.tar.gz"
RUN="$DIR/runner/$LLAMA${FLAVOR:+-$FLAVOR}"
if [ ! -x "$RUN/llama-tts" ]; then
  curl -L --fail -o "$DIR/$TAR" "https://github.com/ggml-org/llama.cpp/releases/download/$LLAMA/$TAR"
  rm -rf "$RUN" && mkdir -p "$RUN"
  tar -xzf "$DIR/$TAR" -C "$RUN" --strip-components=1
  rm "$DIR/$TAR"
fi
echo "LFM3-Audio ready in $DIR (llama.cpp $LLAMA${FLAVOR:+ $FLAVOR}, $QUANT)"
