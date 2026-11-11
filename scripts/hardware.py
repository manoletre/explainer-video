"""What this machine can do for an explainer video: which frameworks and the voice run here, and how fast.

    python3 scripts/hardware.py                  # a summary, with FIX and NOTE lines
    python3 scripts/hardware.py --for remotion   # only what that framework and the voice need
    python3 scripts/hardware.py --json           # the same as JSON
    python3 scripts/hardware.py --no-probe       # skip the few seconds of voice speed test

Remotion draws frames in headless Chrome on the CPU: an 8 minute 1080p30 video takes about 5 minutes
on 8 cores, and it needs no GPU. ManimGX draws with the GPU through wgpu (Metal on macOS, Vulkan on
Linux); without one it can use Mesa's lavapipe on the CPU, which works but is slow (the same video:
41 minutes at 1080p30, about 9 at 960x540, on 8 cores), so scripts/render.py measures the real cost
and picks a format that finishes in time. Kokoro, the voice, runs on the CPU: about 4 times faster
than real time on 8 cores and about real time on one, in under 700 MB of RAM.
pick.py uses this to choose the framework for a video.
"""
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import voice as V  # noqa: E402

GPU_TYPES = {"DiscreteGpu", "IntegratedGpu", "VirtualGpu"}
NODE_MIN = 18
FEEDBACK = "hi@manoletre.com"
# measured on an 8 vCPU cloud VM with no GPU, for an 8 minute video
REMOTION_MIN_8CORES = 5  # 1920x1080 at 30 fps
MANIMGX_CPU_MIN_8CORES = {"1920x1080 at 30 fps": 41, "960x540 at 24 fps": 9}


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
    except (OSError, IndexError, UnicodeDecodeError):
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


def gpu_hint():
    """A GPU this machine seems to have, found without ManimGX (its name), or None."""
    if sys.platform == "darwin":
        return "Apple silicon GPU (Metal)" if platform.machine() == "arm64" else "Mac GPU (Metal)"
    if shutil.which("nvidia-smi"):
        code, out, _ = _run(["nvidia-smi", "-L"], timeout=20)
        if code == 0 and out.strip():
            return out.strip().splitlines()[0]
    if shutil.which("lspci"):
        virtual = re.compile(r"cirrus|qxl|virtio|vmware svga|bochs|red hat|hyper-v|matrox|aspeed", re.I)
        for ln in _run(["lspci"], timeout=20)[1].splitlines():
            if re.search(r"vga|3d controller|display", ln, re.I) and not virtual.search(ln):
                return ln.split(": ", 1)[-1]
    return None


def font_installed(name="PT Serif"):
    """Whether ManimGX (which draws with the system's fonts) can use this font."""
    if shutil.which("fc-list"):
        return name.lower() in _run(["fc-list", ":", "family"])[1].lower()
    dirs = [Path.home() / "Library/Fonts", Path("/Library/Fonts"), Path("/System/Library/Fonts"),
            Path("/System/Library/Fonts/Supplemental")]
    key = name.replace(" ", "").lower()
    return any(key in f.name.replace("_", "").replace("-", "").lower() for d in dirs if d.exists() for f in d.iterdir())


def _node():
    if not shutil.which("node"):
        return None
    m = re.match(r"v(\d+)", _run(["node", "--version"])[1].strip())
    return int(m[1]) if m else None


PROBE = r"""
import json, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import voice as V
out = Path(tempfile.mkdtemp()) / "probe.wav"
V._tts_model()
t = time.time()
V.tts("A binary search halves the list at every step, so a million items take about twenty comparisons.", out)
took = time.time() - t
try:
    import resource
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (2**20 if sys.platform == "darwin" else 1024)
except ImportError:
    peak = None
print(json.dumps({"rtf": round(took / V.duration(out), 2), "peak_mb": peak and round(peak)}))
"""


def voice_probe():
    """Kokoro's speed here: {"rtf": seconds of work per second of speech, "peak_mb": RAM}, or {"error"}."""
    py = V.python()
    if py is None:
        return {"error": "not set up"}
    code, out, err = _run([py, "-c", PROBE, str(HERE)], timeout=300)
    if code == 0 and out.strip():
        return json.loads(out.strip().splitlines()[-1])
    return {"error": (err.strip().splitlines() or ["voice probe failed"])[-1][:300]}


