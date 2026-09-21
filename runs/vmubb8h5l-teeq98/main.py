import time
import math

class VisibilitySystem:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # 0: Unexplored, 1: Explored, 2: Visible
        self.grid = [0] * (width * height)

    def get_index(self, x, y):
        return y * self.width + x

    def update_brute_force(self, agents):
        """
        Equívoco Comum: Cada agente percorre TODAS as células do mapa.
        Complexidade: O(Agentes * Células)
        """
        # Resetamos o que era visível para explorado (simulação simplificada)
        for i in range(len(self.grid)):
            if self.grid[i] == 2:
                self.grid[i] = 1
        
        for agent_x, agent_y, radius in agents:
            for y in range(self.height):
                for x in range(self.width):
                    dist_sq = (x - agent_x)**2 + (y - agent_y)**2
                    if dist_sq <= radius**2:
                        self.grid[self.get_index(x, y)] = 2

    def update_spatial(self, agents):
        """
        Abordagem Eficiente: Cada agente percorre apenas seu Bounding Box.
        Complexidade: O(Agentes * Área_de_Visão)
        """
        # Resetamos o que era visível para explorado
        for i in range(len(self.grid)):
            if self.grid[i] == 2:
                self.grid[i] = 1

        for agent_x, agent_y, radius in agents:
            # Definimos os limites do Bounding Box (Spatial Partitioning simplificado)
            x_min = max(0, int(agent_x - radius))
            x_max = min(self.width - 1, int(agent_x + radius))
            y_min = max(0, int(agent_y - radius))
            y_max = min(self.height - 1, int(agent_y + radius))

            r_sq = radius**2
            for y in range(y_min, y_max + 1):
                for x in range(x_min, x_max + 1):
                    dist_sq = (x - agent_x)**2 + (y - agent_y)**2
                    if dist_sq <= r_sq:
                        self.grid[self.get_index(x, y)] = 2

def run_benchmark():
    WIDTH, HEIGHT = 100, 100
    NUM_AGENTS = 100
    RADIUS = 10
    
    # Dados sintéticos: 100 agentes em posições aleatórias
    import random
    random.seed(42)
    agents = []
    for _ in range(NUM_AGENTS):
        agents.append((
            random.randint(0, WIDTH-1),
            random.randint(0, HEIGHT-1),
            RADIUS
        ))

    print(f"--- Benchmark: {NUM_AGENTS} agentes | Mapa: {WIDTH}x{HEIGHT} | Raio: {RADIUS} ---")

    # Teste 1: Brute Force
    sys_brute = VisibilitySystem(WIDTH, HEIGHT)
    start = time.perf_counter()
    sys_brute.update_brute_force(agents)
    end = time.perf_counter()
    brute_time = (end - start) * 1000
    print(f"Brute Force: {brute_time:.2f} ms")

    # Teste 2: Spatial (Bounding Box)
    sys_spatial = VisibilitySystem(WIDTH, HEIGHT)
    start = time.perf_counter()
    sys_spatial.update_spatial(agents)
    end = time.perf_counter()
    spatial_time = (end - start) * 1000
    print(f"Spatial (Bounding Box): {spatial_time:.2f} ms")

    # Validação de resultado
    assert sys_brute.grid == sys_spatial.grid, "ERRO: Os resultados de visibilidade divergem!"
    
    speedup = brute_time / spatial_time
    print(f"\nGanho de performance: {speedup:.1f}x mais rápido")
    
    # Verificação do critério de sucesso (< 3ms)
    if spatial_time < 3.0:
        print("RESULTADO: Critério de performance ATENDIDO.")
    else:
        print("RESULTADO: Critério de performance NÃO ATENDIDO.")

if __name__ == "__main__":
    run_benchmark()