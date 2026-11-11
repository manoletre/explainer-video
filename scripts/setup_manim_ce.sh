#!/usr/bin/env bash
# Set up Manim Community (Cairo, draws on the CPU) in its own environment, $EXPLAINER_HOME/manim-ce.
# It needs Cairo and Pango headers to build, and LaTeX with dvisvgm for formulas:
#   Debian/Ubuntu: sudo apt install libcairo2-dev libpango1.0-dev pkg-config texlive-latex-extra dvisvgm
#   macOS:         brew install cairo pango pkg-config; brew install --cask mactex-no-gui
set -euo pipefail
HOME_DIR="${EXPLAINER_HOME:-$HOME/.cache/explainer-video}"
VENV="$HOME_DIR/manim-ce"
command -v uv >/dev/null || { echo "uv is needed: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2; exit 1; }
[ -x "$VENV/bin/python" ] || uv venv -q --python 3.12 "$VENV"
VIRTUAL_ENV="$VENV" uv pip install -q "manim==0.22.1"
"$VENV/bin/manim" --version
