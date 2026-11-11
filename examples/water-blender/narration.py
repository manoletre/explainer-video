"""Narration for a short 3D Remotion example (Blender).
    python3 scripts/make_narration.py examples/water-blender/narration.py
    python3 scripts/blender.py check examples/water-blender/water.py
    python3 scripts/blender.py render examples/water-blender/water.py
"""

VOICE = "af_heart"

SECTIONS = {"wa1": "1 · A water molecule"}

LINES = {
    "wa1": "[A water molecule] is [one oxygen atom] bonded to [two hydrogen atoms].",
    "wa2": "The two bonds meet at [an angle of about one hundred and four degrees], so the molecule is "
           "[bent, not straight].",
    "wa3": "[Turn it around], and you see [it is flat]: all three atoms lie [in one plane].",
}
