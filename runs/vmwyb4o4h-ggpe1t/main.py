from collections import Counter
import heapq

def top_k_frequent(nums, k):
    counts = Counter(nums)
    # Usamos um min-heap para manter os k elementos mais frequentes.
    # O heap armazenará tuplas: (frequencia, valor).
    # Como queremos que em caso de empate na frequência, o valor menor venha primeiro,
    # e o min-heap prioriza o menor primeiro, precisamos inverter a ordem de prioridade
    # para a frequência (usar -frequencia) e manter o valor como está.
    # No entanto, o requisito é: "do mais para o menos frequente; em caso de empate na frequência, o valor menor vem primeiro."
    # Isso significa que a ordenação final deve ser: (frequencia DESC, valor ASC).

    # Vamos usar o heapq para encontrar os k elementos com maior frequência.
    # O heap deve ser um min-heap baseado na prioridade de ordenação.
    # Prioridade: 1. Frequência (menor é pior, queremos maior) -> usar -frequencia
    #            2. Valor (menor é melhor em caso de empate) -> usar valor

    # O heap armazenará (frequencia, valor).
    # Para simular a ordenação desejada (frequência decrescente, valor crescente),
    # podemos usar um heap de tamanho k, mas a lógica de comparação precisa ser ajustada.

    # Alternativa mais simples: obter todos os itens e ordenar.
    items = counts.items() # (valor, frequencia)
    
    # Ordenação:
    # 1. Por frequência (descendente: -frequencia)
    # 2. Por valor (crescente: valor)
    sorted_items = sorted(items, key=lambda item: (-item[1], item[0]))
    
    # Extrair os valores dos k primeiros
    result = [item[0] for item in sorted_items[:k]]
    
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