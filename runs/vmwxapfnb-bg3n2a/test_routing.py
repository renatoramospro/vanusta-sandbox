import heapq

# 1. Contraexemplo: Dijkstra com peso negativo (Falha)
def dijkstra_fail(graph, start, end):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    pq = [(0, start)]
    while pq:
        dist, current = heapq.heappop(pq)
        if dist > distances[current]:
            continue
        if current == end:
            return dist
        for neighbor, weight in graph[current].items():
            new_dist = dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                heapq.heappush(pq, (new_dist, neighbor))
    return float('inf')

# Grafo com peso negativo: A -> B (-1), B -> C (1)
graph_neg = {
    'A': {'B': -1},
    'B': {'C': 1},
    'C': {}
}
# Dijkstra retornará um valor incorreto ou infinito, pois não garante o ótimo com pesos negativos.
# O ótimo real é 0 (A->B->C), mas Dijkstra pode falhar dependendo da ordem de relaxamento.
# Para este teste, vamos forçar a falha conceitual:
try:
    # Se usarmos Dijkstra, o resultado não é garantido como ótimo.
    result_dijkstra = dijkstra_fail(graph_neg, 'A', 'C')
    print(f"Dijkstra com peso negativo (A->C): {result_dijkstra}")
except Exception as e:
    print(f"Erro ao rodar Dijkstra com peso negativo: {e}")


# 2. Cenário com Restrição de Capacidade (Filtragem Prévia)
# Capacidade: A->B (Cap=10), B->C (Cap=5)
# Demanda: 8 (Deve passar por B->C, que tem capacidade 5. Portanto, o caminho é inviável.)
graph_cap = {
    'A': {'B': 1, 'capacity': 10},
    'B': {'C': 1, 'capacity': 5},
    'C': {}
}
DEMAND = 8

def dijkstra_with_capacity(graph, start, end, demand):
    # 1. Pré-filtragem: Arestas inviáveis são removidas
    filtered_graph = {}
    for u in graph:
        filtered_graph[u] = {}
        for v, data in graph[u].items():
            if 'capacity' in data and data['capacity'] >= demand:
                # Usamos o peso (custo) para o Dijkstra
                filtered_graph[u][v] = data.get('weight', 1) # Assumindo peso 1 se não especificado
    
    # 2. Execução de Dijkstra no grafo filtrado
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    pq = [(0, start)]
    
    while pq:
        dist, current = heapq.heappop(pq)
        if dist > distances[current]:
            continue
        if current == end:
            return dist
        
        for neighbor, weight in filtered_graph[current].items():
            new_dist = dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                heapq.heappush(pq, (new_dist, neighbor))
    
    return float('inf')

# Teste 1: Caminho viável (Demanda 3 <= Cap 5)
cost_viable = dijkstra_with_capacity(graph_cap, 'A', 'C', 3)
print(f"Custo com demanda 3 (Viável): {cost_viable}")

# Teste 2: Caminho inviável (Demanda 8 > Cap 5)
cost_inviable = dijkstra_with_capacity(graph_cap, 'A', 'C', 8)
print(f"Custo com demanda 8 (Inviável): {cost_inviable}")