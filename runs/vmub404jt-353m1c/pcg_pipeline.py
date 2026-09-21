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
        # Cria grid vazio
        grid = [['.' for _ in range(w)] for _ in range(h)]
        
        # Posiciona Entrada (S) e Saída (E) em cantos opostos
        grid[0][0] = 'S'
        grid[h-1][w-1] = 'E'

        # Distribui obstáculos baseando-se na densidade e na seed
        num_obstacles = int(w * h * self.config.obstacle_density)
        placed = 0
        while placed < num_obstacles:
            rx = self.rng.randint(0, w - 1)
            ry = self.rng.randint(0, h - 1)
            if grid.ry[rx] == '.' and not (rx == 0 and ry == 0) and not (rx == w-1 and ry == h-1):
                # Nota: acesso correto à matriz grid[y][x]
                pass
            # Correção do acesso à matriz grid[y][x]
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
        start, end = None, None

        for y in range(h):
            for x in range(w):
                if grid[y][x] == 'S':
                    start = (x, y)
                elif grid[y][x] == 'E':
                    end = (x, y)

        if not start or not end:
            return False

        # BFS para encontrar caminho entre S e E
        queue = deque([start])
        visited = {start}
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) == end:
                return True

            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < w and 0 <= ny < h:
                    if grid[ny][nx] != '#' and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))

        return False

    @classmethod
    def validate(cls, grid: list[list[str]]) -> tuple[bool, str]:
        if not cls.is_connected(grid):
            return False, "Caminho entre Entrada e Saída bloqueado!"
        return True, "Layout Válido"

class PCGPipeline:
    """Orquestrador do pipeline: Seed -> PRNG -> Gerador -> Validador -> Output"""
    def __init__(self, config: PCGConfig):
        self.config = config

    def create_level(self, seed: int, max_attempts: int = 100) -> list[list[str]]:
        for attempt in range(max_attempts):
            # Se falhar na validação, derivamos uma nova seed de forma determinística
            current_seed = seed + attempt
            generator = LevelGenerator(current_seed, self.config)
            grid = generator.generate()
            
            is_valid, _ = LevelValidator.validate(grid)
            if is_valid:
                print(f"[Pipeline] Sucesso na seed base {seed} (tentativa {attempt})")
                return grid
                
        raise RuntimeError(f"Não foi possível gerar um nível válido para a seed {seed} após {max_attempts} tentativas.")

# --- EXPERIMENTO / TESTES ---
if __name__ == "__main__":
    config = PCGConfig(width=8, height=8, obstacle_density=0.25)
    pipeline = PCGPipeline(config)

    print("=== TESTE 1: Determinismo ===")
    level_a = pipeline.create_level(seed=42)
    level_b = pipeline.create_level(seed=42)
    assert level_a == level_b, "Falha no determinismo: mesma seed produziu layouts diferentes!"
    print("Sucesso: Mesma seed produziu exatamente o mesmo layout.")

    print("\n=== TESTE 2: Variabilidade por Seed ===")
    level_c = pipeline.create_level(seed=100)
    level_d = pipeline.create_level(seed=200)
    assert level_c != level_d, "Falha na variabilidade: seeds diferentes produziram o mesmo layout!"
    print("Sucesso: Seeds diferentes produziram layouts distintos.")

    print("\n=== TESTE 3: Conectividade Obrigatória (BFS) ===")
    for s in [10, 42, 999, 1337]:
        lvl = pipeline.create_level(seed=s)
        connected = LevelValidator.is_connected(lvl)
        assert connected, fingida conectividade na seed {s}!"
        print(f"Seed {s}: Conectividade S -> E garantida.")

    print("\n[+] Todos os testes executados com sucesso absoluto e código de saída 0.")