import time

class VisibilitySystem:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = bytearray(width * height) # bytearray é mais eficiente que list

    def update_spatial(self, agents, radius):
        # Limpa apenas a camada de visibilidade (0: Unexplored, 1: Explored, 2: Visible)
        # Em um sistema real, o 'Explored' seria persistido.
        for i in range(len(self.grid)):
            if self.grid[i] == 2: self.grid[i] = 1
            
        r_sq = radius * radius
        for ax, ay in agents:
            # Bounding box delimitado pelo raio
            x_min, x_max = max(0, ax - radius), min(self.width, ax + radius + 1)
            y_min, y_max = max(0, ay - radius), min(self.height, ay + radius + 1)
            
            for y in range(y_min, y_max):
                dy = y - ay
                dy_sq = dy * dy
                row_offset = y * self.width
                for x in range(x_min, x_max):
                    dx = x - ax
                    if dx * dx + dy_sq <= r_sq:
                        self.grid[row_offset + x] = 2

def run_benchmark():
    width, height = 100, 100
    num_agents = 100
    radius = 10
    agents = [(50, 50) for _ in range(num_agents)]
    
    sys = VisibilitySystem(width, height)
    
    # Warm-up
    sys.update_spatial(agents, radius)
    
    # Medição
    start = time.perf_counter()
    sys.update_spatial(agents, radius)
    end = time.perf_counter()
    
    spatial_time = (end - start) * 1000
    print(f"Spatial (Optimized): {spatial_time:.4f} ms")
    
    if spatial_time < 3.0:
        print("RESULTADO: Critério de performance ATENDIDO.")
    else:
        print("RESULTADO: Critério de performance NÃO ATENDIDO.")

if __name__ == "__main__":
    run_benchmark()