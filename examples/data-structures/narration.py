"""Narration for data_structures.py, one line per beat.

Spoken form, not screen form. [Brackets] mark the words each animation plays on; they are not spoken.
Every beat that opens on a cleared screen brackets its first words, so the picture starts with the voice.
"""

VOICE = "US male"

LINES = {
    # intro
    "in1": "[Eight data structures] come up in almost every coding interview. [Arrays, linked lists, stacks and queues, hash tables, binary search trees, heaps, graphs, and tries].",
    "in2": "For each one, we'll see [how it's laid out in memory], [what each operation costs], and [the kind of problem it's built for]. At the end, there's [a table to compare them all], and [a quick way to choose].",
    # 1. arrays
    "ar1": "[An array] is one block of memory, with [every element stored right next to the one before it]. [That's the whole trick].",
    "ar2": "To read [element i], the computer computes [the start address, plus i times the element size]. One multiplication and one addition, [no matter how big the array is]. So access by index is [order one].",
    "ar3": "Inserting in the middle is different. To put [a new value at index two], [every element after it shifts one slot to the right]. In the worst case, that's [all n elements], so insert and delete are [order n]. And searching an unsorted array is [order n] too.",
    "ar4": "[Dynamic arrays, like Python lists or Java array lists], grow on their own. When [the array is full], they [allocate a bigger block, and copy everything over]. The textbook version [doubles the size].",
    "ar5": "[Copying sounds expensive, but it's rare]. For [sixteen appends], the copies add up to [one plus two plus four plus eight, which is fifteen]. That's [less than one copy per append], so appending is [order one, amortized].",
    # 2. linked lists
    "ll1": "[A linked list] stores each value in its own node, together with [a pointer to the next node]. The nodes can live [anywhere in memory]. You only keep [a pointer to the head].",
    "ll2": "There's no address formula, so to reach [the fourth element], you [walk from the head, one node at a time]. Access and search are [order n].",
    "ll3": "But [if you already hold a node], inserting after it is cheap. [Create the new node], [point it at the next one], and [point the old node at it]. Two pointer changes, [order one], whatever the length.",
    "ll4": "[The costs: every node carries an extra pointer], and [jumping around memory is slow for the cache]. [A doubly linked list] adds a pointer back, so you can [remove any node you hold in order one]. Pair it with a hash map, and you get [an L R U cache], a classic interview question.",
    # 3. stacks and queues
    "sq1": "[A stack] is last in, first out. You [push onto the top], and you [pop from the top]. Both are [order one], and so is [peeking at the top].",
    "sq2": "Stacks are everywhere: [undo], [the function call stack], and [checking that brackets are balanced]. Push every opening bracket, and [pop it when its closing bracket arrives].",
    "sq3": "[A queue] is first in, first out, like [a line at a shop]. You [enqueue at the back], and [dequeue from the front]. Both are [order one].",
    "sq4": "Careful: [removing from the front of a plain array] shifts every element, which is [order n]. Use [a deque, or a ring buffer] instead. Queues drive [breadth first search], and [task scheduling].",
    # 4. hash tables
    "ha1": "[A hash table] maps keys to values. Take [the key cat]. A hash function turns it into [a number, ninety eight thousand two hundred sixty two], and that number [modulo the eight buckets] is [six]. So cat goes [in bucket six].",
    "ha2": "To look cat up later, [hash it again], and [you land in the same bucket]. No scanning, so [insert, lookup and delete are order one on average].",
    "ha3": "Two keys can land [in the same bucket]. Here, [dog and owl both hash to four]. That's [a collision]. With chaining, [the bucket keeps a short list], and you [check the few keys in it].",
    "ha4": "The load factor is [the number of items, over the number of buckets]. [Six items in eight buckets] is [zero point seven five]. Past a threshold, [the table doubles and rehashes everything]. Java resizes at [zero point seven five], and Python at [two thirds].",
    "ha5": "If [every key collides], one bucket holds everything, and lookup drops to [order n]. And [hash tables keep no order]. You can't ask for [the smallest key, or a range], without scanning them all.",
    # 5. binary search trees
    "bs1": "[A binary search tree] keeps one rule at every node: [everything on the left is smaller], and [everything on the right is larger]. Here's [the tree from inserting fifty, thirty, seventy, twenty, forty, sixty, and eighty].",
    "bs2": "To find [sixty], start at [the root, fifty]. Sixty is larger, so [go right, to seventy]. It's smaller, so [go left. Found it], in three comparisons. Each step goes [one level down].",
    "bs3": "So the cost is [the height of the tree]. When the tree is balanced, [the height is about log base two of n]. For [a million keys], that's [about twenty levels].",
    "bs4": "[But insert keys in sorted order], and [every new node goes to the right]. The tree turns into [a linked list], and everything is [order n]. Self balancing trees, like [red black and A V L trees], [rotate nodes] to keep the height logarithmic.",
    "bs5": "[What you get over a hash table is order]. Reading [left, then root, then right] gives [the keys in sorted order], and you can answer [range queries, or find the next larger key]. Java's [tree map] is a red black tree.",
    # 6. heaps
    "hp1": "[A heap] answers one question fast: [what's the smallest item]? In a min heap, [every parent is smaller than its children], so [the minimum is always at the root]. Peeking at it is [order one].",
    "hp2": "A heap is [a complete tree], filled level by level, so it fits [in a plain array]. The children of index i sit at [two i plus one, and two i plus two]. [No pointers needed].",
    "hp3": "To push, [add the new item at the end], then [swap it with its parent while it's smaller]. Pushing [two] goes [up past nine], [then past three], to the root. At most [one swap per level], so push is [order log n].",
    "hp4": "To pop the minimum, [take the root], [move the last item to the top], and [sift it down, swapping with its smaller child]. That's [order log n] too. Building a heap from n items at once, [called heapify], is [only order n].",
    "hp5": "[Heaps are priority queues]: [Dijkstra's shortest paths], [schedulers], and [merging sorted lists]. For [the k largest of n items], keep [a min heap of size k], and the cost is [n log k].",
    # 7. graphs
    "gr1": "[A graph] is [a set of vertices], joined by [edges]. Edges can be [directed], like links between web pages, and they can carry [weights], like road distances.",
    "gr2": "One way to store it is [an adjacency matrix]: [a V by V grid], with [a one wherever an edge exists]. Checking an edge is [order one], but it always takes [V squared space], even when [most cells are zero].",
    "gr3": "The usual choice is [an adjacency list]: [each vertex keeps a list of its neighbors]. That takes [space V plus E], which is far less [for sparse graphs], the common case.",
    "gr4": "Two traversals visit everything in [order V plus E]. [Breadth first search] uses [a queue], and explores [level by level], which gives [shortest paths when edges have no weights]. [Depth first search] uses [a stack, or recursion], and [goes as deep as it can first].",
    # 8. tries
    "tr1": "[A trie] is a tree of characters. Each path from the root [spells a prefix], and [marked nodes end a word]. Here are [car, cart, cat, and dog].",
    "tr2": "Looking up [a word of length L] takes [L steps], no matter [how many words are stored]. And every word that starts with [c a] lives [under one node], which makes [autocomplete] easy. The price is [memory], one node per character.",
    # 9. comparison
    "cm1": "[Here's everything side by side], with average costs. [Arrays win at access by index]. [Hash tables win at lookup by key].",
    "cm2": "[Balanced trees] give order log n for everything, [plus sorted order]. [Heaps] give the minimum in order one. And [linked lists, stacks and queues] give order one at their ends.",
    # 10. choosing
    "ch1": "[So, how do you choose]? Ask [what the problem does over and over]. [Access by position]: an array. [Lookup by key, or checking if you've seen something]: a hash map, or a set.",
    "ch2": "[Sorted order, ranges, or the next larger value]: a balanced tree. [The smallest or largest, again and again]: a heap. [Last in, first out]: a stack. [First in, first out]: a queue.",
    "ch3": "[Prefixes of strings]: a trie. And [anything about connections, paths, or dependencies]: a graph. In interviews, [naming the right structure] is often [most of the solution].",
    # 11. quiz
    "qz1": "[Before your interview], make sure you can answer these. [Why is appending to a dynamic array order one, amortized]? [When does a hash table become order n]? [Why do sorted inserts ruin a plain binary search tree]?",
    "qz2": "[And why is heapify order n, and not n log n]? If you can explain those four, [you know these data structures well]. Good luck.",
}