def profile(where=".", probe=True):
    g = gpu() if manimgx_python() else {"error": "manimgx is not installed"}
    voice_ready = V.python() is not None and V.MODEL_FILE.exists() and V.VOICES_FILE.exists()
    return {
        "os": platform.system(), "arch": platform.machine(),
        "cpu": _cpu(), "ram_gb": _ram_gb(), "free_disk_gb": min(_free_gb(where), _free_gb(V.HOME)),
        "gpu": g, "gpu_hint": gpu_hint(),
        "render": "gpu" if g.get("device_type") in GPU_TYPES else "cpu" if g.get("device_type") == "Cpu" else "none",
        "tools": {
            "ffmpeg": bool(shutil.which("ffmpeg")), "node": _node(), "npm": bool(shutil.which("npm")),
            "manimgx": manimgx_python() is not None,
            "latex": bool(shutil.which("latex") or shutil.which("pdflatex")),
            "pt_serif": font_installed(),
            "voice": voice_ready,
        },
        "voice": voice_probe() if probe and voice_ready else None,
    }


def _scale(minutes_8cores, cores):
    return max(1, round(minutes_8cores * 8 / max(1, cores)))


def frameworks(p):
    """For each framework and the voice: status (fast, slow, setup, unavailable), why, fix lines.
    "slow" and "unavailable" are limits of the hardware; "setup" only needs installing something."""
    cores, ram, t = p["cpu"]["cores"], p["ram_gb"] or 0, p["tools"]
    out = {}

    # Remotion: React in headless Chrome, on the CPU
    if p["arch"].lower() not in ("x86_64", "amd64", "arm64", "aarch64"):
        out["remotion"] = {"status": "unavailable", "why": f"Remotion's Chrome has no build for {p['arch']}", "fix": []}
    elif ram < 2:
        out["remotion"] = {"status": "unavailable", "why": f"{ram} GB of RAM: headless Chrome needs about 2 GB", "fix": []}
    else:
        fix = []
        if not t["node"] or t["node"] < NODE_MIN or not t["npm"]:
            fix.append(f"Install Node.js {NODE_MIN} or newer with npm (https://nodejs.org; brew install node; "
                       "or a nodesource / nvm install on Linux)")
        mins = _scale(REMOTION_MIN_8CORES, cores)
        status = "setup" if fix else "slow" if mins > 15 or ram < 4 else "fast"
        why = f"renders in headless Chrome on the CPU: an 8 minute 1080p30 video in about {mins} min"
        if ram < 4:
            why += f"; {ram} GB of RAM allows only one or two Chrome workers"
        out["remotion"] = {"status": status, "why": why, "fix": fix}

    # ManimGX: wgpu, GPU or Mesa's lavapipe
    fix = []
    if not t["manimgx"]:
        fix.append("Install ManimGX: uv tool install manimgx")
    if not t["latex"]:
        fix.append("Install LaTeX for m.MathTex (MacTeX: brew install --cask mactex-no-gui; TeX Live on Linux)")
    if not t["pt_serif"]:
        fix.append(f"Install the videos' fonts (PT Serif, JetBrains Mono) for ManimGX: {HERE / 'setup_fonts.sh'}")
    slow = ", ".join(f"{_scale(v, cores)} min at {k}" for k, v in MANIMGX_CPU_MIN_8CORES.items())
    if p["render"] == "gpu":
        out["manimgx"] = {"status": "fast", "why": f"draws on the GPU ({p['gpu'].get('name')}): 1080p60 in minutes",
                          "fix": fix}
    elif p["render"] == "cpu":
        out["manimgx"] = {"status": "slow", "fix": fix,
                          "why": f"no GPU, so it draws on the CPU ({p['gpu'].get('name')}): an 8 minute video takes "
                                 f"about {slow}"}
    elif t["manimgx"] and p["os"] == "Linux":
        fix.append("ManimGX finds no GPU adapter. Install Mesa's Vulkan drivers, whose lavapipe draws on the CPU: "
                   "sudo apt install mesa-vulkan-drivers (Fedora: sudo dnf install mesa-vulkan-drivers); with an "
                   "NVIDIA GPU, install its driver's Vulkan ICD instead")
        out["manimgx"] = {"status": "setup" if p["gpu_hint"] else "slow", "fix": fix,
                          "why": f"GPU {p['gpu_hint']} is not visible to Vulkan yet" if p["gpu_hint"] else
                                 f"no GPU: with lavapipe it draws on the CPU, about {slow} for an 8 minute video"}
    elif t["manimgx"]:
        out["manimgx"] = {"status": "unavailable", "fix": fix,
                          "why": f"ManimGX finds no GPU adapter: {p['gpu'].get('error', '')[:160]}"}
    elif p["gpu_hint"]:
        out["manimgx"] = {"status": "setup", "fix": fix, "why": f"should draw on the GPU ({p['gpu_hint']})"}
    else:
        if p["os"] == "Linux":
            fix.append("No GPU: also install Mesa's Vulkan drivers (sudo apt install mesa-vulkan-drivers) so "
                       "ManimGX can draw on the CPU")
        out["manimgx"] = {"status": "slow", "fix": fix,
                          "why": f"no GPU found, so it would draw on the CPU: about {slow} for an 8 minute video"}

    # the voice: Kokoro + Whisper on the CPU
    fix, v = [], p.get("voice") or {}
    if ram < 1:
        out["voice"] = {"status": "unavailable", "fix": [], "why": f"{ram} GB of RAM: Kokoro needs about 0.5 GB "
                        "free with the int8 model, Whisper another 0.3 GB"}
    elif not t["voice"]:
        small = ram < 2 or p["free_disk_gb"] < 3
        fix.append(("KOKORO_MODEL=int8 " if small else "") + f"{HERE / 'setup_voice.sh'}  (Kokoro and Whisper, "
                   "about 1 GB)")
        out["voice"] = {"status": "setup", "fix": fix, "why": "Kokoro is not set up yet"}
    elif "error" in v:
        out["voice"] = {"status": "unavailable", "fix": [f"Rerun {HERE / 'setup_voice.sh'}"],
                        "why": f"Kokoro failed here: {v['error']}"}
    elif v:
        rtf = v["rtf"]
        mins = rtf * 8
        why = f"Kokoro speaks at {rtf:.2f}x real time here ({v.get('peak_mb')} MB): 8 minutes of narration in " \
              f"about {mins:.0f} min, plus about half that again for the Whisper check"
        status = "fast" if rtf <= 1 else "slow" if rtf <= 3 else "unavailable"
        if status != "fast" and V.MODEL != "int8":
            fix.append(f"KOKORO_MODEL=int8 {HERE / 'setup_voice.sh'}, then set KOKORO_MODEL=int8: about 25% faster")
        out["voice"] = {"status": status, "why": why, "fix": fix}
    else:
        out["voice"] = {"status": "fast", "why": "Kokoro is set up (speed not measured)", "fix": []}
    return out


