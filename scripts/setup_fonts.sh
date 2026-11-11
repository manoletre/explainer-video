#!/usr/bin/env bash
# Install the videos' fonts for ManimGX, which draws with the system's fonts: PT Serif (text) and
# JetBrains Mono (code), both from Google Fonts (SIL Open Font License). Remotion videos don't need
# this: they bundle the fonts from npm.
set -euo pipefail
if [ "$(uname)" = Darwin ]; then DEST="$HOME/Library/Fonts"; else DEST="${XDG_DATA_HOME:-$HOME/.local/share}/fonts"; fi
mkdir -p "$DEST"
BASE=https://github.com/google/fonts/raw/main/ofl
for f in ptserif/PT_Serif-Web-Regular.ttf ptserif/PT_Serif-Web-Bold.ttf ptserif/PT_Serif-Web-Italic.ttf \
         ptserif/PT_Serif-Web-BoldItalic.ttf "jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf"; do
  name=$(basename "$f" | sed 's/%5B/[/; s/%5D/]/')
  [ -s "$DEST/$name" ] || curl -fsSL --retry 3 -o "$DEST/$name" "$BASE/$f"
done
command -v fc-cache >/dev/null && fc-cache -f "$DEST" >/dev/null
echo "fonts in $DEST: PT Serif, JetBrains Mono"
