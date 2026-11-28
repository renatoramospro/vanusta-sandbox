from collections import Counter
import heapq

def top_k_frequent(nums, k):
    counts = Counter(nums)
    # Usamos um min-heap para manter os k elementos mais frequentes.
    # O heap armazenará tuplas: (frequencia, valor).
    # Como queremos que em caso de empate na frequência, o valor menor venha primeiro,
    # e o heapq é um min-heap, precisamos que a prioridade seja:
    # 1. Frequência menor (para ser removido se for menor que o k-ésimo)
    # 2. Valor maior (para ser removido se a frequência for igual, pois queremos o menor valor no resultado final)
    # No entanto, o requisito é: "em caso de empate na frequência, o valor menor vem primeiro" no *resultado*.
    # Para o heap, queremos manter os k melhores. O pior candidato a ser mantido é aquele com menor frequência,
    # ou com mesma frequência mas maior valor.
    
    # Estrutura do heap: (frequencia, -valor)
    # Usar -valor garante que, em caso de empate na frequência, o valor maior (mais negativo)
    # seja considerado "maior" pelo min-heap, e assim, o valor menor (menos negativo)
    # será mantido no heap se o tamanho for k.
    
    # Vamos usar (frequencia, valor) e um heap de tamanho k, mas invertendo a lógica de comparação
    # para priorizar a frequência alta e, em caso de empate, o valor baixo.
    
    # Heap de tamanho k: (frequencia, valor)
    # O heap deve ser um min-heap. Queremos que o elemento "pior" (menor frequência, ou mesma frequência e maior valor)
    # fique no topo para ser removido.
    
    min_heap = [] # Armazena (frequencia, valor)
    
    for num, freq in counts.items():
        # Para o min-heap, queremos que o elemento com menor prioridade fique no topo.
        # Prioridade: 1. Frequência baixa. 2. Valor alto (em caso de empate).
        # Portanto, armazenamos (freq, num)
        
        if len(min_heap) < k:
            heapq.heappush(min_heap, (freq, num))
        else:
            # Compara o elemento atual (freq, num) com o topo (min_freq, min_num)
            min_freq, min_num = min_heap[0]
            
            # Se o atual for melhor que o topo:
            # 1. Frequência maior: freq > min_freq
            # 2. Frequência igual E valor menor: freq == min_freq and num < min_num
            
            if freq > min_freq or (freq == min_freq and num < min_num):
                heapq.heapreplace(min_heap, (freq, num))
                
    # O heap agora contém os k elementos mais frequentes, seguindo a regra de desempate.
    # Precisamos ordenar o resultado final: do mais frequente para o menos, e em caso de empate, o menor valor primeiro.
    
    # Extrai os elementos e os converte para uma lista de tuplas (freq, num)
    result_tuples = list(min_heap)
    
    # Ordenação final:
    # 1. Por frequência (decrescente): -freq
    # 2. Por valor (crescente): num
    result_tuples.sort(key=lambda x: (-x[0], x[1]))
    
    # Retorna apenas os valores
    return [num for freq, num in result_tuples]

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