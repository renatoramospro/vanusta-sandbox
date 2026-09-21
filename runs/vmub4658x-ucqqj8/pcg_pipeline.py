import random
from collections import deque

class PCGConfig:
    def __init__(self, width=10, height=10, obstacle_density=0.2):
        self.width = width
        self.height = height
        self.obstacle_density = obstacle_density

class LevelGenerator:
    """Responsável unicamente por gerar a estrutura bruta baseada na seed."""
    def __init__(self, seed: int, config: PCGConfig):
        self.seed = seed
        self.config = config
        self.rng = random.Random(seed)

    def generate(self) -> list[list[str]]:
        w, h = self.config.width, self.config.height
        grid = [['.' for _ in range(w)] for _ in range(h)]
        
        # Posiciona Entrada (S) e Saída (E)
        grid[0][0] = 'S'
        grid[h-1][w-1] = 'E'

        # Distribui obstáculos
        num_obstacles = int(w * h * self.config.obstacle_density)
        placed = 0
        # Limite de tentativas para evitar loop infinito em densidades impossíveis
        attempts = 0 
        while placed < num_obstacles and attempts < 100:
            attempts += 1
            rx = self.rng.randint(0, w - 1)
            ry = self.rng.randint(0, h - 1)
            
            # Não pode colocar obstáculo em cima de S ou E
            if grid[ry][rx] == '.' and not (rx == 0 and ry == 0) and not (rx == w-1 and ry == h-1):
                grid[ry][rx] = '#'
                placed += 1
        return grid

class LevelValidator:
    """Responsável unicamente por validar regras de layout e conectividade (BFS)."""
    @staticmethod
    def is_connected(grid: list[list[str]]) -> bool:
        h = len(grid)
        w = len(grid[0])
        start, end = (0, 0), (h-1, w-1)
        
        if grid[start[0]][start[1]] == '#' or grid[end[0]][end[1]] == '#':
            return False

        queue = deque([start])
        visited = {start}

        while queue:
            curr_y, curr_x = queue.popleft()
            if (curr_y, curr_x) == end:
                return True

            for dy, dx in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                ny, nx = curr_y + dy, curr_x + dx
                if 0 <= ny < h and 0 <= nx < w and \
                   grid[ny][nx] != '#' and (ny, nx) not in visited:
                    visited.add((ny, nx))
                    queue.append((ny, nx))
        return False

class PCGOrchestrator:
    """Coordena o pipeline: Seed -> Gerador -> Validador -> Output."""
    def __init__(self, config: PCGConfig):
        self.config = config

    def create_level(self, seed: int) -> list[list[str]]:
        current_seed = seed
        while True:
            gen = LevelGenerator(current_seed, self.config)
            grid = gen.generate()
            if LevelValidator.is_connected(grid):
                return grid
            # Se o layout for inválido, tentamos a próxima semente (re-roll)
            current_seed += 1

def run_experiments():
    config = PCGConfig(width=8, height=8, obstacle_density=0.25)
    orchestrator = PCGOrchestrator(config)

    print("=== TESTE 1: Determinismo ===")
    lvl_a = orchestrator.create_level(seed=42)
    lvl_b = orchestrator.create_level(seed=42)
    assert lvl_a == lvl_b, "Falha no determinismo: mesma seed produziu layouts diferentes!"
    print("Sucesso: Mesma seed produziu exatamente o mesmo layout.")

    print("\n=== TESTE 2: Variabilidade ===")
    lvl_c = orchestrator.create_level(seed=100)
    lvl_d = orchestrator.create_level(seed=200)
    assert lvl_c != lvl_d, "Falha na variabilidade: seeds diferentes produziram o mesmo layout!"
    print("Sucesso: Seeds diferentes produziram layouts distintos.")

    print("\n=== TESTE 3: Conectividade Obrigatória (BFS) ===")
    for s in [10, 42, 999, 1337]:
        lvl = orchestrator.create_level(seed=s)
        connected = LevelValidator.is_connected(lvl)
        assert connected, f"Falsa conectividade na seed {s}!"
        print(f"Seed {s}: Conectividade S -> E garantida.")

    print("\n=== TESTE 4: Ataque ao Equívoco Comum (Geração sem Validação) ===")
    # Tentamos gerar um nível com densidade altíssima sem o orquestrador
    high_density_config = PCGConfig(width=5, height=5, obstacle_density=0.7)
    bad_gen = LevelGenerator(seed=7, config=high_density_config)
    bad_lvl = bad_gen.generate()
    is_bad_connected = LevelValidator.is_connected(bad_lvl)
    
    if not is_bad_connected:
        print("Sucesso: O teste demonstrou que a geração bruta sem validação pode falhar.")
    else:
        # Se por sorte deu certo, tentamos outra seed para provar o ponto
        bad_gen_2 = LevelGenerator(seed=123, config=high_density_config)
        bad_lvl_2 = bad_gen_2.generate()
        if not LevelValidator.is_connected(bad_lvl_2):
            print("Sucesso: O teste demonstrou que a geração bruta sem validação pode falhar.")
        else:
            print("Aviso: Não conseguimos gerar um mapa inválido por sorte, mas o risco existe.")

    print("\n[+] Todos os testes executados com sucesso absoluto e código de saída 0.")

if __name__ == "__main__":
    run_experiments()