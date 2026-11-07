"""What this machine can do for an explainer video, and how to set the skill up for it.

    python3 scripts/hardware.py           # a summary, with what to fix or change
    python3 scripts/hardware.py --json    # the same as JSON

ManimGX draws every frame with the GPU through wgpu (Vulkan on Linux, Metal on macOS). With no GPU
it can use Mesa's lavapipe, which draws on the CPU: it works, but each changed frame costs about
0.15 s at 1280x720 and 0.3 s at 1920x1080 on 8 cores, so a 1080p60 render of an 8 minute video
takes hours. scripts/render.py measures the real cost and picks a resolution and frame rate that
finish in time. LFM3-Audio (llama.cpp) runs fine on the CPU: about 8 s per take on 8 cores.
"""
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

CKPT = Path(os.environ.get("LFM_AUDIO_CKPT", Path.home() / ".lmstudio/models/LiquidAI/LFM3-Audio-2B-GGUF"))
QUANT = os.environ.get("LFM_AUDIO_QUANT", "Q8_0")
BUILD = os.environ.get("LFM_LLAMA_BUILD", "b11985")
FLAVOR = os.environ.get("LFM_LLAMA_FLAVOR", "")
RUNNER = Path(os.environ.get("LFM_AUDIO_RUNNER", CKPT / f"runner/{BUILD}{'-' + FLAVOR if FLAVOR else ''}"))

# the least the whole pipeline needs, and what makes it comfortable
MIN = {"cores": 4, "ram_gb": 6, "disk_gb": 4}
GOOD = {"cores": 8, "ram_gb": 16}
GPU_TYPES = {"DiscreteGpu", "IntegratedGpu", "VirtualGpu"}


def _run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout, errors="replace")
        return r.returncode, r.stdout, r.stderr
    except (OSError, subprocess.TimeoutExpired) as e:
        return -1, "", str(e)


def manimgx_python():
    """The interpreter `manimgx` runs in (uv installs it in a venv of its own), or None."""
    exe = shutil.which("manimgx") or str(Path.home() / ".local/bin/manimgx")
    try:
        first = Path(exe).read_text(errors="replace").splitlines()[0]
    except (OSError, IndexError):
        return None
    if first.startswith("#!") and Path(first[2:].strip()).exists():
        return first[2:].strip()
    return None


def _cpu():
    model, flags = platform.processor() or platform.machine(), ""
    if sys.platform == "darwin":
        model = _run(["sysctl", "-n", "machdep.cpu.brand_string"])[1].strip() or model
    else:
        try:
            info = Path("/proc/cpuinfo").read_text()
            model = (re.search(r"model name\s*:\s*(.+)", info) or re.search(r"Model\s*:\s*(.+)", info) or [None, model])[1]
            flags = (re.search(r"^flags\s*:\s*(.+)$", info, re.M) or [None, ""])[1]
        except OSError:
            pass
    cores = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else os.cpu_count() or 1
    return {"model": model.strip(), "cores": cores, "avx2": "avx2" in flags.split() if flags else None}


def _ram_gb():
    if sys.platform == "darwin":
        out = _run(["sysctl", "-n", "hw.memsize"])[1].strip()
        return round(int(out) / 2**30, 1) if out.isdigit() else None
    try:
        total = int(re.search(r"MemTotal:\s*(\d+)", Path("/proc/meminfo").read_text())[1]) * 1024
    except (OSError, TypeError):
        return None
    # a container sees the host's MemTotal but is held to its cgroup's limit (v2, then v1)
    for limit in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        try:
            text = Path(limit).read_text().strip()
        except OSError:
            continue
        if text.isdigit():
            total = min(total, int(text))
        break
    return round(total / 2**30, 1)


def _free_gb(path):
    """Free space where path is, or would be: at its nearest existing parent."""
    path = Path(path).expanduser().resolve()
    while not path.exists() and path != path.parent:
        path = path.parent
    return round(shutil.disk_usage(path).free / 2**30, 1)


def gpu():
    """The adapter ManimGX would draw with: its name, device_type (DiscreteGpu, IntegratedGpu, Cpu,
    ...), backend and driver; or {"error": ...} when there is none or ManimGX is missing."""
    py = manimgx_python()
    if py is None:
        return {"error": "manimgx is not installed (uv tool install manimgx)"}
    code, out, err = _run([py, "-c", "import json, manimgx._engine as e; print(json.dumps(e.adapter_info()))"])
    if code == 0 and out.strip():
        return json.loads(out.strip().splitlines()[-1])
    msg = (err.strip().splitlines() or ["unknown error"])[-1]
    return {"error": msg}


