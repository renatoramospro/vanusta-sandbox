def merge_intervals(intervals):
    if not intervals:
        return []
    
    # Ordena os intervalos pelo valor inicial
    intervals.sort(key=lambda x: x[0])
    
    merged = [intervals[0]]
    
    for current in intervals[1:]:
        prev = merged[-1]
        
        # Se o início do intervalo atual é menor ou igual ao fim do anterior, há sobreposição ou toque
        if current[0] <= prev[1]:
            # Atualiza o fim do intervalo anterior para ser o maior entre os dois fins
            prev[1] = max(prev[1], current[1])
        else:
            merged.append(current)
            
    return merged

# --- testes do benchmark (não fazem parte da resposta) ---
assert merge_intervals([]) == []
assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
assert merge_intervals([[5, 6], [1, 2], [2, 3]]) == [[1, 3], [5, 6]]
assert merge_intervals([[1, 10], [2, 3], [4, 5]]) == [[1, 10]]
print("BENCHMARK_OK")