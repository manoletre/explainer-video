---
name: explainer-video
description: Make a narrated explainer video (MP4) about a paper, method or concept, animated with ManimGX and voiced locally by LFM3-Audio, optionally tied to the user's own project. Use whenever the user asks for an animation, an animated explainer, or an explainer video.
---

# Narrated explainer videos

The reference is `examples/sec/` in this skill: a 3Blue1Brown-style explainer of the
Self-Evolving Curriculum paper. Match it: dark background, one idea per beat,
every animation timed to the words that describe it, the real math built up one piece at a time,
and, when the user has a project the idea relates to, a closing part about how it applies there.

Tools (see README.md for setup; if one is missing, tell the user how to install it):
- `manimgx` (`uv tool install manimgx`; CLI, Manim CE API, `import manimgx as m`): `inspect` for storyboard and layout report, `render` for the MP4 and its `.srt`.
- LFM3-Audio-2B GGUF for TTS and ASR, in `$LFM_AUDIO_CKPT` (default
  `~/.lmstudio/models/LiquidAI/LFM3-Audio-2B-GGUF/`), run with llama.cpp's `llama-tts` and
  `llama-mtmd-cli` from `runner/b11985/` there. `scripts/fetch_model.sh` downloads both.
- `ffmpeg`/`ffprobe`.
- Helpers in this skill's `scripts/`: `lfm_audio.py` (TTS, ASR, word error rate), `make_narration.py`
  (each line spoken up to 3 times, the take whose transcript is closest wins), `lfm_voice.py`
  (the scene's `voice`, reuses those clips), `stage.py` (a laser `Pointer` the narration can move, and
  `say_synced`, which flags speech over an empty or frozen screen). `examples/sec/sec_explainer.py` +
  `examples/sec/narration.py` are a full video: copy its helpers (`T`, `M`, `card`, `header`, `beat`,
  `clear_all`) and idioms.

## The screen leads the voice

The viewer must always be able to see what the narrator is talking about. Two failures to avoid:
- **Dead air**: talking over an empty screen. It happens after `header()` or a fade-out, when the first
  `[bracket]` comes late in the line ("Math piece three, from the appendix. Suppose [...]"): every word
  before it plays over black. A beat that starts on a cleared screen brackets its opening words, so
  something appears as the voice starts.
- **Frozen screen**: talking for more than about 4 seconds while nothing moves, so the viewer loses
  which part of the picture the words are about. Every sentence gets an animation, and when the words
  refer to something already on screen, point at it: `self.ptr.at(x)` (flies there and pulses),
  `self.ptr.sweep(x)` (underlines it as it is read), `self.ptr.circle(x)`, `self.ptr.hide()`.
  `m.Indicate(x)` works too.

Silence is fine: after a line, a pause that lets a point land (an `Indicate` or a pointer pulse, then a
second or two of nothing) is good pacing. The rule is about speech, not about silence.

## Steps

1. **Research first.** Read the paper or source and, when the video is about the user's project,
   the project's README, docs and notes. Get the numbers right; never invent a result. Write
   `<slug>_cheatsheet.md` with the formulas, numbers and sources. It ships with the video.
2. **Outline 8–13 numbered sections**, about 6–10 minutes total: intro with a roadmap, the problem,
   the idea, the math one piece at a time, worked numeric examples, results, and then (if there is
   a project) "how this applies to <project>" with concrete steps, then a summary or questions.
   For the project part, use real names, files, numbers and known findings from the project.
3. **Write `narration.py`**: `VOICE = "US male"` (or `"UK female"`, `"es male"`: a locale and male/female) and `LINES = {key: text}`, one line per beat
   (2–5 sentences). Spoken form, not screen form: "L L M", "G R P O", "two point six B",
   "zero point four three", no symbols, no CamelCase, no code identifiers. Wrap in `[brackets]`
   the words each animation should play on; brackets are stripped before speaking.
4. **Write the scene** `<slug>.py` beside it:
   ```python
   sys.path.insert(0, "<this skill>/scripts"); from lfm_voice import load_script, lfm_voice
   N = load_script(HERE / "narration.py").LINES
   class XExplainer(m.Scene):
       voice = staticmethod(lfm_voice(HERE / "narration.py"))
   ```
   In `construct()`, create `self.ptr = Pointer()` (from `stage`). Each beat is
   `say_synced(self, key, N[key], *anims)` (the example's `beat`) with exactly one animation per
   bracketed span (wrap several in `m.AnimationGroup`); a pointer gesture is an animation like any
   other, so "the [denominator] is the spread" plays `self.ptr.at(frac[2])` on "denominator".
   Sections start with `header("3 · Title")`, which clears the screen (and hides the pointer) and
   marks the title with `chrome()` so it doesn't count as content. For an emphasis pause, use
   `hold(self, m.Indicate(x))` from `stage`. Style: background `#111111`, text `#FFFFFF`, dim `#9A9A9A`, accent `#FF8700`,
   good `#5FD787`, bad `#FF5F5F`, blue `#5FAFFF`, panels `#1C1C1C`, font "Avenir Next"
   (or another installed sans), formulas with `m.MathTex`. Prefer diagrams, bars, dots, flows and
   transforms to walls of text; on-screen text is short and complements the narration rather than
   repeating it. Label toy simulations and illustrative shapes as such on screen.
5. **Generate the voice**: `python3 <skill>/scripts/make_narration.py <dir>/narration.py`
   (run in the background; about 7 s per take, up to 3 takes per line). Read `audio/report.json`; rewrite any line
   flagged `<-- check` (word error rate > 0.15) in plainer spoken words and redo it with
   `make_narration.py <dir>/narration.py key1 key2`. Number-heavy lines get false flags (the transcript writes
   "150" for "a hundred and fifty"), so read the transcript before redoing.
6. **Inspect and fix layout and sync**: `manimgx inspect <slug>.py` writes storyboard PNGs and a layout
   report (overlaps, text off screen), and `say_synced` writes `sync_report.txt` beside the scene. Look
   at every storyboard PNG, fix overlaps, crowding, tiny text and off-frame items. Fix every
   `sync_report.txt` entry: for **dead air**, move the first bracket onto the opening words (or show
   the picture before the line starts); for **still**, add a bracket on the words it quotes, with a
   pointer gesture or the reveal of what they describe. Moving or adding brackets doesn't change
   what is spoken, so the clips don't need redoing. Inspect again until both reports are clean
   (a layout flag on `self.ptr` while it is flying between targets is fine; one where it rests is not:
   point at another `edge`).
   `manimgx inspect <slug>.py -t 12.5,end` checks particular moments.
7. **Render**: `manimgx render <slug>.py` (background). Check the result: duration with
   `ffprobe`, a few frames (`ffmpeg -ss T -i X.mp4 -frames:v 1 f.png`) and the `.srt`.
8. **Deliver** the MP4 plus the cheat sheet, with the length and a one-paragraph summary of the
   argument. Keep files in `explainers/<slug>/` inside the project (`audio/` holds the clips).
   Don't commit the MP4 or audio unless asked.

## Quality bar

- Every claim either comes from the source, is computed on screen, or is marked as an assumption.
- One concept per beat, built up visually; transforms connect a step to the next.
- Worked examples with real numbers (as in the SEC advantage example: 2 of 8 correct → mean 0.25 → std 0.433 → ±Â).
- No speech over an empty screen and no more than about 4 s of speech with nothing moving
  (`sync_report.txt` is empty); deliberate silent pauses for emphasis are fine.
- No rushed beats: an animation can't outrun its words, so long animations need long spans.
- The project section names the real files, scores and constraints, and gives an ordered plan.
