def two_sum(nums, target):
    seen = {}
    for j, num in enumerate(nums):
        if target - num in seen:
            return seen[target - num], j
        seen[num] = j

# --- testes do benchmark (não fazem parte da resposta) ---
assert two_sum([2, 7, 11, 15], 9) == (0, 1)
assert two_sum([3, 2, 4], 6) == (1, 2)
assert two_sum([3, 3], 6) == (0, 1)
assert two_sum([-1, -2, -3, -4, -5], -8) == (2, 4)
print("BENCHMARK_OK")