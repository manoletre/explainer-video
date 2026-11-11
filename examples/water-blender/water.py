"""A water molecule in Blender, timed to the narration with the skill's blender_kit."""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))
import blender_kit as K  # noqa: E402

K.setup()
half = math.radians(104.5 / 2)
O = (0, 0, 0.4)
Hs = [(math.sin(half) * 1.5, 0, 0.4 - math.cos(half) * 1.5), (-math.sin(half) * 1.5, 0, 0.4 - math.cos(half) * 1.5)]
title = K.text("H2O", (0, 0, 1.75), 0.45, bold=True)
K.grow(title, K.at("wa1", 0))
o = K.sphere(O, 0.62, K.gold())
K.grow(o, K.at("wa1", 1))
for i, h in enumerate(Hs):
    t = K.at("wa1", 2) + 0.3 * i
    K.grow(K.sphere(h, 0.36, K.plain()), t)
    K.grow(K.cylinder(O, h, 0.1, K.plain(K.S["dim"])), t)
angle = K.text("bond angle ≈ 104.5°", (0, 0, -1.55), 0.3)
K.grow(angle, K.at("wa2", 0))
bent = K.text("bent, not straight", (2.3, 0, 0.3), 0.28, K.S["ink"])
K.grow(bent, K.at("wa2", 1))
for label in (title, angle, bent):
    K.shrink(label, K.at("wa3", 0))
K.camera_to((11, 0, 0.4), K.at("wa3", 0), dur=2.2, look=(0, 0, 0.4))
K.grow(K.box((0, 0, 0.1), (3.6, 0.02, 2.4), K.material(K.S["accent"], 0, 0.6, emit=0.4)), K.at("wa3", 1))
flat = K.text("one plane", (0, -1.4, -1.55), 0.3, K.S["ink"])
flat.rotation_euler = (math.radians(90), 0, math.radians(90))
K.grow(flat, K.at("wa3", 2))
K.finish()
