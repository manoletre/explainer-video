# explainer-video

A [Claude Code](https://claude.com/claude-code) skill for narrated explainer videos.
Ask Claude for "an animated explainer of this paper". It researches the source, writes
a narration script, animates it with [ManimGX](https://pypi.org/project/manimgx/), and voices it
locally with [LFM3-Audio](https://huggingface.co/LiquidAI/LFM3-Audio-2B). Every
animation is timed to the words that describe it. The result is an MP4 with subtitles plus a
cheat sheet of the formulas and sources.

Narration runs fully offline. The skill speaks each line up to three times, transcribes every
take back with the same model, and keeps the take closest to the script. Lines that still
come out wrong get flagged for a rewrite.

## Examples

Click a thumbnail to watch the video. Both were made with this skill, and each ends with a section
on how the idea applies to a chess-playing LLM project.

| [![DAgger explainer](docs/dagger.jpg)](https://github.com/manoletre/explainer-video/releases/download/v0.1.0/DAggerExplainer.mp4) | [![SEC explainer](docs/sec.jpg)](https://github.com/manoletre/explainer-video/releases/download/v0.1.0/SECExplainer.mp4) |
|---|---|
| **[DAgger: imitation learning that doesn't drift](https://github.com/manoletre/explainer-video/releases/download/v0.1.0/DAggerExplainer.mp4)** (7:33)<br>Ross, Gordon & Bagnell, AISTATS 2011 | **[Self-Evolving Curriculum for LLM reasoning](https://github.com/manoletre/explainer-video/releases/download/v0.1.0/SECExplainer.mp4)** (11:02)<br>Chen et al., 2025. Source in [`examples/sec/`](examples/sec/) |

## Install

```bash
git clone https://github.com/manoletre/explainer-video ~/.claude/skills/explainer-video
```

```bash
uv tool install manimgx
```

```bash
uv run ~/.claude/skills/explainer-video/scripts/lfm_audio.py fetch
```

You also need `ffmpeg` and a LaTeX install for `MathTex` (for example `brew install ffmpeg` and
MacTeX/BasicTeX on macOS), plus [uv](https://docs.astral.sh/uv/). The voice runs on Hugging Face
Transformers: `uv run` sets up torch and transformers for the scripts, and `fetch` downloads the 4 GB
model into the Hugging Face cache (otherwise it downloads on first use). It runs on the Apple GPU,
CUDA or the CPU. On an M-series Mac it speaks about as fast as real time.

## Use

In Claude Code:

> Make an explainer video of arXiv 2505.14970 and how it applies to this project.

The skill (`SKILL.md`) walks Claude through research, outline, narration, voice generation,
layout inspection and render.

## What's inside

- `SKILL.md`: the instructions Claude follows.
- `scripts/lfm_audio.py`: TTS, ASR and word error rate with LFM3-Audio-2B on Transformers.
- `scripts/make_narration.py`: generates and checks every narration clip; writes `audio/report.json`.
- `scripts/lfm_voice.py`: plugs those clips into a ManimGX scene as its `voice`.
- `examples/sec/`: a complete 11 minute video explaining *Self-Evolving Curriculum for LLM
  Reasoning* (Chen et al., 2025). Run it yourself:

  ```bash
  cd ~/.claude/skills/explainer-video && uv run scripts/make_narration.py examples/sec/narration.py && manimgx render examples/sec/sec_explainer.py
  ```

## License

MIT
