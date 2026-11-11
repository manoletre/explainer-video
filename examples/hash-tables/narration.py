"""Narration for the hash tables explainer (Remotion), one line per beat.

Spoken form, not screen form. [Brackets] mark the words each animation plays on; they are not spoken.
    python3 scripts/make_narration.py examples/hash-tables/narration.py
    python3 scripts/remotion.py new examples/hash-tables
    python3 scripts/remotion.py render examples/hash-tables
"""

VOICE = "am_michael"
# THEME = "light"  # this video only; otherwise the default from scripts/style.py (dark)

SECTIONS = {
    "pr1": "1 · The problem",
    "hf1": "2 · The trick",
    "co1": "3 · Collisions",
    "su1": "4 · Summary",
}

LINES = {
    "pr1": "Say you keep [a list of a million names], and you want to know if [Ada] is in it. Without any order, you "
           "[check them one by one].",
    "pr2": "On average that's [half a million comparisons], and [a million] when the name isn't there. A hash table "
           "does it in [about one].",
    "hf1": "The trick is [a hash function]. It turns the key, [Ada], into [a number], and that number, modulo the "
           "table size, is [a bucket index].",
    "hf2": "So to find Ada, you [hash the name again], [jump straight to bucket three], and [compare just the keys "
           "stored there].",
    "co1": "Sometimes [two keys land in the same bucket]. That's [a collision], and the bucket keeps [a short list].",
    "co2": "How long are those lists? That's [the load factor, alpha], [the number of keys] over [the number of "
           "buckets]. A successful lookup checks [about one plus alpha over two keys].",
    "co3": "Keep alpha [below one] by [doubling the table when it fills up], and lookups stay [close to one step], "
           "even [as the table grows].",
    "su1": "So [a hash table] trades [extra memory] for [constant time lookups] [on average]. Use it whenever you look "
           "up [exact keys, many times].",
}
