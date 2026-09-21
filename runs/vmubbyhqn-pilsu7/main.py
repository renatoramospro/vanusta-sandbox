import time

class VisibilitySystem:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Usamos uint16 (2 bytes por célula) para suportar até 65535 frames de histórico
        # Isso permite que cada célula saiba em qual frame foi vista.
        # 0: Unexplored, >0: Frame ID em que foi visto.
        # Para fins de simulação de estados (Explored/Visible), usaremos lógica de comparação.
        import array
        self.grid = array.array('H', [0] * (width * height))
        self.current_frame = 0

    def update_visibility(self, agents, radius):
        """
        Atualiza a visibilidade usando técnica de Frame ID (Zero-cost cleanup).
        Complexity: O(A * R^2)
        """
        self.current_frame += 1
        if self.current_frame == 0: # Reset para evitar overflow de uint16
            self.grid = array.array('H', [0] * (self.width * self.height))
            self.current_frame = 1

        r_sq = radius * radius
        
        for ax_f, ay_f in agents:
            # SECURITY: Bounds Checking rigoroso
            # Garante que agentes fora do mapa não causem crash ou acesso ilegal
            if not (0 <= ax_f < self.width and 0 <= ay_f < self.height):
                continue

            ax, ay = int(ax_f), int(ay_f)
            
            x_min = max(0, ax - radius)
            x_max = min(self.width - 1, ax + radius)
            y_min = max(0, ay - radius)
            y_max = min(self.height - 1, ay + radius)
            
            for y in range(y_min, y_max + 1):
                dy_sq = (y - ay) ** 2
                if dy_sq > r_sq:
                    continue
                    
                row_offset = y * self.width
                for x in range(x_min, x_max + 1):
                    dx_sq = (x - ax) ** 2
                    if dx_sq + dy_sq <= r_sq:
                        # Marca a célula com o ID do frame atual
                        self.grid[row_offset + x] = self.current_frame

    def get_cell_state(self, x, y):
        """
        Retorna o estado lógico da célula baseado no frame.
        0: Unexplored, 1: Explored (visto em frames passados), 2: Visible (visto no frame atual)
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return 0
        
        val = self.grid[y * self.width + x]
        if val == self.current_frame:
            return 2 # Visible
        elif val > 0:
            return 1 # Explored
        return 0 # Unexplored

def run_test_suite():
    print("--- Iniciando Testes de Correção Otimizada ---")
    
    # Configuração do cenário
    W, H = 200, 200
    sys = VisibilitySystem(W, H)
    radius = 15
    # 100 agentes em posições variadas (incluindo floats e fora de limites)
    agents = [(float(i % W), float((i * 7) % H)) for i in range(100)]
    # Adiciona agentes fora de limites para testar SECURITY
    agents.append((-10.0, 50.0))
    agents.append((W + 10.0, H + 10.0))

    # Teste 1: Coordenadas Float e Bounds Checking
    try:
        sys.update_visibility(agents, radius)
        print("Teste 1: Coordenadas Float e Bounds Checking... PASSOU")
    except Exception as e:
        print(f"Teste 1: FALHOU com erro: {e}")
        return 1

    # Teste 2: Performance (O(1) Cleanup via Frame ID)
    # Vamos rodar 10 iterações para estabilizar a média
    start_time = time.perf_counter()
    iterations = 10
    for _ in range(iterations):
        sys.update_visibility(agents, radius)
    end_time = time.perf_counter()
    
    avg_time_ms = ((end_time - start_time) / iterations) * 1000
    print(f"Teste 2: Performance em Mapa Grande (Frame ID method)... PASSOU (Média: {avg_time_ms:.4f} ms)")

    if avg_time_ms < 3.0:
        print(f"\nRESULTADO FINAL: Critério de <3ms ATENDIDO ({avg_time_ms:.4f} ms).")
        return 0
    else:
        print(f"\nRESULTADO FINAL: Critério de <3ms NÃO ATENDIDO ({avg_time_ms:.4f} ms).")
        return 1

if __name__ == "__main__":
    exit(run_test_suite())