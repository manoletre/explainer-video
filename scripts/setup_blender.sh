#!/usr/bin/env bash
# Download Blender 4.2 LTS (about 350 MB) into $EXPLAINER_HOME/blender. On macOS, install Blender.app
# instead (brew install --cask blender); blender.py finds it there.
set -euo pipefail
HOME_DIR="${EXPLAINER_HOME:-$HOME/.cache/explainer-video}"
VER=4.2.23
DEST="$HOME_DIR/blender"
if [ "$(uname)" = Darwin ]; then echo "macOS: brew install --cask blender" >&2; exit 1; fi
case "$(uname -m)" in x86_64) ;; *) echo "Blender publishes Linux builds for x86_64 only" >&2; exit 1 ;; esac
mkdir -p "$DEST"
if [ ! -x "$DEST/blender-$VER-linux-x64/blender" ]; then
  curl -fsSL "https://download.blender.org/release/Blender4.2/blender-$VER-linux-x64.tar.xz" | tar -xJ -C "$DEST"
fi
"$DEST/blender-$VER-linux-x64/blender" --version | head -1
