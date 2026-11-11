"""Narration for a short Motion Canvas example (vector tweening on a 2D canvas).
    python3 scripts/make_narration.py examples/linked-list-mc/narration.py
    python3 scripts/motion_canvas.py new examples/linked-list-mc
    python3 scripts/motion_canvas.py render examples/linked-list-mc
"""

VOICE = "bf_emma"

SECTIONS = {"ll1": "1 · Inserting into a linked list"}

LINES = {
    "ll1": "[A linked list is a chain of nodes], each one [pointing to the next].",
    "ll2": "To insert a new value, [make a node], [point it at the next node], then [point the previous node at it].",
    "ll3": "Nothing else moves, so the insert [takes constant time], [however long the list is].",
}
