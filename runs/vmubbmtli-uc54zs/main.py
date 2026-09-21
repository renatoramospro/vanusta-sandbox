import time

class VisibilitySystem:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # 0: Unexplored, 1: Explored, 2: Visible
        self.grid = bytearray(width * height)
        # Lista para rastrear quais células foram alteradas para visibilidade (2)
        # Isso permite limpar apenas o que é necessário, evitando O(N)
        self.dirty_cells = []

    def update_visibility(self, agents, radius):
        """
        Atualiza a visibilidade dos agentes.
        Complexity: O(A * R^2) para atualização + O(Dirty) para limpeza.
        """
        # 1. Limpeza eficiente: Transformar o que era 'Visible' (2) em 'Explored' (1)
        # Usamos a lista de células que foram marcadas como visíveis no frame anterior
        for idx in self.dirty_cells:
            if self.grid[idx] == 2:
                self.grid[idx] = 1
        self.dirty_cells.clear()

        r_sq = radius * radius
        
        for ax_f, ay_f in agents:
            # CORREÇÃO 1: Suporte a Float (Conversão para int para uso em range/index)
            ax, ay = int(ax_f), int(ay_f)
            
            # Bounding box delimitado pelo raio
            x_min = max(0, ax - radius)
            x_max = min(self.width, ax + radius + 1)
            y_min = max(0, ay - radius)
            y_max = min(self.height, ay + radius + 1)
            
            for y in range(y_min, y_max):
                dy = y - ay
                dy_sq = dy * dy
                row_offset = y * self.width
                
                for x in range(x_min, x_max):
                    dx = x - ax
                    if dx * dx + dy_sq <= r_sq:
                        idx = row_offset + x
                        # Se a célula não era visível, marcamos para limpeza futura
                        if self.grid[idx] != 2:
                            self.grid[idx] = 2
                            self.dirty_cells.append(idx)

def run_test_suite():
    print("--- Iniciando Testes de Correção ---")
    
    # Teste 1: Coordenadas Float (Edge Case)
    print("Teste 1: Coordenadas Float...", end=" ")
    sys_float = VisibilitySystem(100, 100)
    try:
        # Agentes em posições não inteiras
        agents_float = [(10.5, 20.7), (50.9, 50.1)]
        sys_float.update_visibility(agents_float, 5)
        print("PASSOU (Sem TypeError)")
    except TypeError as e:
        print(f"FALHOU (TypeError: {e})")
        return 1

    # Teste 2: Performance em Mapa Grande (Adversarial - Evitando O(N))
    # Um mapa de 1000x1000 tem 1.000.000 de células. 
    # Varrer tudo (O(N)) levaria muito tempo.
    print("Teste 2: Performance em Mapa Grande (O(N) avoidance)...", end=" ")
    width, height = 1000, 1000
    sys_large = VisibilitySystem(width, height)
    num_agents = 100
    radius = 10
    agents = [(500.0, 500.0) for _ in range(num_agents)]

    # Warm-up
    sys_large.update_visibility(agents, radius)

    start = time.perf_counter()
    # Executa 10 frames para média
    for _ in range(10):
        sys_large.update_visibility(agents, radius)
    end = time.perf_counter()
    
    avg_time_ms = ((end - start) / 10) * 1000
    print(f"PASSOU (Média: {avg_time_ms:.4f} ms)")

    if avg_time_ms < 3.0:
        print("\nRESULTADO FINAL: Critério de <3ms ATENDIDO.")
    else:
        print(f"\nRESULTADO FINAL: Critério de <3ms NÃO ATENDIDO ({avg_time_ms:.4f} ms).")
        return 1

    return 0

if __name__ == "__main__":
    exit(run_test_suite())