def merge_intervals(intervals):
    ordered = sorted(intervals, key=lambda interval: interval[0])
    merged = []

    for start, end in ordered:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)

    return merged

# --- testes do benchmark (não fazem parte da resposta) ---
assert merge_intervals([]) == []
assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
assert merge_intervals([[5, 6], [1, 2], [2, 3]]) == [[1, 3], [5, 6]]
assert merge_intervals([[1, 10], [2, 3], [4, 5]]) == [[1, 10]]
print("BENCHMARK_OK")