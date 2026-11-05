# Must-know data structures: cheat sheet

Average-case costs unless noted. n = number of items, L = key length, V/E = vertices/edges.

| Structure | Access | Search | Insert | Delete | Notes |
|---|---|---|---|---|---|
| Array (dynamic) | O(1) | O(n) | O(n); append O(1) amortized | O(n) | contiguous; cache-friendly |
| Linked list | O(n) | O(n) | O(1) at a held node | O(1) at a held node (doubly linked) | extra pointer per node |
| Stack | O(1) top | O(n) | O(1) push | O(1) pop | LIFO |
| Queue (deque / ring buffer) | O(1) front | O(n) | O(1) enqueue | O(1) dequeue | FIFO; popping index 0 of a plain array is O(n) |
| Hash table | — | O(1), worst O(n) | O(1), worst O(n) | O(1), worst O(n) | no order |
| Balanced BST (red-black, AVL) | — | O(log n) | O(log n) | O(log n) | sorted order, ranges, successor |
| Plain BST | — | O(h), O(n) if sorted inserts | O(h) | O(h) | h = height |
| Binary heap | O(1) min/max | O(n) | O(log n) | O(log n) pop | heapify O(n) |
| Trie | — | O(L) | O(L) | O(L) | prefix queries |
| Graph (adjacency list) | — | — | O(1) add edge | O(deg) | space O(V+E); BFS/DFS O(V+E) |
| Graph (adjacency matrix) | O(1) edge check | — | O(1) | O(1) | space O(V²) |

## Formulas and worked numbers from the video

- **Array address**: `address(i) = start + i × size`. With 4-byte ints at 1000: `address(3) = 1012`.
- **Amortized append (doubling)**: 16 appends starting at capacity 1 copy 1 + 2 + 4 + 8 = 15 elements,
  so fewer than one copy per append. In general, n appends copy fewer than n elements in total, which makes append O(1) amortized.
  Real growth factors vary. Java's `ArrayList` grows by 1.5×, C++ `std::vector` doubles in libstdc++, and CPython
  `list` grows by about 1.125× plus a constant. Any constant factor > 1 still gives O(1) amortized.
- **Hash bucket**: `bucket = hash(key) mod m`. The video's hashes come from Java's `String.hashCode`
  (`s[0]·31^(k-1) + … + s[k-1]`): cat = 98262 → 6, dog = 99644 → 4, owl = 110468 → 4 (a collision),
  bee → 2, fox → 7, ant → 7. Java's `HashMap` mixes the bits further (`h ^ (h >>> 16)`), so its real buckets can
  differ. The numbers here only illustrate the idea.
- **Load factor**: α = items / buckets, so 6 / 8 = 0.75. Java `HashMap` resizes (doubles) when size exceeds 0.75 × capacity.
  CPython `dict` resizes when it is 2/3 full.
- **BST height**: balanced h ≈ log₂ n; log₂ 10⁶ ≈ 19.9, so about 20 levels for a million keys. Inserting
  10, 20, 30, 40, 50 in order gives a chain of height n.
- **Heap in an array** (0-indexed): children of i are 2i+1 and 2i+2, and the parent is ⌊(i−1)/2⌋.
  The push example is [3, 5, 9, 6, 7, 10] + 2. The 2 swaps past 9, then past 3, giving [2, 5, 3, 6, 7, 10, 9].
  Popping takes the root 2, moves 9 to the top and swaps it with the smaller child 3, giving [3, 5, 9, 6, 7, 10].
- **Heapify is O(n)**: most nodes sit near the bottom and sift down only a little. The total work
  Σ (n / 2^(h+1)) · h over all heights h is O(n).
- **Top-k**: keep a min-heap of size k and replace its root when a larger item arrives. Cost O(n log k).
  The video's example takes the 3 largest of [5, 17, 2, 9, 21, 4, 13, 8, 30, 1, 11, 19], which are 19, 21, 30.
- **BFS/DFS**: both O(V+E). BFS (queue) gives shortest paths in unweighted graphs. In the video graph
  (A–B, A–C, B–D, C–D, D–E), A → E takes 3 edges.

## How to choose

| The problem repeatedly needs… | Use |
|---|---|
| access by position | array |
| lookup by key, or "have I seen this?" | hash map / set |
| sorted order, ranges, next larger | balanced BST (TreeMap, std::map) |
| smallest / largest, again and again | heap (priority queue) |
| last in, first out | stack |
| first in, first out | queue (deque) |
| prefixes of strings | trie |
| connections, paths, dependencies | graph |

## Quiz

1. Why is appending to a dynamic array O(1) amortized?
2. When does a hash table become O(n)?
3. Why do sorted inserts ruin a plain BST?
4. Why is heapify O(n), not O(n log n)?

## Sources

- Cormen, Leiserson, Rivest, Stein, *Introduction to Algorithms* (3rd ed.): dynamic tables and amortized
  analysis (§17.4), hash tables (Ch. 11), BSTs and red-black trees (Ch. 12–13), heaps and BUILD-MAX-HEAP in O(n)
  (Ch. 6), BFS/DFS (Ch. 22).
- OpenJDK `java.util.HashMap` (default load factor 0.75), `java.util.ArrayList` (growth `old + (old >> 1)`),
  `java.lang.String.hashCode`, `java.util.TreeMap` (red-black tree).
- CPython `Objects/dictobject.c` (`USABLE_FRACTION` = 2/3) and `Objects/listobject.c` (over-allocation).
