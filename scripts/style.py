"""The look of every video: PT Serif, high contrast, in the colors of manoletre.com (gold on black),
in a dark or a light theme.

    python3 scripts/style.py              # the default theme and its colors
    python3 scripts/style.py light        # make light the default for every video (dark is the default)
    python3 scripts/style.py --for <dir>/narration.py   # the theme that video uses

The theme of a video is, first match wins: THEME = "light" / "dark" in its narration.py, the
EXPLAINER_THEME environment variable, the default saved by `style.py light|dark` (in
~/.config/explainer-video/config.json), then dark.

In a ManimGX scene:  S = theme(HERE / "narration.py"); m.config.background_color = S.bg; T(..., font=S.font)
Remotion gets it through the timeline (remotion.py writes it into src/timeline.json).
"""
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "explainer-video" / "config.json"
FONT = "PT Serif"
MONO = "JetBrains Mono"

# accent: gold, for fills (highlights, bars, the active box) with on_accent text on it.
# ink: the accent as text or a thin line on the background (gold is unreadable as text on white).
THEMES = {
    "dark": {"bg": "#000000", "fg": "#FFFFFF", "dim": "#B4B4B4", "accent": "#FFD700", "on_accent": "#000000",
             "ink": "#FFD700", "good": "#3DDC84", "bad": "#FF6B5A", "blue": "#4DA3FF", "panel": "#0D0D0D",
             "line": "#FFFFFF", "pointer": "#FF4646"},
    "light": {"bg": "#FFFFFF", "fg": "#000000", "dim": "#4A4A4A", "accent": "#FFD700", "on_accent": "#000000",
              "ink": "#8A6A00", "good": "#0A7D33", "bad": "#C62828", "blue": "#0B57D0", "panel": "#FFFFFF",
              "line": "#000000", "pointer": "#E00000"},
}


def default():
    if os.environ.get("EXPLAINER_THEME") in THEMES:
        return os.environ["EXPLAINER_THEME"]
    try:
        name = json.loads(CONFIG.read_text()).get("theme")
    except (OSError, ValueError):
        name = None
    return name if name in THEMES else "dark"


def name_for(narration=None):
    """The theme name for a video: its narration.py's THEME, else the default."""
    if narration is not None and not hasattr(narration, "LINES"):
        spec = importlib.util.spec_from_file_location("narration", narration)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        narration = mod
    name = getattr(narration, "THEME", None) if narration is not None else None
    if name is not None and name not in THEMES:
        raise SystemExit(f"THEME = {name!r} in narration.py: use one of {', '.join(THEMES)}")
    return name or default()


def palette(narration=None):
    """The theme as a dict: name, colors, font and mono."""
    name = name_for(narration)
    return {"name": name, **THEMES[name], "font": FONT, "mono": MONO}


def theme(narration=None):
    """The theme as attributes, for a ManimGX scene: S.bg, S.fg, S.accent, S.font, ..."""
    return SimpleNamespace(**palette(narration))


def save_default(name):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    try:
        data = json.loads(CONFIG.read_text())
    except (OSError, ValueError):
        pass
    data["theme"] = name
    CONFIG.write_text(json.dumps(data, indent=1) + "\n")


def main():
    args = sys.argv[1:]
    if args and args[0] in THEMES:
        save_default(args[0])
        print(f"default theme: {args[0]} (saved in {CONFIG})")
        return
    p = palette(args[1] if len(args) > 1 and args[0] == "--for" else None)
    print(json.dumps(p, indent=1) if "--json" in args else
          f"theme {p['name']} (default: {default()}); font {p['font']}, mono {p['mono']}\n" +
          "  ".join(f"{k} {v}" for k, v in p.items() if str(v).startswith("#")))


if __name__ == "__main__":
    main()
