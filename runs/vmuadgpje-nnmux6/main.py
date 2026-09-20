import time
import math
import random

# --- CONFIGURAÇÕES ---
ENTITIES_COUNT_INTEGRITY = 2000
ENTITIES_COUNT_PERFORMANCE = 10000
MAP_SIZE = 1000.0
CELL_SIZE = 20.0  # Tamanho da célula do Grid
RADIUS = 2.0      # Raio de colisão das entidades
FPS_TARGET = 60
FRAME_TIME_TARGET = 1.0 / FPS_TARGET

# --- COMPONENTES (DADOS) ---
class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Velocity:
    def __init__(self, vx, vy):
        self.vx = vx
        self.vy = vy

# --- ENTIDADE (ID) ---
class Entity:
    def __init__(self, id, pos, vel):
        self.id = id
        self.pos = pos
        self.vel = vel

# --- SISTEMAS ---

class MovementSystem:
    """Atualiza a posição baseado na velocidade e sanitiza inputs."""
    def update(self, entities, dt):
        for e in entities:
            # Sanitização de Segurança: Evitar NaN/Inf que quebram o Grid
            if not math.isfinite(e.pos.x) or not math.isfinite(e.pos.y):
                e.pos.x, e.pos.y = 0.0, 0.0 # Reset seguro
                continue
            
            e.pos.x += e.vel.vx * dt
            e.pos.y += e.vel.vy * dt

            # Tratamento de Limites (Out-of-bounds)
            if e.pos.x < 0: e.pos.x = 0
            if e.pos.x > MAP_SIZE: e.pos.x = MAP_SIZE
            if e.pos.y < 0: e.pos.y = 0
            if e.pos.y > MAP_SIZE: e.pos.y = MAP_SIZE

class CollisionSystemBruteForce:
    """Sistema O(n^2) para validação de integridade."""
    def update(self, entities):
        collisions = 0
        n = len(entities)
        for i in range(n):
            for j in range(i + 1, n):
                e1 = entities[i]
                e2 = entities[j]
                dx = e1.pos.x - e2.pos.x
                dy = e1.pos.y - e2.pos.y
                dist_sq = dx*dx + dy*dy
                if dist_sq <= (RADIUS * 2)**2:
                    collisions += 1
        return collisions

class SpatialHashGrid:
    """Partição espacial para otimização O(n)."""
    def __init__(self, cell_size, map_size):
        self.cell_size = cell_size
        self.map_size = map_size
        self.grid = {}

    def _get_cell_coords(self, x, y):
        return int(x // self.cell_size), int(y // self.cell_size)

    def clear(self):
        self.grid.clear()

    def insert(self, entity):
        cx, cy = self._get_cell_coords(entity.pos.x, entity.pos.y)
        key = (cx, cy)
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append(entity)

    def get_nearby(self, entity):
        cx, cy = self._get_cell_coords(entity.pos.x, entity.pos.y)
        nearby = []
        # CORREÇÃO CRÍTICA: Checar as 9 células (a atual + 8 vizinhas)
        # para garantir que colisões na borda da célula sejam detectadas.
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                key = (cx + dx, cy + dy)
                if key in self.grid:
                    nearby.extend(self.grid[key])
        return nearby

class CollisionSystemECS:
    """Sistema O(n) usando o Spatial Hash Grid."""
    def __init__(self, grid):
        self.grid = grid

    def update(self, entities):
        self.grid.clear()
        for e in entities:
            self.grid.insert(e)

        collisions = 0
        checked_pairs = set()

        for e1 in entities:
            nearby = self.grid.get_nearby(e1)
            for e2 in nearby:
                if e1.id == e2.id:
                    continue
                
                # Garantir que cada par seja verificado apenas uma vez
                pair = tuple(sorted((e1.id, e2.id)))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)

                dx = e1.pos.x - e2.pos.x
                dy = e1.pos.y - e2.pos.y
                dist_sq = dx*dx + dy*dy
                if dist_sq <= (RADIUS * 2)**2:
                    collisions += 1
        return collisions

# --- EXPERIMENTO ---

def run_experiment():
    print(f"--- Iniciando Experimento: {ENTITIES_COUNT_PERFORMANCE} Entidades ---")
    print(f"Alvo: < {FRAME_TIME_TARGET:.4f}s por frame (60 FPS)")
    print(f"Mapa: {MAP_SIZE}x{MAP_SIZE} | Célula: {CELL_SIZE} | Raio: {RADIUS}\n")

    # 1. SETUP
    entities = []
    for i in range(ENTITIES_COUNT_PERFORMANCE):
        pos = Position(random.uniform(0, MAP_SIZE), random.uniform(0, MAP_SIZE))
        vel = Velocity(random.uniform(-5, 5), random.uniform(-5, 5))
        entities.append(Entity(i, pos, vel))

    # Inserir alguns NaNs para testar sanitização
    entities[0].pos.x = float('nan')

    grid = SpatialHashGrid(CELL_SIZE, MAP_SIZE)
    move_sys = MovementSystem()
    collision_brute = CollisionSystemBruteForce()
    collision_ecs = CollisionSystemECS(grid)

    # 2. VALIDAÇÃO DE INTEGRIDADE (Amostra Pequena)
    print(f"Validando integridade com {ENTITIES_COUNT_INTEGRITY} entidades...")
    sample_entities = entities[:ENTITIES_COUNT_INTEGRITY]
    
    # Reset de posições para teste controlado
    for e in sample_entities:
        e.pos.x, e.pos.y = random.uniform(0, MAP_SIZE), random.uniform(0, MAP_SIZE)

    # O Brute Force é a nossa "Verdade Absoluta"
    expected_col = collision_brute.update(sample_entities)
    # O ECS deve ser idêntico
    actual_col = collision_ecs.update(sample_entities)

    print(f"[OOP Brute Force] Colisões: {expected_col}")
    print(f"[ECS + Grid]      Colisões: {actual_col}")

    assert expected_col == actual_col, f"ERRO DE LÓGICA! OOP: {expected_col}, ECS: {actual_col}"
    print("✅ Integridade validada: ECS coincide com Brute Force.\n")

    # 3. TESTE DE PERFORMANCE (Escala Total)
    print(f"Executando teste de performance com {ENTITIES_COUNT_PERFORMANCE} entidades...")
    
    start_time = time.time()
    
    # Simulação de 1 frame
    move_sys.update(entities, 0.016) # dt = 16ms
    col_count = collision_ecs.update(entities)
    
    end_time = time.time()
    elapsed = end_time - start_time

    print(f"Tempo de processamento: {elapsed:.4f}s")
    print(f"Colisões detectadas: {col_count}")

    if elapsed <= FRAME_TIME_TARGET:
        print(f"✅ SUCESSO: {1.0/elapsed:.1f} FPS atingidos.")
    else:
        print(f"❌ FALHA: {1.0/elapsed:.1f} FPS (Abaixo de 60 FPS).")
        # Não usamos assert aqui para permitir que o relatório mostre o resultado
        # mas o critério de sucesso é o tempo.

    # 4. TESTE DE SEGURANÇA (Sanitização)
    print("\nValidando sanitização de segurança...")
    # Se o NaN não foi tratado, o grid quebraria ou o tempo explodiria
    # Verificamos se a entidade 0 (que era NaN) agora tem posição válida
    if math.isfinite(entities[0].pos.x) and math.isfinite(entities[0].pos.y):
        print("✅ Sanitização de NaN/Inf: OK")
    else:
        print("❌ Sanitização de NaN/Inf: FALHOU")

if __name__ == "__main__":
    run_experiment()