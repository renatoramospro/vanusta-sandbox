import time

class Asset:
    def __init__(self, asset_id, size, priority=1):
        self.id = asset_id
        self.size = size
        self.priority = priority
        self.state = "UNLOADED"  # UNLOADED, LOADING, LOADED
        self.last_used_frame = 0

class StreamingManager:
    def __init__(self, memory_limit, load_radius, unload_radius, frame_budget_units):
        self.memory_limit = memory_limit
        self.load_radius = load_radius
        self.unload_radius = unload_radius
        self.frame_budget = frame_budget_units # Simula tempo de CPU disponível por frame
        
        self.assets = {}
        self.current_memory = 0
        self.frame_count = 0
        self.load_queue = []

    def add_asset(self, asset):
        self.assets[asset.id] = asset

    def update(self, player_pos):
        self.frame_count += 1
        work_done_this_frame = 0
        
        # 1. Detecção de Zonas (Streaming Logic)
        for asset_id, asset in self.assets.items():
            dist = abs(asset.id - player_pos) # Simplificação: ID é a posição no eixo X
            
            if dist <= self.load_radius and asset.state == "UNLOADED":
                asset.state = "LOADING"
                self.load_queue.append(asset)
            
            elif dist > self.unload_radius and asset.state == "LOADED":
                asset.state = "UNLOADED"
                self.current_memory -= asset.size
                # print(f"[Frame {self.frame_count}] Asset {asset.id} descarregado (Hysteresis)")

        # 2. Time-Slicing (Processamento da Fila)
        while self.load_queue and work_done_this_frame < self.frame_budget:
            asset = self.load_queue.pop(0)
            # Simula custo de CPU para carregar/descomprimir
            work_cost = 2 
            work_done_this_frame += work_cost
            
            # Verifica teto de memória antes de carregar
            if self.current_memory + asset.size <= self.memory_limit:
                asset.state = "LOADED"
                asset.last_used_frame = self.frame_count
                self.current_memory += asset.size
            else:
                # Política de Evicção Simples (LRU)
                self._evict_lru(asset.size)
                if self.current_memory + asset.size <= self.memory_limit:
                    asset.state = "LOADED"
                    self.current_memory += asset.size
                else:
                    asset.state = "UNLOADED" # Falhou em carregar
            
            # print(f"[Frame {self.frame_count}] Asset {asset.id} carregado. Mem: {self.current_memory}")

    def _evict_lru(self, needed_size):
        # Ordena assets carregados pelo frame de último uso (mais antigo primeiro)
        loaded_assets = sorted(
            [a for a in self.assets.values() if a.state == "LOADED"],
            key=lambda x: x.last_used_frame
        )
        
        for asset in loaded_assets:
            if self.current_memory + needed_size <= self.memory_limit:
                break
            asset.state = "UNLOADED"
            self.current_memory -= asset.size
            # print(f"[Frame {self.frame_count}] Evicção LRU: Asset {asset.id}")

def run_simulation(use_hysteresis):
    # Se não usar hysteresis, load_radius == unload_radius
    l_rad = 10
    u_rad = 20 if use_hysteresis else 10
    
    manager = StreamingManager(memory_limit=50, load_radius=l_rad, unload_radius=u_rad, frame_budget_units=3)
    
    # Criar assets em posições 10, 20, 30...
    for i in range(0, 100, 10):
        manager.add_asset(Asset(asset_id=i, size=20))

    print(f"\n--- Iniciando Simulação (Hysteresis={use_hysteresis}) ---")
    
    # Simular jogador oscilando na borda (posições 9.5, 10.5, 9.5, 10.5...)
    # Isso causa Thrashing se não houver Hysteresis
    path = [5, 9.5, 10.5, 9.5, 10.5, 15, 25, 24, 26, 25, 35]
    
    for pos in path:
        manager.update(pos)
        # Contagem de estados para verificar instabilidade
        loaded_count = len([a for a in manager.assets.values() if a.state == "LOADED"])
        loading_count = len([a for a in manager.assets.values() if a.state == "LOADING"])
        print(f"Pos: {pos:4} | Mem: {manager.current_memory:2} | Loaded: {loaded_count} | Loading: {loading_count}")

if __name__ == "__main__":
    # 1. Teste com erro: Sem Hysteresis (Causa Thrashing)
    run_simulation(use_hysteresis=False)
    
    # 2. Teste correto: Com Hysteresis (Estabilidade)
    run_simulation(use_hysteresis=True)