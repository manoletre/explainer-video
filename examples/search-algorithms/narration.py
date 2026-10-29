"""Narration for search_algorithms.py, one line per beat.

Spoken form, not screen form. [Brackets] mark the words each animation plays on; they are not spoken.
Generate the clips with `python3 scripts/make_narration.py examples/search-algorithms/narration.py`.
"""

VOICE = "US male"

LINES = {
    # intro
    "in1": "Six search algorithms come up again and again in interviews. [Linear, binary, jump, exponential, interpolation, and hash table lookup]. By the end of this video, you'll know [how each one works, what it costs, and when to pick it].",
    "in2": "For each one, we track [the best case, the average case, and the worst case], plus [the extra memory it needs]. And one question that matters just as much: [what does the data have to look like]?",
    # 1. growth rates
    "bg1": "First, a feel for the sizes. Take [an array of one million elements]. Here's roughly how many steps each growth rate means.",
    "bg2": "Constant time is [one step]. Log log n is [about four]. Log n is [about twenty]. Square root of n is [one thousand]. And linear is [the full million].",
    "bg3": "That gap is the whole story. Going from linear to logarithmic turns [a million steps into twenty]. Keep these five numbers in mind, because [every algorithm in this video lands on one of them].",
    # 2. linear
    "li1": "Linear search is the simplest. [Start at the first element], [compare each one to the target, moving right], until you [find it, or run off the end].",
    "li2": "If the target is [the very first element], that's one comparison, the best case, order one. If it's [the last element, or not there at all], you check all n, the worst case, order n. On average you check [about half], n over two, and since we drop constants, that's still order n.",
    "li3": "It needs [no extra memory], just an index. Its big strength is that [the data can be unsorted], or even a linked list. And if you only search once, [sorting first costs n log n], which is worse than just scanning.",
    # 3. binary
    "bi1": "Binary search needs [a sorted array]. Keep two pointers, [low and high]. We're looking for twenty three. Check [the middle element]. It's forty five, too big, so [the whole right half is thrown away].",
    "bi2": "The new middle is [twelve, too small], so [throw away the left part]. The next middle is [twenty three. Found it], in three steps.",
    "bi3": "Each step halves the range. [Sixteen, eight, four, two, one]. The number of halvings is [log base two of n]. For a million elements, that's [about twenty comparisons].",
    "bi4": "The best case is order one, when [the target sits right in the middle]. Average and worst are [order log n]. The loop version uses [constant space]. The recursive version uses [log n stack frames].",
    "bi5": "Two classic interview bugs. Compute the middle as [low, plus high minus low, over two], to avoid integer overflow. And loop [while low is less than or equal to high], so a range of one element still gets checked.",
    # 4. jump
    "ju1": "Jump search also needs sorted data. Instead of halving, it [jumps ahead in fixed blocks], checking only [the last element of each block], until it [passes the target]. Then it [steps back and scans that one block].",
    "ju2": "How big should a block be? With block size m, you make [about n over m jumps], plus [up to m steps] inside the last block. That total is smallest when [m is the square root of n].",
    "ju3": "So the cost is [order square root of n]. For a million elements, that's [about a thousand jumps plus a thousand steps]. Slower than binary search, but it [only moves backward once], which helps when going back is expensive.",
    # 5. exponential
    "ex1": "Exponential search starts small and [doubles the index: one, two, four, eight], until it finds [an element bigger than the target]. That traps the target between [the last two probes]. Then it runs [a binary search inside that range].",
    "ex2": "If the target sits at position i, doubling takes [about log i steps], and the binary search over that range takes [another log i]. So it's [order log i]. That's never worse than order log n, and much better [when the target is near the front].",
    "ex3": "Its real superpower is that [it never needs to know n]. That makes it the go to choice for [unbounded or infinite lists], like a stream, or a service that only tells you what's at a given index. Its space is [constant].",
    # 6. interpolation
    "ip1": "Interpolation search is how you use a phone book. Looking for a name that starts with W? You [don't open the middle]. You [open near the end]. It guesses the position from [the values themselves].",
    "ip2": "The guess is [a straight line between the lowest and highest values]. The position is [low, plus the target minus the low value, times the index range, divided by the value range].",
    "ip3": "Try it on [ten, twenty, thirty, up to one hundred sixty], looking for one hundred thirty. The formula gives [index twelve], and [that's exactly the target], in one probe.",
    "ip4": "On uniformly spread data, the average is [order log log n], about four probes for a million elements. But on skewed data, like [one, two, three, and then a million], each guess [lands just one step forward], and it falls to [order n].",
    # 7. hash table
    "ha1": "Hash tables take a different route: [no comparisons, and no order]. A hash function [turns the key into a bucket index], so you [jump straight to the right bucket].",
    "ha2": "With a good hash function, and [a load factor kept low by resizing], each bucket holds only a few items. So lookup is [order one on average].",
    "ha3": "But if [every key lands in the same bucket], that bucket becomes a long list, and lookup is [order n]. That's the worst case, from a bad hash function, or an attacker choosing the keys.",
    "ha4": "The price is [order n extra space] for the table, and [no ordering], so no range queries and no next larger key. Use it when you look up [exact keys, many times].",
    # 8. comparison
    "cm1": "Here's the whole picture in one table. [Every algorithm has an order one best case], because the first thing it checks might be the target. So [the best case almost never decides anything].",
    "cm2": "The real differences are in the average and worst columns. [Hashing wins the average]. [Interpolation is fast on uniform data, but can collapse to n]. And [binary and exponential search guarantee log n].",
    "cm3": "Space is [constant for all of them except the hash table], which pays [order n memory] for its speed.",
    # 9. choosing
    "ch1": "So how do you pick? Ask in order. [Unsorted data, and you search only once]? Linear search. [Exact keys, looked up many times]? Build a hash table.",
    "ch2": "[Sorted, in memory]? Binary search, the safe default. [Size unknown or unbounded]? Exponential search. [Sorted and evenly spread]? Interpolation. [Stepping back is costly]? Jump search.",
    # 10. interview check
    "qz1": "Before your interview, make sure you can answer these out loud. [Why is binary search log n]? [Why is the jump size the square root of n]? [When does a hash table hit order n]? And [when does linear search beat binary search]?",
    "qz2": "If you can explain those, and [write binary search without an off by one bug], you know these algorithms very well. Good luck.",
}