def profile(where="."):
    cpu = _cpu()
    g = gpu()
    return {
        "os": platform.system(), "arch": platform.machine(),
        "apple_silicon": sys.platform == "darwin" and platform.machine() == "arm64",
        "cpu": cpu, "ram_gb": _ram_gb(), "free_disk_gb": min(_free_gb(where), _free_gb(CKPT)),
        "gpu": g,
        "render": "gpu" if g.get("device_type") in GPU_TYPES else "cpu" if g.get("device_type") == "Cpu" else "none",
        "tools": {
            "ffmpeg": bool(shutil.which("ffmpeg")), "manimgx": manimgx_python() is not None,
            "latex": bool(shutil.which("latex") or shutil.which("pdflatex")),
            "lfm_model": (CKPT / f"LFM3-Audio-2B-{QUANT}.gguf").exists(),
            "lfm_projector": (CKPT / "mmproj-LFM3-Audio-2B-Q8_0.gguf").exists(),
            "llama_tts": (RUNNER / "llama-tts").exists(),
            "llama_mtmd": (RUNNER / "llama-mtmd-cli").exists(),
        },
    }


def advice(p):
    """(blocking problems, things to change): what the skill should do on this machine."""
    fix, tune = [], []
    t = p["tools"]
    if not t["manimgx"]:
        fix.append("Install ManimGX: uv tool install manimgx")
    if not t["ffmpeg"]:
        fix.append("Install ffmpeg (brew install ffmpeg / sudo apt install ffmpeg)")
    if not all(t[k] for k in ("lfm_model", "lfm_projector", "llama_tts", "llama_mtmd")):
        fix.append("Fetch the voice: scripts/fetch_model.sh (about 2.2 GB)")
    if p["render"] == "none" and t["manimgx"]:
        if p["os"] == "Linux":
            fix.append("ManimGX finds no GPU adapter. Install Mesa's Vulkan drivers, whose lavapipe draws on the "
                       "CPU: sudo apt install mesa-vulkan-drivers (Fedora: sudo dnf install mesa-vulkan-drivers). "
                       "On a machine with an NVIDIA GPU, install its driver's Vulkan ICD instead.")
        else:
            fix.append(f"ManimGX finds no GPU adapter: {p['gpu'].get('error')}")
    ram, cores, disk = p["ram_gb"] or 0, p["cpu"]["cores"], p["free_disk_gb"]
    if ram < 4:
        fix.append(f"{ram} GB of RAM: the voice model and the renderer need at least 4 GB together (6 GB to be safe)")
    elif ram < MIN["ram_gb"]:
        tune.append(f"{ram} GB of RAM: use the smaller voice model, LFM_AUDIO_QUANT=Q4_K_M scripts/fetch_model.sh, "
                    "and render at 1280x720 or less")
    if disk < MIN["disk_gb"]:
        fix.append(f"{disk} GB free: the model, clips and video need about {MIN['disk_gb']} GB")
    if cores < MIN["cores"]:
        tune.append(f"{cores} CPU cores: each narration take will take 20 s or more; generate it in the background")
    if p["cpu"].get("avx2") is False and p["arch"] in ("x86_64", "AMD64"):
        tune.append("No AVX2: llama.cpp falls back to slower kernels; expect slow narration")
    if p["render"] == "cpu":
        tune.append(f"No GPU: ManimGX draws on the CPU ({p['gpu'].get('name')}). Render with scripts/render.py, "
                    "which benchmarks this machine and picks a resolution and frame rate that finish in budget "
                    "(typically 1280x720 at 30 fps, or 854x480 at 15 fps for a long video on few cores). "
                    "Never run a plain 1920x1080 at 60 fps render here: it runs about 20 times slower than real time.")
    elif p["render"] == "gpu":
        tune.append(f"GPU: {p['gpu'].get('name')} ({p['gpu'].get('backend')}). The default 1920x1080 at 60 fps is fine.")
        if p["os"] == "Linux":
            tune.append("The voice runs on the CPU by default. With an NVIDIA or AMD GPU, LFM_LLAMA_FLAVOR=vulkan "
                        "scripts/fetch_model.sh fetches a llama.cpp build that runs it on the GPU.")
    if not t["latex"]:
        tune.append("No LaTeX: m.MathTex needs it (MacTeX / TeX Live). Use m.Text only, or install it.")
    return fix, tune


def main():
    p = profile()
    fix, tune = advice(p)
    if "--json" in sys.argv:
        print(json.dumps({**p, "fix": fix, "tune": tune}, indent=1))
        return 1 if fix else 0
    g = p["gpu"]
    print(f"OS        {p['os']} {p['arch']}")
    print(f"CPU       {p['cpu']['model']}, {p['cpu']['cores']} cores" + (", AVX2" if p["cpu"].get("avx2") else ""))
    print(f"RAM       {p['ram_gb']} GB    free disk {p['free_disk_gb']} GB")
    print("GPU       " + (f"{g.get('name')} [{g.get('device_type')}, {g.get('backend')}]" if "error" not in g else g["error"][:160]))
    print(f"renders   on the {p['render'].upper()}" if p["render"] != "none" else "renders   NOT POSSIBLE yet")
    print("tools     " + ", ".join(f"{k} {'ok' if v else 'MISSING'}" for k, v in p["tools"].items()))
    for s in fix:
        print(f"FIX   {s}")
    for s in tune:
        print(f"NOTE  {s}")
    return 1 if fix else 0


if __name__ == "__main__":
    sys.exit(main())
