import heapq

# Estrutura do Grafo: {Nó_Origem: {Nó_Destino: {'weight': W, 'capacity': C}}}
graph_cap = {
    'A': {'B': {'weight': 1, 'capacity': 5}},
    'B': {'C': {'weight': 1, 'capacity': 5}},
    'A': {'C': {'weight': 5, 'capacity': 1}} # Adicionando aresta direta para teste
}

# Função auxiliar para Dijkstra com restrição de capacidade
def dijkstra_with_capacity(graph, start, end, demand):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    pq = [(0, start)]
    
    while pq:
        dist, current = heapq.heappop(pq)
        
        if dist > distances[current]:
            continue
        
        if current == end:
            return dist
        
        # Iteração corrigida: vizinho é a chave, data é o dicionário de atributos
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