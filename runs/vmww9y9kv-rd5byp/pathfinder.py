import heapq
import math
import random

# --- Configurações do Grid ---
GRID_SIZE = 50
OBSTACLE_DENSITY = 0.2
START = (0, 0)
GOAL = (GRID_SIZE - 1, GRID_SIZE - 1)

def generate_grid(size, density):
    """Gera um grid 2D com obstáculos."""
    grid = [[0] * size for _ in range(size)]  # 0: livre, 1: obstáculo
    for r in range(size):
        for c in range(size):
            if random.random() < density:
                grid[r][c] = 1
    # Garantir que início e fim não sejam obstáculos
    grid[START[0]][START[1]] = 0
    grid[GOAL[0]][GOAL[1]] = 0
    return grid

def heuristic_chebyshev(a, b):
    """Heurística de Chebyshev (admissível e consistente para custo 1 em 8 direções)."""
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

def a_star_search(grid, start, goal):
    """Implementação do algoritmo A*."""
    rows, cols = len(grid), len(grid[0])
    
    # g_score: custo real do início ao nó atual
    g_score = {start: 0}
    # f_score: g_score + heurística
    f_score = {start: heuristic_chebyshev(start, goal)}
    
    # Priority Queue: (f_score, node)
    open_set = [(f_score[start], start)]
    
    came_from = {}
    nodes_expanded = 0

    while open_set:
        # Pega o nó com menor f_score
        current_f, current = heapq.heappop(open_set)
        nodes_expanded += 1

        if current == goal:
            # Reconstruir caminho
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path, nodes_expanded

        r, c = current
        
        # Vizinhos (8 direções: ortogonal e diagonal)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                
                neighbor = (r + dr, c + dc)
                nr, nc = neighbor
                
                # Checar limites e obstáculos
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                    
                    # Custo de movimento: 1 para ortogonal, sqrt(2) para diagonal
                    move_cost = 1.0 if abs(dr) + abs(dc) == 1 else math.sqrt(2)
                    tentative_g_score = g_score[current] + move_cost
                    
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        # Este é um caminho melhor
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + heuristic_chebyshev(neighbor, goal)
                        
                        # Adiciona ou atualiza no open_set (heapq lida com duplicatas, mas o menor será pego primeiro)
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        
    return None, nodes_expanded # Rota inalcançável

def dijkstra_search(grid, start, goal):
    """Implementação do algoritmo Dijkstra (A* com h=0)."""
    rows, cols = len(grid), len(grid[0])
    
    g_score = {start: 0}
    open_set = [(0, start)] # (g_score, node)
    came_from = {}
    nodes_expanded = 0

    while open_set:
        current_g, current = heapq.heappop(open_set)
        nodes_expanded += 1

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path, nodes_expanded

        r, c = current
        
        # Vizinhos (8 direções)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                
                neighbor = (r + dr, c + dc)
                nr, nc = neighbor
                
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                    move_cost = 1.0 if abs(dr) + abs(dc) == 1 else math.sqrt(2)
                    tentative_g_score = g_score[current] + move_cost
                    
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        heapq.heappush(open_set, (tentative_g_score, neighbor))
                        
    return None, nodes_expanded

# --- Execução e Verificação ---
grid = generate_grid(GRID_SIZE, OBSTACLE_DENSITY)

# 1. Executar A*
path_a_star, expanded_a_star = a_star_search(grid, START, GOAL)

# 2. Executar Dijkstra
path_dijkstra, expanded_dijkstra = dijkstra_search(grid, START, GOAL)

# 3. Verificações
is_optimal_a_star = (path_a_star is not None and 
                     (len(path_a_star) - 1) * 1.0 <= (len(path_dijkstra) - 1) * 1.0 if path_dijkstra else True)

# A otimalidade é garantida se A* for igual a Dijkstra (pois Dijkstra é ótimo)
# Para este teste, verificamos se o custo de A* é igual ao custo de Dijkstra
cost_a_star = 0
if path_a_star:
    for i in range(len(path_a_star) - 1):
        r1, c1 = path_a_star[i]
        r2, c2 = path_a_star[i+1]
        cost_a_star += 1.0 if abs(r1-r2) + abs(c1-c2) == 1 else math.sqrt(2)

cost_dijkstra = 0
if path_dijkstra:
    for i in range(len(path_dijkstra) - 1):
        r1, c1 = path_dijkstra[i]
        r2, c2 = path_dijkstra[i+1]
        cost_dijkstra += 1.0 if abs(r1-r2) + abs(c1-c2) == 1 else math.sqrt(2)

is_optimal_check = abs(cost_a_star - cost_dijkstra) < 1e-6

# Critério de sucesso: A* expande menos nós que Dijkstra
is_more_efficient = expanded_a_star < expanded_dijkstra

print(f"--- Resultados do Teste (Grid {GRID_SIZE}x{GRID_SIZE}, {OBSTACLE_DENSITY*100:.0f}% obstáculos) ---")
print(f"Rota A* encontrada: {path_a_star is not None}")
print(f"Rota Dijkstra encontrada: {path_dijkstra is not None}")
print(f"Custo A*: {cost_a_star:.2f} | Custo Dijkstra: {cost_dijkstra:.2f}")
print(f"A* é ótimo (Custo igual a Dijkstra): {is_optimal_check}")
print(f"A* é mais eficiente (Nós expandidos): {is_more_efficient} (A*={expanded_a_star}, Dijkstra={expanded_dijkstra})")
print(f"Resultado final: {'SUCESSO' if is_optimal_check and is_more_efficient else 'FALHA'}")