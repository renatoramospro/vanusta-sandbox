import heapq

# Estrutura do Grafo: {Nó_Origem: {Nó_Destino: {'weight': W, 'capacity': C}}}
# Nota: O grafo deve ser consistente. A chave 'A' não pode ser duplicada.
graph_cap = {
    'A': {'B': {'weight': 1, 'capacity': 5}, 'C': {'weight': 5, 'capacity': 1}},
    'B': {'C': {'weight': 1, 'capacity': 5}}
}

# Função auxiliar para Dijkstra com restrição de capacidade
def dijkstra_with_capacity(graph, start, end, demand):
    # 1. Identificar todos os nós no grafo
    all_nodes = set(graph.keys())
    for neighbors in graph.values():
        all_nodes.update(neighbors.keys())
    
    # 2. Inicializar distâncias para TODOS os nós identificados
    distances = {node: float('inf') for node in all_nodes}
    
    if start not in distances or end not in distances:
        # Caso de erro se start ou end não estiverem no grafo
        return float('inf')

    distances[start] = 0
    pq = [(0, start)]
    
    while pq:
        dist, current = heapq.heappop(pq)
        
        if dist > distances[current]:
            continue
        
        if current == end:
            return dist
        
        # Iteração corrigida: vizinho é a chave, data é o dicionário de atributos
        if current in graph:
            for neighbor, data in graph[current].items():
                weight = data['weight']
                capacity = data['capacity']
                
                # Verificação de restrição de capacidade
                if capacity >= demand:
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

# Teste 3: Comparação com caminho direto (A->C, custo 5, Cap 1)
cost_direct_low_cap = dijkstra_with_capacity(graph_cap, 'A', 'C', 1)
print(f"Custo com demanda 1 (Viável, inclui direto): {cost_direct_low_cap}")