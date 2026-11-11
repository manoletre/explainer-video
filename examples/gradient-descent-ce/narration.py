"""Narration for a short Manim Community example (math animation on the CPU).
    python3 scripts/make_narration.py examples/gradient-descent-ce/narration.py
    python3 scripts/manim_ce.py check examples/gradient-descent-ce/gradient_descent.py
    python3 scripts/manim_ce.py render examples/gradient-descent-ce/gradient_descent.py
"""

VOICE = "am_michael"

SECTIONS = {"gd1": "1 · Gradient descent"}

LINES = {
    "gd1": "[Gradient descent] finds the bottom of a curve, like [f of x equals x squared], by walking downhill.",
    "gd2": "Each step [moves x against the slope]: [x minus eta times the derivative], and here the derivative "
           "is [two x].",
    "gd3": "So the update [simplifies] to [x times one minus two eta]. With eta at [zero point one], every step "
           "[keeps eighty percent of x], and the point [slides down to zero].",
}
