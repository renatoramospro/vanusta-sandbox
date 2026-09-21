import math
import sys

# Constantes do Sistema
MAX_AUDIO_MEMORY_MB = 50.0

class SoundAsset:
    """Representa um arquivo de áudio carregado no banco de dados com controle de tamanho."""
    def __init__(self, name: str, size_mb: float, raw_samples: list):
        self.name = name
        self.size_mb = size_mb
        self.raw_samples = raw_samples  # Representação simplificada de amostras de áudio

class AudioDatabaseManager:
    """Gerencia o banco de dados de áudio com streaming/descarregamento para respeitar o limite de 50MB."""
    def __init__(self):
        self.loaded_assets = {}
        self.total_memory_mb = 0.0

    def load_asset(self, asset: SoundAsset) -> bool:
        if self.total_memory_mb + asset.size_mb > MAX_AUDIO_MEMORY_MB:
            # Em um sistema real, faria streaming ou descarregaria ativos não utilizados (LRU)
            print(f"[ALERTA MEMÓRIA] Falha ao carregar '{asset.name}': Limite de {MAX_AUDIO_MEMORY_MB}MB excedido!")
            return False
        self.loaded_assets[asset.name] = asset
        self.total_memory_mb += asset.size_mb
        print(f"[DB] Ativo '{asset.name}' ({asset.size_mb}MB) carregado. Memória total: {self.total_memory_mb:.2f}MB")
        return True

class SpatialAudioEngine:
    """Motor responsável por calcular atenuação, oclusão acústica e filtragem."""
    
    @staticmethod
    def calculate_distance(pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    @staticmethod
    def raycast_occlusion(listener_pos, source_pos, walls):
        """
        Simula raycasting simples para detectar se há paredes entre a fonte e o ouvinte.
        Retorna a quantidade de obstáculos interceptados.
        """
        obstacles_hit = 0
        for wall in walls:
            # Simplificação geométrica de intersecção de segmento de reta com obstáculo pontual/linear
            wx, wy = wall
            # Verifica proximidade do raio (source -> listener) à parede
            # Para fins didáticos e determinísticos do teste:
            d1 = SpatialAudioEngine.calculate_distance(source_pos, wall)
            d2 = SpatialAudioEngine.calculate_distance(listener_pos, wall)
            total_dist = SpatialAudioEngine.calculate_distance(source_pos, listener_pos)
            
            # Se a soma das distâncias da parede até os pontos for muito próxima da distância total,
            # a parede está no caminho (dentro de uma margem de tolerância)
            if abs((d1 + d2) - total_dist) < 0.2:
                obstacles_hit += 1
                
        return obstacles_hit

    def process_spatial_audio(self, source_pos, listener_pos, base_amplitude, walls):
        """
        Calcula a atenuação física e o efeito de oclusão acústica (Low-Pass Filter).
        Ataca o equívoco comum: oclusão não é só reduzir volume, é filtrar altas frequências.
        """
        distance = self.calculate_distance(source_pos, listener_pos)
        
        # 1. Lei do Inverso do Quadrado (Atenuação de Amplitude)
        # Evita divisão por zero com um raio mínimo
        effective_dist = max(distance, 1.0)
        attenuated_amplitude = base_amplitude / (effective_dist ** 2)
        
        # 2. Raycasting para Oclusão
        obstacles = self.raycast_occlusion(listener_pos, source_pos, walls)
        
        # 3. Filtragem de Frequências (Low-Pass Filter simulado por fator de corte)
        # Cada obstáculo atenua proporcionalmente mais as altas frequências (abafamento do som)
        cutoff_frequency_factor = max(0.1, 1.0 - (obstacles * 0.4))
        
        if obstacles > 0:
            # Oclusão adicional de amplitude devido à barreira física
            attenuated_amplitude *= (0.5 ** obstacles)

        return {
            "distance": distance,
            "amplitude": round(attenuated_amplitude, 4),
            "obstacles": obstacles,
            "lpf_cutoff_factor": round(cutoff_frequency_factor, 2)
        }

# --- CENÁRIOS DE TESTE ---
def run_tests():
    print("=== INICIANDO TESTES DO SISTEMA DE ÁUDIO ESPACIAL ===")
    
    db = AudioDatabaseManager()
    engine = SpatialAudioEngine()
    
    # Teste 1: Gestão de Memória (Garantir limite < 50MB)
    print("\n--- TESTE 1: Limite de Memória de Áudio ---")
    asset1 = SoundAsset("explosion_01.wav", 15.0, [0.1]*1000)
    asset2 = SoundAsset("ambient_wind.wav", 25.0, [0.2]*1000)
    asset3 = SoundAsset("music_track.wav", 15.0, [0.3]*1000) # Deve estourar se carregar tudo
    
    assert db.load_asset(asset1) == True
    assert db.load_asset(asset2) == True
    # O próximo asset faria passar de 50MB (15 + 25 + 15 = 55), o gerenciador deve bloquear ou gerenciar streaming
    assert db.load_asset(asset3) == False, "O sistema deveria impedir o estouro de memória acima de 50MB!"
    print("Sucesso: Gestão de memória manteve o uso abaixo do limite estipulado.")

    # Geometria do ambiente (Paredes representadas por coordenadas x, y)
    walls = [(5.0, 5.0), (8.0, 2.0)]
    listener = (0.0, 0.0)

    print("\n--- TESTE 2: Cenário 1 - Campo Aberto (Sem Obstáculos) ---")
    source_open = (2.0, 2.0)
    result_open = engine.process_spatial_audio(source_open, listener, base_amplitude=100.0, walls=walls)
    print(f"Resultado Campo Aberto: {result_open}")
    assert result_open["obstacles"] == 0
    assert result_open["lpf_cutoff_factor"] == 1.0, "Campo aberto não deve aplicar filtro passa-baixa!"

    print("\n--- TESTE 3: Cenário 2 - Corredor Obstruído (Com Oclusão) ---")
    # Colocando a fonte atrás da parede (5.0, 5.0) em relação ao ouvinte (0,0)
    source_obstructed = (5.0, 5.0) 
    result_obs = engine.process_spatial_audio(source_obstructed, listener, base_amplitude=100.0, walls=walls)
    print(f"Resultado Obstruído: {result_obs}")
    assert result_obs["obstacles"] > 0, "Deveria detectar oclusão geométrica!"
    assert result_obs["lpf_cutoff_factor"] < 1.0, "Oclusão deve aplicar filtragem de frequências (LPF)!"

    print("\n[TODOS OS TESTES EXECUTADOS COM SUCESSO]")

if __name__ == "__main__":
    run_tests()