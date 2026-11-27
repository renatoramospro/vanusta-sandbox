def merge_intervals(intervals):
    if not intervals:
        return []

    intervals.sort(key=lambda x: x[0])

    merged = [intervals[0]]

    for current_start, current_end in intervals[1:]:
        last_merged_start, last_merged_end = merged[-1]

        # Verifica sobreposição ou toque (fim de um == início do outro)
        if current_start <= last_merged_end:
            # Junta: atualiza o fim do último intervalo na lista 'merged'
            merged[-1][1] = max(last_merged_end, current_end)
        else:
            # Não há sobreposição, adiciona o novo intervalo
            merged.append([current_start, current_end])

    return merged

# --- testes do benchmark (não fazem parte da resposta) ---
assert merge_intervals([]) == []
assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
assert merge_intervals([[5, 6], [1, 2], [2, 3]]) == [[1, 3], [5, 6]]
assert merge_intervals([[1, 10], [2, 3], [4, 5]]) == [[1, 10]]
print("BENCHMARK_OK")