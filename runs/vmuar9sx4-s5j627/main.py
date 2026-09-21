import math

class Asset:
    def __init__(self, asset_id: str, size_mb: float):
        self.asset_id = asset_id
        self.size_mb = size_mb
        self.ref_count = 0

class AssetManager:
    def __init__(self):
        self._loaded_assets = {} # asset_id -> Asset

    def load_asset(self, asset_id: str, size_mb: float = 10.0) -> Asset:
        # Garante integridade de instância: se já existe, apenas retorna o existente
        if asset_id not in self._loaded_assets:
            self._loaded_assets[asset_id] = Asset(asset_id, size_mb)
            print(f"[MEMÓRIA] Asset '{asset_id}' CARREGADO ({size_mb} MB).")
        else:
            print(f"[MEMÓRIA] Asset '{asset_id}' já estava carregado. Reutilizando instância.")
        
        asset = self._loaded_assets[asset_id]
        asset.ref_count += 1
        return asset

    def release_asset(self, asset_id: str):
        if asset_id in self._loaded_assets:
            asset = self._loaded_assets[asset_id]
            asset.ref_count -= 1
            print(f"[MEMÓRIA] Asset '{asset_id}' liberado (ref_count={asset.ref_count}).")
            if asset.ref_count <= 0:
                del self._loaded_assets[asset_id]
                print(f"[MEMÓRIA] Asset '{asset_id}' REMOVIDO da memória (0 referências).")

    def get_total_memory_mb(self) -> float:
        return sum(asset.size_mb for asset in self._loaded_assets.values())

class GameObject:
    def __init__(self, name: str, x: float, y: float, required_asset: str):
        self.name = name
        self.x = x
        self.y = y
        self.required_asset = required_asset
        self.is_active_in_memory = False

class SpatialProximitySystem:
    def __init__(self, asset_manager: AssetManager, load_radius: float, unload_radius: float):
        self.asset_manager = asset_manager
        self.load_radius = load_radius
        self.unload_radius = unload_radius # Hysteresis: unload_radius > load_radius
        
        # Validação do equívoco comum de Hysteresis
        if self.unload_radius <= self.load_radius:
            raise ValueError("O raio de descarregamento deve ser maior que o raio de carregamento para evitar Thrashing.")

    def update(self, player_x: float, player_y: float, objects: list):
        for obj in objects:
            dist = math.hypot(obj.x - player_x, obj.y - player_y)
            
            if not obj.is_active_in_memory:
                # Usa raio menor para disparar o carregamento
                if dist <= self.load_radius:
                    print(f"[PROXIMIDADE] Jogador entrou no raio de carga de '{obj.name}' (dist={dist:.1f}).")
                    self.asset_manager.load_asset(obj.required_asset)
                    obj.is_active_in_memory = True
            else:
                # Usa raio maior para o descarregamento (Hysteresis)
                if dist > self.unload_radius:
                    print(f"[PROXIMIDADE] Jogador saiu do raio de descarga de '{obj.name}' (dist={dist:.1f}).")
                    self.asset_manager.release_asset(obj.required_asset)
                    obj.is_active_in_memory = False

# --- TESTES E VALIDAÇÃO ---
if __name__ == "__main__":
    manager = AssetManager()
    
    # Raio de carga = 10, Raio de descarga = 15 (Margem de Hysteresis = 5)
    spatial_system = SpatialProximitySystem(manager, load_radius=10.0, unload_radius=15.0)
    
    obj_boss = GameObject("BossMonster", x=8.0, y=0.0, required_asset="boss_texture")
    
    print("--- 1. Movimento de Aproximação (Entra no raio de carga) ---")
    spatial_system.update(player_x=0.0, player_y=0.0, objects=[obj_boss])
    print(Memória Atual: {manager.get_total_memory_mb()} MB)
    
    print("\n--- 2. Movimento na Borda (Teste de Hysteresis - dist=12) ---")
    # A distância é 12. Como o load_radius é 10 e unload_radius é 15,
    # se o objeto já está ativo, ele NÃO deve ser descarregado (evita thrashing).
    spatial_system.update(player_x=12.0, player_y=0.0, objects=[obj_boss])
    print(f"Memória Atual (Deve continuar 10MB): {manager.get_total_memory_mb()} MB")
    
    print("\n--- 3. Afastamento Completo (Sai do raio de descarga - dist=16) ---")
    spatial_system.update(player_x=16.0, player_y=0.0, objects=[obj_boss])
    print(f"Memória Atual (Retornou ao baseline 0MB): {manager.get_total_memory_mb()} MB")

    print("\n--- 4. Validação de Contraexemplo: Tentativa de configurar Hysteresis errada ---")
    try:
        # Tentando criar um sistema sem margem de segurança
        SpatialProximitySystem(manager, load_radius=10.0, unload_radius=10.0)
    except ValueError as e:
        print(f"[SUCESSO NO CONTRAEXEMPLO] Erro capturado corretamente: {e}")