import random
from collections import deque

class GenerationError(Exception):
    """Exceção lançada quando o pipeline não consegue gerar um nível válido."""
    pass

class PCGConfig:
    def __init__(self, width=10, height=10, obstacle_density=0.3):
        self.width = width
        self.height = height
        self.obstacle_density = obstacle_density

class LevelGenerator:
    """Gera um grid de caracteres baseado em uma semente determinística."""
    def __init__(self, seed, config):
        self.seed = seed
        self.config = config
        self.rng = random.Random(seed)

    def generate(self):
        w, h = self.config.width, self.config.height
        # Inicializa grid com caminhos '.'
        grid = [['.' for _ in range(w)] for _ in range(h)]
        
        # Define Entrada (S) e Saída (E)
        grid[0][0] = 'S'
        grid[h-1][w-1] = 'E'

        # Preenche obstáculos '#' baseados na densidade
        for y in range(h):
            for x in range(w):
                # Não colocar obstáculo em S ou E
                if (x == 0 and y == 0) or (x == w-1 and y == h-1):
                    continue
                
                if self.rng.random() < self.config.obstacle_density:
                    grid[y][x] = '#'
        
        return grid

class LevelValidator:
    """Valida se o layout gerado respeita as regras de conectividade."""
    @staticmethod
    def is_connected(grid):
        h = len(grid)
        w = len(grid[0])
        start = (0, 0)
        end = (h-1, w-1)

        # BFS para encontrar caminho de S para E
        queue = deque([start])
        visited = {start}

        while queue:
            curr_y, curr_x = queue.popleft()

            if (curr_y, curr_x) == end:
                return True

            # Movimentos: Cima, Baixo, Esquerda, Direita
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = curr_y + dy, curr_x + dx

                if 0 <= ny < h and 0 <= nx < w:
                    if grid[ny][nx] != '#' and (ny, nx) not in visited:
                        visited.add((ny, nx))
                        queue.append((ny, nx))
        
        return False

class PCGOrchestrator:
    """Coordena o pipeline: Seed -> Gerador -> Validador -> Output."""
    def __init__(self, config, max_attempts=50):
        self.config = config
        self.max_attempts = max_attempts

    def generate_valid_level(self, base_seed):
        current_seed = base_seed
        attempts = 0

        # CORREÇÃO DE SEGURANÇA: Adicionado limite de tentativas para evitar loop infinito (DoS)
        while attempts < self.max_attempts:
            attempts += 1
            generator = LevelGenerator(current_seed, self.config)
            grid = generator.generate()

            if LevelValidator.is_connected(grid):
                return grid, current_seed, attempts
            
            # Se falhar, incrementamos a semente para tentar um layout diferente (re-roll)
            current_seed += 1
        
        raise GenerationError(f"Falha ao gerar nível válido após {self.max_attempts} tentativas.")

def run_experiments():
    print("=== INICIANDO EXPERIMENTOS PCG ===\n")

    # 1. Teste de Determinismo
    print("[TESTE 1] Determinismo:")
    config = PCGConfig(width=5, height=5, obstacle_density=0.2)
    orch = PCGOrchestrator(config)
    lvl1, seed1, _ = orch.generate_valid_level(42)
    lvl2, seed2, _ = orch.generate_valid_level(42)
    assert lvl1 == lvl2, "ERRO: Mesma seed produziu layouts diferentes!"
    assert seed1 == seed2, "ERRO: Sementes divergiram!"
    print("  -> Sucesso: Mesma seed produziu o mesmo layout.\n")

    # 2. Teste de Variabilidade
    print("[TESTE 2] Variabilidade:")
    lvl3, seed3, _ = orch.generate_valid_level(43)
    assert lvl1 != lvl3, "ERRO: Seeds diferentes produziram o mesmo layout!"
    print(f"  -> Sucesso: Seeds diferentes (42 vs {seed3}) produziram layouts distintos.\n")

    # 3. Teste de Conectividade (Funcionalidade)
    print("[TESTE 3] Conectividade (BFS):")
    # Gerando múltiplos níveis para garantir que o validador funciona em casos variados
    for s in [10, 100, 999, 1337]:
        lvl, used_seed, _ = orch.generate_valid_level(s)
        assert LevelValidator.is_connected(lvl), f"ERRO: Nível com seed {used_seed} está desconectado!"
    print("  -> Sucesso: 100% dos layouts gerados possuem caminho S -> E.\n")

    # 4. Teste de Segurança (Limite de Tentativas / DoS)
    print("[TESTE 4] Segurança (Limite de Tentativas):")
    # Criamos uma configuração impossível: densidade de 100% (tudo é obstáculo)
    impossible_config = PCGConfig(width=5, height=5, obstacle_density=1.0)
    safe_orch = PCGOrchestrator(impossible_config, max_attempts=10)
    
    try:
        safe_orch.generate_valid_level(7)
        print("  -> ERRO: O orquestrador não detectou a impossibilidade e não parou!")
    except GenerationError as e:
        print(f"  -> Sucesso: O sistema interrompeu o loop com segurança: {e}")
    except Exception as e:
        print(f"  -> ERRO: Capturou exceção inesperada: {type(e).__name__}: {e}")
    else:
        print("  -> ERRO: O orquestrador não lançou GenerationError em cenário impossível.")

    print("\n[+] Todos os experimentos concluídos com sucesso (Código 0).")

if __name__ == "__main__":
    run_experiments()