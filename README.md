# explainer-video

<p align="center">
  <img src="assets/logo.png" alt="Explainer Video logo: a white integral sign beside a yellow play button" width="240">
</p>

A [Claude Code](https://claude.com/claude-code) skill for narrated explainer videos.
Ask Claude for "an animated explainer of this paper". It researches the source, writes
a narration script, animates it with [ManimGX](https://pypi.org/project/manimgx/), and voices it
locally with [LFM3-Audio](https://huggingface.co/LiquidAI/LFM3-Audio-2B-GGUF) on llama.cpp. Every
animation is timed to the words that describe it. The result is an MP4 with subtitles plus a
cheat sheet of the formulas and sources.

Narration runs fully offline. The skill speaks each line up to three times, transcribes every
take back with the same model, and keeps the take closest to the script. Lines that still
come out wrong get flagged for a rewrite.

## Examples

| [![Search algorithms explainer](docs/search.jpg)](https://github.com/manoletre/explainer-video/releases/download/v0.1.0/SearchAlgorithms.mp4) | [![Data structures explainer](docs/data-structures.jpg)](https://github.com/manoletre/explainer-video/releases/download/v0.1.0/DataStructures.mp4) |
|---|---|
| **[Search algorithms, compared](https://github.com/manoletre/explainer-video/releases/download/v0.1.0/SearchAlgorithms.mp4)** (7:58)<br>Linear, binary, jump, exponential, interpolation and hash table lookup: how each one works, what it costs, and when to pick it. Source and cheat sheet in [`examples/search-algorithms/`](examples/search-algorithms/). | **[Must-know data structures](https://github.com/manoletre/explainer-video/releases/download/v0.1.0/DataStructures.mp4)** (10:00)<br>Arrays, linked lists, stacks and queues, hash tables, binary search trees, heaps, graphs and tries: how each is laid out, what it costs, and how to choose. Source and cheat sheet in [`examples/data-structures/`](examples/data-structures/). |

Both were made from a one-line request, for interview prep.

## Install

You need macOS (Apple silicon or Intel) or Linux (x64 or arm64), [Claude Code](https://claude.com/claude-code),
Python 3.9 or newer, and about 3 GB of free disk space. Setup takes about 10 minutes, most of it
downloading the voice model.

### Hardware

| | Minimum | Comfortable |
|---|---|---|
| CPU | 4 cores (x64 with AVX2, or arm64) | 8 cores or Apple silicon |
| RAM | 6 GB (4 GB with the `Q4_K_M` voice model) | 16 GB |
| Disk | 4 GB free | 10 GB free |
| GPU | none: Mesa's lavapipe draws on the CPU, at 720p30 or less | any GPU with Metal or Vulkan, for 1080p60 |

The voice runs on the CPU everywhere (about 8 s per take on 8 cores). Rendering is what needs a GPU:
[ManimGX](https://pypi.org/project/manimgx/) draws every frame through wgpu (Metal on macOS, Vulkan on
Linux). On a Linux box with no GPU driver (most cloud VMs and containers) it fails with `no GPU adapter`
until you install Mesa's Vulkan drivers (`sudo apt install mesa-vulkan-drivers`); it then draws on the
CPU, about 0.15 s per changed frame at 1280x720 and 0.3 s at 1920x1080 on 8 x64 cores. That is fine
at 720p30, but the scene's default 1920x1080 at 60 fps renders about 20 times slower than real time:
hours for an 8 minute video. `scripts/render.py` measures this on your machine and picks the format
that finishes in time; `scripts/hardware.py` tells you which case you are in and what to fix.

On the CPU, lavapipe's worker threads and ManimGX's (rayon) race, so frames come out garbled at random:
black patches over text, boxes missing, different on every run. `render.py` therefore pins both to one
thread (`LP_NUM_THREADS=1 RAYON_NUM_THREADS=1`), which draws every frame right but about 4.5 times
slower per process, and renders the video as one segment per core in parallel, split so each draws as
many changing frames, then joins them without re-encoding and adds the sound and subtitles.

For example, the 8 minute awordaday explainer on an 8 vCPU cloud VM with no GPU (7 parallel segments):
1920x1080 at 30 fps took 41 minutes and 854x480 at 15 fps took 6; 1080p60 would take well over an hour.
The same video renders in about 10 minutes on a MacBook's GPU. So `render.py` defaults to a 10 minute
budget, which on such a VM means about 960x540, and its plan lists what better formats would cost
(`--budget` raises the limit). For full quality without a local GPU, render on any machine that has
one: a small rented cloud GPU (a T4, or a consumer card) is plenty, as long as Vulkan sees it
(`vulkaninfo --summary` lists the GPU, not only llvmpipe).

### 1. Install ffmpeg and uv

[uv](https://docs.astral.sh/uv/) installs ManimGX; ffmpeg muxes the audio and video.

On macOS, with [Homebrew](https://brew.sh):

```bash
brew install ffmpeg uv
```

On Debian or Ubuntu:

```bash
sudo apt install ffmpeg python3 curl
```

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone the skill into Claude Code's skills folder

Claude Code finds skills in `~/.claude/skills/`, so clone it there:

```bash
git clone https://github.com/manoletre/explainer-video ~/.claude/skills/explainer-video
```

### 3. Install ManimGX

```bash
uv tool install manimgx
```

Check that it's on your `PATH`:

```bash
manimgx --version
```

If the shell says `command not found`, run `uv tool update-shell`, open a new terminal, and check again.

### 4. Download the voice model and llama.cpp

```bash
~/.claude/skills/explainer-video/scripts/fetch_model.sh
```

This downloads LFM3-Audio-2B (Q8_0 GGUF plus its audio projector, about 2.2 GB) and a prebuilt
llama.cpp release (`b11985`) for your platform into `~/.lmstudio/models/LiquidAI/LFM3-Audio-2B-GGUF/`.
That's also where LM Studio keeps the model, so an existing LM Studio download is reused. Running the
script again skips whatever is already there.

### 5. Check the hardware

```bash
python3 ~/.claude/skills/explainer-video/scripts/hardware.py
```

It prints the CPU, RAM, disk and the adapter ManimGX will draw with, then a `FIX` line for anything
that would stop a video (on a Linux VM with no GPU: `sudo apt install mesa-vulkan-drivers`) and a
`NOTE` for what to change on this machine.

### 6. Check the voice

```bash
cd ~/.claude/skills/explainer-video && python3 -c "import sys; sys.path.insert(0, 'scripts'); import lfm_audio as L; L.tts('Hello from explainer video.', '/tmp/hello.wav'); print(L.asr('/tmp/hello.wav'))"
```

It speaks the sentence into `/tmp/hello.wav`, transcribes it back, and prints
`Hello from Explainer Video.` (about 7 s on an M-series Mac). Play the file to hear the voice.

### 7. Start Claude Code

Open a new Claude Code session (skills load at startup) and ask for a video, or type `/explainer-video`.

### Optional: LaTeX

Scenes that typeset formulas with `m.MathTex` need a LaTeX install: MacTeX on macOS
(`brew install --cask mactex-no-gui`) or TeX Live on Linux. Scenes that use only `m.Text`, like
the search algorithms example, don't.

### Settings

All optional, set as environment variables before running Claude Code or the scripts:

| Variable | Default | What it changes |
|---|---|---|
| `LFM_AUDIO_CKPT` | `~/.lmstudio/models/LiquidAI/LFM3-Audio-2B-GGUF` | Where the model and llama.cpp live |
| `LFM_LLAMA_BUILD` | `b11985` | llama.cpp release to download and run (LFM3-Audio needs `b11960` or newer) |
| `LFM_AUDIO_RUNNER` | `$LFM_AUDIO_CKPT/runner/$LFM_LLAMA_BUILD` | A folder with your own `llama-tts` and `llama-mtmd-cli` |
| `LFM_AUDIO_QUANT` | `Q8_0` | Model quantization to download and use |
| `LFM_LLAMA_FLAVOR` | (CPU build) | `vulkan` fetches and uses llama.cpp's Vulkan build on Linux, to voice on a GPU |

On an M-series Mac a line of narration takes about 3.5 s to speak and 3.5 s to check.

## Use

In Claude Code:

> Make an explainer video of arXiv 2505.14970 and how it applies to this project.

The skill (`SKILL.md`) walks Claude through research, outline, narration, voice generation,
layout inspection and render. An 8 minute video takes about half an hour end to end.

To rebuild an example yourself, voice it and then render it:

```bash
cd ~/.claude/skills/explainer-video && python3 scripts/make_narration.py examples/search-algorithms/narration.py
```

```bash
cd ~/.claude/skills/explainer-video && python3 scripts/render.py examples/search-algorithms/search_algorithms.py
```

`render.py` prints its plan (for example `plan: 1280x720 at 30 fps, about 25 min` on a CPU-only
VM), then progress every 20 s. On a machine with a GPU, `manimgx render <scene>.py` works as well.

The MP4 and its `.srt` subtitles are written next to the scene file.

## What's inside

- `SKILL.md`: the instructions Claude follows.
- `scripts/lfm_audio.py`: TTS, ASR and word error rate on top of llama.cpp's `llama-tts` and `llama-mtmd-cli`.
- `scripts/make_narration.py`: generates and checks every narration clip; writes `audio/report.json`.
- `scripts/lfm_voice.py`: plugs those clips into a ManimGX scene as its `voice`.
- `scripts/stage.py`: a laser pointer the narration can move, and a check that flags speech over an empty or frozen screen.
- `scripts/fetch_model.sh`: downloads the model and a llama.cpp release that runs it.
- `scripts/hardware.py`: what this machine can render on (GPU or CPU), and what to fix first.
- `scripts/render.py`: renders at the best resolution and frame rate that finish within a time budget, with progress.
- `examples/search-algorithms/`: the 8 minute search algorithms video: scene, narration and cheat sheet.
- `examples/data-structures/`: the 10 minute data structures video: scene, narration and cheat sheet.
- `examples/sec/`: an 11 minute video explaining *Self-Evolving Curriculum for LLM Reasoning*
  (Chen et al., 2025).

## License

MIT