def advice(p, only=None):
    """(blocking problems, things to know) for this machine, for one framework (and the voice) or all."""
    fix, tune = [], []
    if not p["tools"]["ffmpeg"]:
        fix.append("Install ffmpeg (brew install ffmpeg / sudo apt install ffmpeg)")
    if p["free_disk_gb"] < 3:
        fix.append(f"{p['free_disk_gb']} GB free: the voice, the renderer and the video need about 3 GB")
    for name, f in frameworks(p).items():
        if only and name not in (only, "voice"):
            continue
        fix += f["fix"] if (only or name == "voice") else []
        tune.append(f"{name}: {f['status']}: {f['why']}")
    if p["render"] == "cpu" and only in (None, "manimgx"):
        tune.append("manimgx on the CPU: always render with scripts/render.py (one-thread parallel segments, "
                    "a format that fits the time budget), never a plain 1920x1080 at 60 fps manimgx render")
    return fix, tune


def main():
    only = sys.argv[sys.argv.index("--for") + 1] if "--for" in sys.argv else None
    p = profile(probe="--no-probe" not in sys.argv)
    fix, tune = advice(p, only)
    if "--json" in sys.argv:
        print(json.dumps({**p, "frameworks": frameworks(p), "fix": fix, "tune": tune}, indent=1))
        return 1 if fix else 0
    g, t = p["gpu"], p["tools"]
    print(f"OS        {p['os']} {p['arch']}")
    print(f"CPU       {p['cpu']['model']}, {p['cpu']['cores']} cores" + (", AVX2" if p["cpu"].get("avx2") else ""))
    print(f"RAM       {p['ram_gb']} GB    free disk {p['free_disk_gb']} GB")
    print("GPU       " + (f"{g.get('name')} [{g.get('device_type')}, {g.get('backend')}]" if "error" not in g
                          else p["gpu_hint"] or "none found"))
    print("tools     " + ", ".join(f"{k} {('v' + str(v)) if k == 'node' and v else 'ok' if v else 'MISSING'}"
                                   for k, v in t.items()))
    for s in fix:
        print(f"FIX   {s}")
    for s in tune:
        print(f"NOTE  {s}")
    return 1 if fix else 0


if __name__ == "__main__":
    sys.exit(main())
