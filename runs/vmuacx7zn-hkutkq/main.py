import time
import math
import random

# --- CONFIGURAÇÕES ---
NUM_ENTITIES = 10000
WORLD_SIZE = 1000.0
ENTITY_RADIUS = 2.0
GRID_CELL_SIZE = 10.0  # Deve ser proporcional ao raio de detecção
TARGET_FPS = 60
FRAME_TIME_LIMIT = 1.0 / TARGET_FPS

class ECS_Engine:
    """
    Implementação de um ECS minimalista focado em Data Locality.
    Os componentes são armazenados em arrays (listas de floats) para simular 
    o layout de memória contíguo.
    """
    def __init__(self, count):
        self.count = count
        # Componentes: Arrays de dados (Data Locality)
        self.pos_x = [random.uniform(0, WORLD_SIZE) for _ in range(count)]
        self.pos_y = [random.uniform(0, WORLD_SIZE) for _ in range(count)]
        self.vel_x = [random.uniform(-1, 1) for _ in range(count)]
        self.vel_y = [random.uniform(-1, 1) for _ in range(count)]
        
        # Estrutura de Partição Espacial (Spatial Hash Grid)
        self.grid = {}

    def movement_system(self):
        """Atualiza posições baseado na velocidade."""
        for i in range(self.count):
            self.pos_x[i] = (self.pos_x[i] + self.vel_x[i]) % WORLD_SIZE
            self.pos_y[i] = (self.pos_y[i] + self.vel_y[i]) % WORLD_SIZE

    def update_grid(self):
        """Reconstrói o Spatial Hash Grid."""
        self.grid = {}
        for i in range(self.count):
            # Mapeia coordenada para chave da célula (inteiro)
            cell_x = int(self.pos_x[i] // GRID_CELL_SIZE)
            cell_y = int(self.pos_y[i] // GRID_CELL_SIZE)
            key = (cell_x, cell_y)
            
            if key not in self.grid:
                self.grid[key] = []
            self.grid[key].append(i)

    def proximity_system(self):
        """Detecta colisões usando o Grid para evitar O(n^2)."""
        collisions = 0
        diameter_sq = (ENTITY_RADIUS * 2) ** 2
        
        # Para cada entidade, checamos apenas sua célula e as 8 vizinhas
        for i in range(self.count):
            cx = int(self.pos_x[i] // GRID_CELL_SIZE)
            cy = int(self.pos_y[i] // GRID_CELL_SIZE)
            
            # Checar células vizinhas (incluindo a atual)
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    neighbor_key = (cx + dx, cy + dy)
                    if neighbor_key in self.grid:
                        for other_idx in self.grid[neighbor_key]:
                            # Evita comparar a entidade com ela mesma e evita contagem dupla
                            # Usamos i < other_idx para garantir que cada par seja contado uma única vez
                            if i < other_idx:
                                dist_sq = (self.pos_x[i] - self.pos_x[other_idx])**2 + \
                                          (self.pos_y[i] - self.pos_y[other_idx])**2
                                if dist_sq <= diameter_sq:
                                    collisions += 1
        return collisions

    def run_frame(self):
        start = time.perf_counter()
        self.movement_system()
        self.update_grid()
        cols = self.proximity_system()
        end = time.perf_counter()
        return (end - start), cols

def run_oop_brute_force(entities):
    """
    Implementação OOP tradicional para comparação (O(n^2)).
    Cada entidade é um objeto independente.
    """
    start = time.perf_counter()
    collisions = 0
    diameter_sq = (ENTITY_RADIUS * 2) ** 2
    n = len(entities)
    
    for i in range(n):
        e1 = entities[i]
        # Atualiza posição (simulando o sistema de movimento)
        e1['x'] = (e1['x'] + e1['vx']) % WORLD_SIZE
        e1['y'] = (e1['y'] + e1['vy']) % WORLD_SIZE
        
        for j in range(i + 1, n):
            e2 = entities[j]
            dist_sq = (e1['x'] - e2['x'])**2 + (e1['y'] - e2['y'])**2
            if dist_sq <= diameter_sq:
                collisions += 1
                
    end = time.perf_counter()
    return (end - start), collisions

def main():
    print(f"--- Iniciando Experimento: {NUM_ENTITIES} Entidades ---")
    print(f"Alvo: < {FRAME_TIME_LIMIT:.4f}s por frame (60 FPS)\n")

    # 1. Preparação de dados para OOP
    oop_entities = []
    for _ in range(NUM_ENTITIES):
        oop_entities.append({
            'x': random.uniform(0, WORLD_SIZE),
            'y': random.uniform(0, WORLD_SIZE),
            'vx': random.uniform(-1, 1),
            'vy': random.uniform(-1, 1)
        })

    # 2. Preparação de dados para ECS
    ecs = ECS_Engine(NUM_ENTITIES)
    # Sincronizar posições iniciais para garantir comparação justa
    for i in range(NUM_ENTITIES):
        ecs.pos_x[i] = oop_entities[i]['x']
        ecs.pos_y[i] = oop_entities[i]['y']
        ecs.vel_x[i] = oop_entities[i]['vx']
        ecs.vel_y[i] = oop_entities[i]['vy']

    # --- TESTE OOP (Apenas para escala pequena, pois 10k é inviável) ---
    # Se NUM_ENTITIES for muito grande, o OOP vai demorar minutos. 
    # Vamos rodar o OOP com uma amostra menor para validar a lógica de colisão.
    SAMPLE_SIZE = min(NUM_ENTITIES, 2000)
    print(f"Validando lógica com amostra de {SAMPLE_SIZE} entidades...")
    
    sample_oop = oop_entities[:SAMPLE_SIZE]
    # Para o ECS, precisamos de uma instância que contenha apenas a amostra para o assert
    sample_ecs = ECS_Engine(SAMPLE_SIZE)
    for i in range(SAMPLE_SIZE):
        sample_ecs.pos_x[i] = sample_oop[i]['x']
        sample_ecs.pos_y[i] = sample_oop[i]['y']
        sample_ecs.vel_x[i] = sample_oop[i]['vx']
        sample_ecs.vel_y[i] = sample_oop[i]['vy']

    # Execução da amostra
    # Nota: O OOP aqui já faz o movimento dentro do loop para simular um frame completo
    oop_time, oop_col = run_oop_brute_force(sample_oop)
    # O ECS precisa rodar o frame completo (movimento + grid + proximidade)
    ecs_sample_time, ecs_col = sample_ecs.run_frame()

    print(f"[OOP Brute Force] Tempo: {oop_time:.4f}s | Colisões: {oop_col}")
    print(f"[ECS + Grid]      Tempo: {ecs_sample_time:.4f}s | Colisões: {ecs_col}")

    # Validação de Integridade (O ponto que falhou anteriormente)
    assert oop_col == ecs_col, f"ERRO DE LÓGICA! OOP: {oop_col}, ECS: {ecs_col}"
    print("✅ Integridade de dados confirmada (Colisões idênticas).")

    # --- TESTE DE ESCALA REAL (10.000 Entidades) ---
    print(f"\nTestando escala real: {NUM_ENTITIES} entidades...")
    ecs_full_time, ecs_full_col = ecs.run_frame()
    
    print(f"[ECS Full Scale]  Tempo: {ecs_full_time:.4f}s | Colisões: {ecs_full_col}")
    
    if ecs_full_time <= FRAME_TIME_LIMIT:
        print(f"✅ SUCESSO: {1/ecs_full_time:.1f} FPS atingidos.")
    else:
        print(f"❌ FALHA: {1/ecs_full_time:.1f} FPS (Abaixo de 60).")

    # Verificação final do critério de sucesso
    assert ecs_full_time <= FRAME_TIME_LIMIT, "Não atingiu 60 FPS"

if __name__ == "__main__":
    main()