import heapq
from collections import defaultdict

def top_k_frequent(nums, k):
    freq = defaultdict(int)
    for num in nums:
        freq[num] += 1

    heap = []
    for num, count in freq.items():
        heapq.heappush(heap, (-count, num))

    result = []
    for _ in range(k):
        if heap:
            result.append(heapq.heappop(heap)[1])

    return result

# --- testes do benchmark (não fazem parte da resposta) ---
assert top_k_frequent([1, 1, 1, 2, 2, 3], 2) == [1, 2]
assert top_k_frequent([1], 1) == [1]
assert top_k_frequent([4, 4, 5, 5, 6], 2) == [4, 5]
assert top_k_frequent([3, 1, 2, 2, 3, 1], 3) == [1, 2, 3]
assert top_k_frequent([7, 7, 8], 1) == [7]
assert top_k_frequent([5, 5, 5, 1, 1, 2], 2) == [5, 1]
assert top_k_frequent([9, 9, 8, 8, 8, 7], 1) == [8]
assert top_k_frequent([3, 3, 2, 2, 1], 2) == [2, 3]
print("BENCHMARK_OK")