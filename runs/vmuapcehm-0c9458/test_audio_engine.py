import math
import pytest

# Constantes do Sistema
MAX_AUDIO_MEMORY_MB = 50.0

class SoundAsset:
    """Representa um arquivo de áudio carregado no banco de dados com controle de tamanho."""
    def __init__(self, name: str, size_mb: float):
        self.name = name
        self.size_mb = size_mb

class AudioDatabaseManager:
    """Gerencia o banco de dados de áudio com controle para respeitar o limite de 50MB."""
    def __init__(self):
        self.loaded_assets = {}
        self.total_memory_mb = 0.0

    def load_asset(self, asset: SoundAsset) -> bool:
        if self.total_memory_mb + asset.size_mb > MAX_AUDIO_MEMORY_MB:
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
        Simula raycasting para detectar se há paredes entre a fonte e o ouvinte.
        Retorna a quantidade de obstáculos interceptados.
        """
        obstacles_hit = 0
        for wall in walls:
            w_start, w_end = wall[0], wall[1]
            # Verificação geométrica simplificada de interseção de segmentos
            if SpatialAudioEngine._intersect(listener_pos, source_pos, w_start, w_end):
                obstacles_hit += 1
        return obstacles_hit

    @staticmethod
    def _ccw(A, B, C):
        return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

    @staticmethod
    def _intersect(A, B, C, D):
        return SpatialAudioEngine._ccw(A,C,D) != SpatialAudioEngine._ccw(B,C,D) and \
               SpatialAudioEngine._ccw(A,B,C) != SpatialAudioEngine._ccw(A,B,D)

    @classmethod
    def process_spatial_audio(cls, source_pos, listener_pos, base_amplitude, walls):
        # 1. Atenuação por distância (Inverse Square Law) com clamping para evitar divisão por zero
        raw_distance = cls.calculate_distance(source_pos, listener_pos)
        distance = max(raw_distance, 0.1) # Clamping defensivo contra d=0
        
        # Evita divisão por zero ou valores absurdos
        attenuated_amplitude = base_amplitude / (distance ** 2)

        # 2. Detecção de Oclusão
        obstacles = cls.raycast_occlusion(listener_pos, source_pos, walls)

        # 3. Filtragem de Frequências (LPF) com modelo assintótico (nunca negativo ou zero)
        # Formula: 1 / (1 + k * obstacles) -> garante decaimento suave e intervalo (0, 1]
        lpf_cutoff_factor = 1.0 / (1.0 + 0.5 * obstacles)

        return {
            "distance": distance,
            "amplitude": attenuated_amplitude,
            "obstacles": obstacles,
            "lpf_cutoff_factor": lpf_cutoff_factor
        }

# --- TESTES AUTOMATIZADOS (COMPATÍVEIS COM PYTEST) ---

def test_audio_database_memory_limit():
    db = AudioDatabaseManager()
    asset1 = SoundAsset("sound_effects_pack.wav", 30.0)
    asset2 = SoundAsset("ambient_music.wav", 15.0)
    asset3 = SoundAsset("heavy_ost.wav", 10.0)

    assert db.load_asset(asset1) is True
    assert db.load_asset(asset2) is True
    # Adicionar asset3 ultrapassaria 50MB (30 + 15 + 10 = 55MB)
    assert db.load_asset(asset3) is False
    assert db.total_memory_mb == 45.0

def test_inverse_square_law_robustness():
    # Testa distância zero (fonte e ouvinte na mesma posição) para garantir robustness
    engine = SpatialAudioEngine()
    same_pos = (0.0, 0.0)
    result = engine.process_spatial_audio(same_pos, same_pos, base_amplitude=100.0, walls=[])
    
    assert result["distance"] == 0.1 # Verificação do clamping
    assert result["amplitude"] > 0 # Não deve lançar ZeroDivisionError nem infinito

def test_open_field_scenario():
    engine = SpatialAudioEngine()
    walls = [((2.0, -5.0), (2.0, 5.0))] # Parede vertical
    listener = (0.0, 0.0)
    source_open = (1.0, 0.0) # Na frente da parede (sem obstáculos entre listener e source)
    
    result = engine.process_spatial_audio(source_open, listener, base_amplitude=100.0, walls=walls)
    assert result["obstacles"] == 0
    assert result["lpf_cutoff_factor"] == 1.0

def test_obstructed_corridor_scenario():
    engine = SpatialAudioEngine()
    walls = [((2.0, -5.0), (2.0, 5.0))]
    listener = (0.0, 0.0)
    source_obstructed = (4.0, 0.0) # Atrás da parede
    
    result = engine.process_spatial_audio(source_obstructed, listener, base_amplitude=100.0, walls=walls)
    assert result["obstacles"] > 0
    assert result["lpf_cutoff_factor"] < 1.0
    assert result["lpf_cutoff_factor"] > 0.0, "O fator LPF nunca deve ser menor ou igual a zero!"

def test_multiple_obstacles_lpf_behavior():
    engine = SpatialAudioEngine()
    # Múltiplas paredes cruzando o feixe
    walls = [
        ((1.0, -5.0), (1.0, 5.0)),
        ((3.0, -5.0), (3.0, 5.0))
    ]
    listener = (0.0, 0.0)
    source = (5.0, 0.0)
    
    result = engine.process_spatial_audio(source, listener, base_amplitude=100.0, walls=walls)
    assert result["obstacles"] == 2
    # Com 2 obstáculos: 1.0 / (1.0 + 0.5 * 2) = 1.0 / 2.0 = 0.5
    assert math.isclose(result["lpf_cutoff_factor"], 0.5)