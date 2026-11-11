"""Blender scenes timed to the narration, in the house style. Runs inside Blender (blender.py starts it):

    import sys; sys.path.insert(0, "<this skill>/scripts")
    import blender_kit as K
    K.setup()                                    # theme world, camera, lights, frame range, render settings
    o = K.sphere((0, 0, 0), 0.6, K.gold())
    K.grow(o, K.at("wa1", 1))                     # appears when bracket 1 of line wa1 is spoken
    K.camera_to((6, 0, 1), K.at("wa3", 0), dur=2)
    K.finish()                                   # renders what blender.py asked for

Times are seconds from the start of the video; each helper keyframes the property at that frame.
On a GPU it renders with Eevee; on the CPU with Cycles at a few samples per pixel.
"""
import json
import math
import os
import sys
from pathlib import Path

import bpy

TL = json.loads(Path(os.environ["EXPLAINER_TIMELINE"]).read_text())
S = TL["theme"]
FPS = TL["fps"]
LINES = {ln["key"]: ln for ln in TL["lines"]}
USED = set()
FONTS = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "fonts"


def rgb(hex_color, a=1.0):
    h = hex_color.lstrip("#")
    lin = [(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in lin]
    return (*lin, a)


def at(key, i=0):
    s = LINES[key]["spans"][i]
    USED.add(f"{key}:{i}")
    return s["start"]


def frame(t):
    return max(1, round(t * FPS) + 1)


def setup():
    """An empty scene; the camera starts at (0, -11, 0.4) looking along +y (about ±4 by ±2.2 units visible at y = 0)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, max(1, round(TL["duration"] * FPS))
    sc.render.resolution_x, sc.render.resolution_y = TL["width"], TL["height"]
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = rgb(S["bg"])
    sc.world = world
    gpu = os.environ.get("EXPLAINER_BLENDER_GPU") == "1"
    sc.render.engine = "BLENDER_EEVEE_NEXT" if gpu else "CYCLES"
    if not gpu:
        sc.cycles.device, sc.cycles.samples = "CPU", int(os.environ.get("EXPLAINER_BLENDER_SAMPLES", "16"))
        sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "Standard"
    bpy.ops.object.camera_add(location=(0, -11, 0.4), rotation=(math.radians(90), 0, 0))
    sc.camera = bpy.context.object
    for loc, power in (((4, -4, 6), 4.0), ((-5, -2, 2), 1.2)):
        bpy.ops.object.light_add(type="SUN", location=loc)
        bpy.context.object.data.energy = power
        bpy.context.object.rotation_euler = (math.radians(40), 0, math.atan2(loc[0], -loc[1]))
    return sc


def material(color, metal=0.2, rough=0.4, emit=0.0):
    m = bpy.data.materials.new(color)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = rgb(color)
    p.inputs["Metallic"].default_value, p.inputs["Roughness"].default_value = metal, rough
    if emit:
        p.inputs["Emission Color"].default_value = rgb(color)
        p.inputs["Emission Strength"].default_value = emit
    return m


def gold():
    return material(S["accent"], 0.6, 0.3)


def plain(color=None):
    return material(color or S["fg"], 0.0, 0.55)


def _put(obj, mat):
    if mat is not None:
        obj.data.materials.append(mat)
    return obj


def sphere(loc, r, mat=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=48, ring_count=24)
    bpy.ops.object.shade_smooth()
    return _put(bpy.context.object, mat)


def box(loc, size, mat=None):
    bpy.ops.mesh.primitive_cube_add(location=loc, scale=[s / 2 for s in size])
    return _put(bpy.context.object, mat)


def cylinder(a, b, r, mat=None):
    """A rod from point a to point b."""
    from mathutils import Vector
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=(b - a).length, location=(a + b) / 2, vertices=32)
    o = bpy.context.object
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = (b - a).to_track_quat("Z", "Y")
    return _put(o, mat)


def text(body, loc, size=0.4, color=None, bold=False):
    """3D text in PT Serif (scripts/setup_fonts.sh), facing the camera's start."""
    bpy.ops.object.text_add(location=loc, rotation=(math.radians(90), 0, 0))
    o = bpy.context.object
    o.data.body, o.data.size, o.data.align_x = body, size, "CENTER"
    f = FONTS / ("PT_Serif-Web-Bold.ttf" if bold else "PT_Serif-Web-Regular.ttf")
    if f.exists():
        o.data.font = bpy.data.fonts.load(str(f))
    return _put(o, plain(color))


def _key(obj, path, value, t):
    setattr(obj, path, value)
    obj.keyframe_insert(data_path=path, frame=frame(t))


def grow(obj, t, dur=0.6):
    """Hidden until t, then grows to its size."""
    full = tuple(obj.scale)
    _key(obj, "scale", (0, 0, 0), 0)
    _key(obj, "scale", (0, 0, 0), t)
    _key(obj, "scale", full, t + dur)


def shrink(obj, t, dur=0.4):
    """Shrinks away between t and t + dur, e.g. labels before the camera turns away from them."""
    _key(obj, "scale", tuple(obj.scale), t)
    _key(obj, "scale", (0, 0, 0), t + dur)


def move(obj, loc, t, dur=1.0):
    _key(obj, "location", tuple(obj.location), t)
    _key(obj, "location", loc, t + dur)


def spin(obj, degrees, t, dur=1.5, axis=2):
    r = list(obj.rotation_euler)
    _key(obj, "rotation_euler", tuple(r), t)
    r[axis] += math.radians(degrees)
    _key(obj, "rotation_euler", tuple(r), t + dur)


def camera_to(loc, t, dur=1.5, look=(0, 0, 0)):
    """Fly the camera to loc between t and t + dur, looking at look."""
    from mathutils import Vector
    cam = bpy.context.scene.camera
    _key(cam, "location", tuple(cam.location), t)
    _key(cam, "rotation_euler", tuple(cam.rotation_euler), t)
    cam.location = loc
    cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam.keyframe_insert("location", frame=frame(t + dur))
    cam.keyframe_insert("rotation_euler", frame=frame(t + dur))


def _layout(sc, t):
    """Text off the frame or overlapping another object, as the camera sees it at the current frame."""
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    boxes, problems = [], []
    for obj in sc.objects:
        if obj.type not in ("MESH", "FONT") or obj.hide_render or min(obj.matrix_world.to_scale()) < 0.05:
            continue
        pts = [world_to_camera_view(sc, sc.camera, obj.matrix_world @ Vector(c)) for c in obj.bound_box]
        if min(p.z for p in pts) <= 0:
            continue
        b = (min(p.x for p in pts), min(p.y for p in pts), max(p.x for p in pts), max(p.y for p in pts))
        boxes.append((obj, b))
        if obj.type == "FONT" and (b[0] < -0.002 or b[1] < -0.002 or b[2] > 1.002 or b[3] > 1.002):
            problems.append(f"{t:7.2f}s  off frame: text {obj.data.body[:30]!r}")
    name = lambda o: f"text {o.data.body[:30]!r}" if o.type == "FONT" else o.name  # noqa: E731
    for i, (p, P) in enumerate(boxes):
        for q, Q in boxes[i + 1:]:
            if "FONT" not in (p.type, q.type):
                continue  # 3D shapes may touch or cross each other, like the atoms and bonds of a molecule
            w, h = min(P[2], Q[2]) - max(P[0], Q[0]), min(P[3], Q[3]) - max(P[1], Q[1])
            if w <= 0 or h <= 0:
                continue
            small = min((P[2] - P[0]) * (P[3] - P[1]), (Q[2] - Q[0]) * (Q[3] - Q[1])) or 1e-9
            inside = all(P[k] <= Q[k] for k in (0, 1)) and all(P[k] >= Q[k] for k in (2, 3)) or \
                all(Q[k] <= P[k] for k in (0, 1)) and all(Q[k] >= P[k] for k in (2, 3))
            if not inside and w * h > 0.03 * small:
                problems.append(f"{t:7.2f}s  overlap: {name(p)} and {name(q)} ({round(100 * w * h / small)}%)")
    return problems


def finish():
    """Write check.json, then render what blender.py asked for: stills at times, or every frame."""
    sc = bpy.context.scene
    out = Path(os.environ["EXPLAINER_OUT"])
    out.mkdir(parents=True, exist_ok=True)
    layout = []
    for t in (float(x) for x in (os.environ.get("EXPLAINER_STILLS") or "").split(",") if x):
        sc.frame_set(frame(t))
        layout += _layout(sc, t)
    (out / "check.json").write_text(json.dumps({"used": sorted(USED), "layout": layout}))
    sc.render.resolution_percentage = round(100 * float(os.environ.get("EXPLAINER_SCALE", "1")))
    sc.render.image_settings.file_format = "PNG"
    stills = os.environ.get("EXPLAINER_STILLS")
    if stills:
        for i, t in enumerate(float(x) for x in stills.split(",")):
            sc.frame_set(frame(t))
            sc.render.filepath = str(out / f"{i:03d}_{t:.2f}s.png")
            bpy.ops.render.render(write_still=True)
    else:
        sc.render.filepath = str(out / "frame_")
        bpy.ops.render.render(animation=True)
    sys.stdout.flush()
