# Search algorithms: interview cheat sheet

| Algorithm | Best | Average | Worst | Space | Needs |
|---|---|---|---|---|---|
| Linear | O(1) | O(n) | O(n) | O(1) | nothing (unsorted, linked lists OK) |
| Binary | O(1) | O(log n) | O(log n) | O(1) iterative, O(log n) recursive | sorted, random access |
| Jump | O(1) | O(√n) | O(√n) | O(1) | sorted |
| Exponential | O(1) | O(log i) ≤ O(log n) | O(log i) ≤ O(log n) | O(1) | sorted; size may be unknown/unbounded |
| Interpolation | O(1) | O(log log n) on uniform data | O(n) | O(1) | sorted + roughly uniform values |
| Hash table | O(1) | O(1) | O(n) | O(n) | a hash table (built in O(n)) |

`i` = position of the target. Best case is O(1) for all of them, so it rarely decides anything.

## Sizes for n = 1,000,000
| Rate | Steps |
|---|---|
| O(1) | 1 |
| O(log log n) | ≈ 4.3 |
| O(log n) | ≈ 20 (log₂ 10⁶ ≈ 19.9) |
| O(√n) | 1,000 |
| O(n) | 1,000,000 |

## How each works
- **Linear**: scan left to right. Average n/2 comparisons → O(n). If you search once on unsorted data, sorting first (O(n log n)) costs more than scanning.
- **Binary**: compare with middle, discard half. Halvings until one element left = log₂ n.
  ```python
  def binary_search(a, x):
      lo, hi = 0, len(a) - 1
      while lo <= hi:                 # <=: a one-element range must be checked
          mid = lo + (hi - lo) // 2   # avoids (lo + hi) overflow in fixed-width ints
          if a[mid] == x: return mid
          if a[mid] < x: lo = mid + 1
          else: hi = mid - 1
      return -1
  ```
- **Jump**: check every m-th element until you pass the target, then scan back through one block. Cost ≈ n/m + m, minimized at m = √n (derivative: −n/m² + 1 = 0) → ≈ 2√n. Moves backward only once, useful when going back is expensive.
- **Exponential**: probe indices 1, 2, 4, 8, … until A[i] > x (or past the end), then binary search in [i/2, i]. Both phases ≈ log₂ i → O(log i). Doesn't need n, so it works on unbounded/infinite lists.
- **Interpolation**: `pos = lo + (x − A[lo]) · (hi − lo) / (A[hi] − A[lo])`. Example: A = 10, 20, …, 160, x = 130 → pos = (120 · 15) / 150 = 12, one probe. Uniform data → O(log log n) average (Perl, Itai & Avni 1978; Yao & Yao 1976). Skewed data (1, 2, 3, …, 1,000,000) → each guess advances one step → O(n). Guard against A[hi] == A[lo] (division by zero).
- **Hash table**: index = hash(key) mod buckets. Average O(1) if the hash spreads keys and the load factor (items / buckets) is kept bounded by resizing (resizing is amortized O(1) per insert; e.g. Java HashMap resizes at 0.75). Worst O(n) when keys collide into one bucket (bad hash or adversarial keys; Java 8+ turns long chains into trees, giving O(log n)). No ordering → no range queries or "next larger key".

## Which one?
1. Unsorted, searched once → Linear
2. Exact keys, many lookups → Hash table
3. Sorted, in memory → Binary (default)
4. Size unknown / unbounded → Exponential
5. Sorted and evenly spread → Interpolation
6. Stepping back is costly → Jump

## Questions to answer out loud
- Why is binary search O(log n)? It halves the range each step.
- Why is the jump size √n? It minimizes n/m + m.
- When is a hash lookup O(n)? When all keys collide.
- When does linear beat binary? Unsorted data searched once, or very small n (cache-friendly, no branches mispredicted).
- Space of recursive binary search? O(log n) call stack.

## Sources
- Knuth, *The Art of Computer Programming*, Vol. 3 §6.1–6.4 (sequential, binary, hashing).
- Bentley & Yao, "An almost optimal algorithm for unbounded searching", 1976 (exponential search).
- Perl, Itai & Avni, "Interpolation search: a log log N search", CACM 1978.
- Shneiderman, "Jump searching: a fast sequential search technique", CACM 1978.
