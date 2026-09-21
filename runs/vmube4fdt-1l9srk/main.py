def merge_intervals(intervals):
    if not intervals:
        return []
    
    # Ordena os intervalos pelo tempo de início
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    
    merged = []
    for interval in sorted_intervals:
        # Se a lista estiver vazia ou se o início do intervalo atual 
        # for maior que o fim do último intervalo mesclado, não há sobreposição
        if not merged or interval[0] > merged[-1][1]:
            merged.append(list(interval))
        else:
            # Caso contrário, há sobreposição ou eles se tocam, então mescla
            merged[-1][1] = max(merged[-1][1], interval[1])
            
    return merged

# --- testes do benchmark (não fazem parte da resposta) ---
assert merge_intervals([]) == []
assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
assert merge_intervals([[5, 6], [1, 2], [2, 3]]) == [[1, 3], [5, 6]]
assert merge_intervals([[1, 10], [2, 3], [4, 5]]) == [[1, 10]]
print("BENCHMARK_OK")