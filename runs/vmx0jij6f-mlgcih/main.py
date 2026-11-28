import time
import random
from collections import deque

# --- 1. Implementação com Lista de Adjacência (O(V+E)) ---
def build_adj_list(V, E):
    adj = {i: [] for i in range(V)}
    edges = set()
    while len(edges) < E:
        u = random.randint(0, V - 1)
        v = random.randint(0, V - 1)
        if u != v and tuple(sorted((u, v))) not in edges:
            adj[u].append(v)
            adj[v].append(u)
            edges.add(tuple(sorted((u, v))))
    return adj

def bfs_adj_list(V, adj, start_node):
    visited = [False] * V
    queue = deque([start_node])
    visited[start_node] = True
    count = 0
    while queue:
        u = queue.popleft()
        count += 1
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                queue.append(v)
    return count

# --- 2. Simulação com Matriz de Adjacência (O(V^2)) ---
# Nota: Para V=1000, V^2 = 1,000,000. A BFS em matriz requer iteração sobre todas as V colunas para cada V linha.
def bfs_matrix_simulation(V, adj_list, start_node):
    # Simula o custo de iteração O(V^2) sem alocar a matriz completa para simplicidade de teste
    # O custo real é V * V para checar vizinhos
    visited = [False] * V
    queue = deque([start_node])
    visited[start_node] = True
    count = 0
    
    while queue:
        u = queue.popleft()
        count += 1
        
        # Simulação do loop de vizinhos O(V) em vez de O(degree(u))
        for v in range(V):
            # Verifica se (u, v) é uma aresta (usando a lista de adjacência para verificar a existência)
            if v in adj_list[u] and not visited[v]:
                visited[v] = True
                queue.append(v)
    return count

# --- Teste e Medição ---
V_test = 1000
E_test = 2000
start_node = 0
NUM_RUNS = 10

# 1. Preparação do Grafo
adj_list = build_adj_list(V_test, E_test)

# 2. Medição Lista de Adjacência
times_adj = []
for _ in range(NUM_RUNS):
    start = time.perf_counter()
    bfs_adj_list(V_test, adj_list, start_node)
    end = time.perf_counter()
    times_adj.append(end - start)

avg_time_adj = sum(times_adj) / NUM_RUNS

# 3. Medição Matriz de Adjacência (Simulação de custo O(V^2))
times_matrix = []
for _ in range(NUM_RUNS):
    start = time.perf_counter()
    bfs_matrix_simulation(V_test, adj_list, start_node)
    end = time.perf_counter()
    times_matrix.append(end - start)

avg_time_matrix = sum(times_matrix) / NUM_RUNS

# 4. Resultados Observáveis
print(f"--- Teste em Grafo Esparso (V={V_test}, E={E_test}) ---")
print(f"Média de tempo (Lista de Adjacência O(V+E)): {avg_time_adj:.6f} segundos")
print(f"Média de tempo (Simulação Matriz O(V^2)): {avg_time_matrix:.6f} segundos")

# Verificação do critério de sucesso (Complexidade O(V+E) é demonstrada pela performance superior)
# Não podemos provar O(V+E) apenas com tempo, mas a performance deve ser muito melhor que O(V^2)
if avg_time_adj < avg_time_matrix * 0.1: # Espera-se uma diferença significativa
    print("\nSUCESSO: A performance da Lista de Adjacência é significativamente melhor que a simulação de Matriz de Adjacência para grafos esparsos.")
else:
    print("\nAVISO: A diferença de performance não foi drástica, mas o algoritmo O(V+E) foi implementado.")