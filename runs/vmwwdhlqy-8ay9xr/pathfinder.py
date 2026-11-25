import heapq
import math
import random
import sys

# --- Configurações do Grid ---
# Ajustando para o critério de sucesso: 100x100, 20% obstáculos
GRID_SIZE = 100
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

def reconstruct_path(came_from, current):
    """Reconstrói o caminho do nó atual até a origem."""
    path = []
    while current in came_from:
        path.append(current)
        current = came_from[current]
    path.append(current) # Adiciona a origem
    return path[::-1]

def a_star_search(grid, start, goal):
    """Implementação do algoritmo A*."""
    rows, cols = len(grid), len(grid[0])
    
    # Validação de entrada (Correção obrigatória)
    if not (0 <= start[0] < rows and 0 <= start[1] < cols and 
            0 <= goal[0] < rows and 0 <= goal[1] < cols):
        print("Erro: Coordenadas de início ou destino fora dos limites do grid.")
        return None, 0, 0
    if grid[start[0]][start[1]] == 1 or grid[goal[0]][goal[1]] == 1:
        print("Erro: Início ou destino é um obstáculo.")
        return None, 0, 0
    if rows == 0 or cols == 0:
        print("Erro: Grid vazio.")
        return None, 0, 0

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
            path = reconstruct_path(came_from, goal)
            return path, g_score[goal], nodes_expanded

        r_curr, c_curr = current
        
        # Movimentos em 8 direções (ortogonal e diagonal)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                
                neighbor = (r_curr + dr, c_curr + dc)
                r_next, c_next = neighbor
                
                # Validação de limites e obstáculos
                if not (0 <= r_next < rows and 0 <= c_next < cols and grid[r_next][c_next] == 0):
                    continue
                
                # Custo de movimento: 1 para ortogonal, sqrt(2) para diagonal
                move_cost = 1.0 if abs(dr) + abs(dc) == 1 else math.sqrt(2)
                tentative_g_score = g_score[current] + move_cost

                # Se este caminho for melhor que o já conhecido
                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + heuristic_chebyshev(neighbor, goal)
                    
                    # Adiciona ou atualiza no open_set (heapq não suporta atualização direta, 
                    # então adicionamos a nova entrada e ignoramos a antiga quando for retirada)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
                    
    # Destino inalcançável
    return None, 0, nodes_expanded

# --- Execução do Experimento (Critério de Sucesso) ---
# Para garantir reprodutibilidade e testar o critério de sucesso, fixamos a semente.
random.seed(42) 
grid = generate_grid(GRID_SIZE, OBSTACLE_DENSITY)

# 1. Teste de caminho ótimo e eficiência (A* vs Dijkstra)
# Para comparar, precisamos de Dijkstra. Implementação simplificada de Dijkstra:
def dijkstra_search(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    
    g_score = {start: 0}
    open_set = [(0, start)] # (cost, node)
    came_from = {}
    nodes_expanded = 0

    while open_set:
        current_cost, current = heapq.heappop(open_set)
        nodes_expanded += 1

        if current_cost > g_score.get(current, float('inf')):
            continue
            
        if current == goal:
            path = reconstruct_path(came_from, goal)
            return path, current_cost, nodes_expanded

        r_curr, c_curr = current
        
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                
                neighbor = (r_curr + dr, c_curr + dc)
                r_next, c_next = neighbor
                
                if not (0 <= r_next < rows and 0 <= c_next < cols and grid[r_next][c_next] == 0):
                    continue
                
                move_cost = 1.0 if abs(dr) + abs(dc) == 1 else math.sqrt(2)
                tentative_g_score = g_score[current] + move_cost

                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    heapq.heappush(open_set, (tentative_g_score, neighbor))
                    
    return None, 0, nodes_expanded

# Execução
path_a_star, cost_a_star, expanded_a_star = a_star_search(grid, START, GOAL)
path_dijkstra, cost_dijkstra, expanded_dijkstra = dijkstra_search(grid, START, GOAL)

# 2. Teste de inalcançabilidade (Simulação de bloqueio total)
# Criar um grid onde o destino é inalcançável (ex: cercado por obstáculos)
grid_unreachable = generate_grid(50, 0.1)
# Bloquear o caminho entre (0,0) e (49,49)
for r in range(50):
    grid_unreachable[r][25] = 1
    grid_unreachable[r][26] = 1
grid_unreachable[START[0]][START[1]] = 0
grid_unreachable[GOAL[0]][GOAL[1]] = 0

path_unreachable, _, _ = a_star_search(grid_unreachable, START, GOAL)


# 3. Verificações Finais
is_optimal_check = abs(cost_a_star - cost_dijkstra) < 1e-6
is_more_efficient = expanded_a_star < expanded_dijkstra
is_unreachable_handled = path_unreachable is None

print("\n=========================================================")
print("--- Teste 1: 100x100, 20% Obstáculos (Critério de Sucesso) ---")
print(f"Rota A* encontrada: {path_a_star is not None}")
print(f"Rota Dijkstra encontrada: {path_dijkstra is not None}")
print(f"Custo A*: {cost_a_star:.2f} | Custo Dijkstra: {cost_dijkstra:.2f}")
print(f"A* é ótimo (Custo igual a Dijkstra): {is_optimal_check}")
print(f"A* é mais eficiente (Nós expandidos): {is_more_efficient} (A*={expanded_a_star}, Dijkstra={expanded_dijkstra})")
print(f"Resultado Teste 1: {'SUCESSO' if is_optimal_check and is_more_efficient else 'FALHA'}")

print("\n--- Teste 2: Destino Inalcançável ---")
print(f"Rota A* para destino inalcançável é None: {is_unreachable_handled}")
print(f"Resultado Teste 2: {'SUCESSO' if is_unreachable_handled else 'FALHA'}")
print("=========================================================")