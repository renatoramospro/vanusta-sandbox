import time
import math
import random

# --- CONFIGURAÇÕES ---
NUM_ENTITIES = 2000  # Usamos 2000 para o teste de comparação para não travar o ambiente, 
                     # mas o algoritmo de Grid escala para 10k+ facilmente.
WORLD_SIZE = 1000
GRID_CELL_SIZE = 50
PROXIMITY_THRESHOLD = 10

# --- ABORDAGEM 1: OOP INGUÍNA (O QUE NÃO FAZER) ---
class EntityOOP:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy

    def update(self):
        self.x += self.vx
        self.y += self.vy

def run_oop_brute_force(entities):
    start = time.time()
    # 1. Movimentação
    for e in entities:
        e.update()
    
    # 2. Detecção de Proximidade O(n^2)
    collisions = 0
    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            e1 = entities[i]
            e2 = entities[j]
            dist_sq = (e1.x - e2.x)**2 + (e1.y - e2.y)**2
            if dist_sq < PROXIMITY_THRESHOLD**2:
                collisions += 1
    
    end = time.time()
    return end - start, collisions

# --- ABORDAGEM 2: ECS + SPATIAL GRID (O QUE FAZER) ---
class ECS_Engine:
    def __init__(self, count):
        self.count = count
        # Componentes armazenados em arrays contíguos (simulando Data Locality)
        self.pos_x = [random.uniform(0, WORLD_SIZE) for _ in range(count)]
        self.pos_y = [random.uniform(0, WORLD_SIZE) for _ in range(count)]
        self.vel_x = [random.uniform(-1, 1) for _ in range(count)]
        self.vel_y = [random.uniform(-1, 1) for _ in range(count)]
        self.grid = {}

    def movement_system(self):
        for i in range(self.count):
            self.pos_x[i] += self.vel_x[i]
            self.pos_y[i] += self.vel_y[i]

    def update_grid(self):
        self.grid.clear()
        for i in range(self.count):
            cell_x = int(self.pos_x[i] // GRID_CELL_SIZE)
            cell_y = int(self.pos_y[i] // GRID_CELL_SIZE)
            cell_key = (cell_x, cell_y)
            if cell_key not in self.grid:
                self.grid[cell_key] = []
            self.grid[cell_key].append(i)

    def proximity_system(self):
        collisions = 0
        threshold_sq = PROXIMITY_THRESHOLD**2
        
        for i in range(self.count):
            cx = int(self.pos_x[i] // GRID_CELL_SIZE)
            cy = int(self.pos_y[i] // GRID_CELL_SIZE)
            
            # Checar célula atual e 8 vizinhas
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    neighbor_cell = (cx + dx, cy + dy)
                    if neighbor_cell in self.grid:
                        for other_idx in self.grid[neighbor_cell]:
                            if i < other_idx: # Evita duplicatas e auto-comparação
                                dist_sq = (self.pos_x[i] - self.pos_x[other_idx])**2 + \
                                          (self.pos_y[i] - self.pos_y[other_idx])**2
                                if dist_sq < threshold_sq:
                                    collisions += 1
        return collisions

    def run_frame(self):
        start = time.time()
        self.movement_system()
        self.update_grid()
        collisions = self.proximity_system()
        end = time.time()
        return end - start, collisions

# --- EXECUÇÃO DO TESTE ---
if __name__ == "__main__":
    print(f"--- Teste de Performance: {NUM_ENTITIES} Entidades ---")

    # Teste OOP
    oop_entities = [EntityOOP(random.uniform(0, WORLD_SIZE), random.uniform(0, WORLD_SIZE), 
                              random.uniform(-1, 1), random.uniform(-1, 1)) for _ in range(NUM_ENTITIES)]
    oop_time, oop_col = run_oop_brute_force(oop_entities)
    print(f"[OOP Brute Force] Tempo: {oop_time:.4f}s | Colisões: {oop_col}")

    # Teste ECS + Grid
    ecs = ECS_Engine(NUM_ENTITIES)
    ecs_time, ecs_col = ecs.run_frame()
    print(f"[ECS + Grid]      Tempo: {ecs_time:.4f}s | Colisões: {ecs_col}")

    # Verificação de escala
    speedup = oop_time / ecs_time
    print(f"\nGanho de performance: {speedup:.2f}x mais rápido")
    
    if ecs_time < 0.0166:
        print("RESULTADO: SUCESSO (Dentro dos 60 FPS)")
    else:
        print("RESULTADO: FALHA (Abaixo de 60 FPS)")

    # Validação de integridade
    assert oop_col == ecs_col, f"Erro de lógica! OOP: {oop_col}, ECS: {ecs_col}"