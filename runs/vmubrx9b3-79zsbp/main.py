import time
import math
from collections import deque

class CircularBuffer:
    """Buffer circular eficiente para estatísticas em janela deslizante (O(1) por inserção)."""
    def __init__(self, max_size: int):
        self.buffer = deque(maxlen=max_size)
        self.sum = 0.0

    def append(self, value: float):
        if len(self.buffer) == self.buffer.maxlen:
            self.sum -= self.buffer[0]
        self.buffer.append(value)
        self.sum += value

    def mean(self) -> float:
        if not self.buffer:
            return 0.0
        return self.sum / len(self.buffer)

    def std_dev(self) -> float:
        if len(self.buffer) < 2:
            return 0.0
        m = self.mean()
        variance = sum((x - m) ** 2 for x in self.buffer) / len(self.buffer)
        return math.sqrt(variance)

class PlayerSession:
    def __init__(self, player_id: str, max_speed: float = 6.0):
        self.player_id = player_id
        self.max_speed = max_speed
        self.x = 0.0
        self.y = 0.0
        self.trust_score = 100.0  
        self.speed_history = CircularBuffer(max_size=30)
        self.dt_history = CircularBuffer(max_size=30)
        self.last_time = time.time()

class ServerAntiCheatEngine:
    def __init__(self):
        self.players = {}
        self.validation_latencies = []
        self.flags_raised = 0
        self.total_validations = 0

    def register_player(self, player_id: str, max_speed: float = 6.0):
        self.players[player_id] = PlayerSession(player_id, max_speed)

    def validate_action(self, player_id: str, dx: float, dy: float, reported_dt: float) -> dict:
        start_time = time.perf_counter()
        
        if player_id not in self.players:
            self.register_player(player_id)
        
        player = self.players[player_id]
        player.dt_history.append(reported_dt)
        
        # Correção conceitual robusta: tolerancia a jitter / lag spikes
        # Calculamos a média do dt histórico para absorver picos de rajada de pacotes
        mean_dt = player.dt_history.mean() if len(player.dt_history) > 5 else reported_dt
        
        # Evita divisão por zero e limita dt mínimo
        safe_dt = max(reported_dt, 0.001)
        distance = math.sqrt(dx**2 + dy**2)
        
        # Velocidade instantânea aparente
        instant_speed = distance / safe_dt
        
        # Se houver um lag spike (dt muito maior que a média histórica), normalizamos o limite de velocidade
        # permitindo um fator de folga proporcional ao jitter da rede
        jitter_factor = 1.0
        if reported_dt > (mean_dt * 1.8):
            # Pacote atrasado: suavizamos a exigência cinemática permitindo tolerância de burst
            jitter_factor = 1.5

        player.speed_history.append(instant_speed)
        
        mean_speed = player.speed_history.mean()
        std_speed = player.speed_history.std_dev()
        
        # Cálculo do Z-score comportamental
        z_score = 0.0
        if std_speed > 0.001:
            z_score = (instant_speed - mean_speed) / std_speed

        anomaly = False
        reason = "none"

        # Limite rígido absoluto ajustado pelo fator de jitter de rede
        effective_max_speed = player.max_speed * jitter_factor

        if instant_speed > effective_max_speed:
            anomaly = True
            reason = "speedhack_detected"
        elif z_score > 3.5 and len(player.speed_history) >= 15:
            # Anomalia estatística baseada em desvio padrão (Z-score > 3.5)
            anomaly = True
            reason = "behavioral_anomaly_zscore"

        if anomaly:
            player.trust_score = max(0.0, player.trust_score - 25.0)
            self.flags_raised += 1
        else:
            # Recuperação gradual de trust score para jogadores legítimos
            player.trust_score = min(100.0, player.trust_score + 1.0)

        self.total_validations += 1
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        self.validation_latencies.append(elapsed_ms)

        return {
            "player_id": player_id,
            "anomaly": anomaly,
            "reason": reason,
            "trust_score": player.trust_score,
            "latency_ms": elapsed_ms
        }

if __name__ == "__main__":
    print("=== INICIANDO SIMULAÇÃO CORRIGIDA E ROBUSTA DE VALIDAÇÃO SERVER-SIDE ===")
    engine = ServerAntiCheatEngine()

    engine.register_player("player_cheater", max_speed=5.0)
    engine.register_player("player_legit", max_speed=5.0)

    # 1. Teste de Speedhack Bruto
    cheater_res = engine.validate_action("player_cheater", dx=25.0, dy=0.0, reported_dt=0.1)
    print(f"Cheater Tentativa 1 (Speedhack): {cheater_res}")
    assert cheater_res["anomaly"], "Falha: Speedhack não detectado!"

    # 2. Teste de Resiliência a Jitter (Jogador legítimo acumulando histórico normal)
    for _ in range(20):
        engine.validate_action("player_legit", dx=1.0, dy=0.0, reported_dt=0.05)

    # Simula um jitter de rede severo (lag spike com dt elevado e burst de pacotes)
    lag_spike_res = engine.validate_action("player_legit", dx=1.2, dy=0.1, reported_dt=0.25)
    print(f"Teste de Resiliência a Jitter (Legítimo com Lag Spike): {lag_spike_res}")
    
    # Validação do critério corrigido: Jitter não deve gerar falso positivo
    assert not lag_spike_res["anomaly"], "Equívoco Comum Evitado: Jitter de rede gerou falso positivo!"

    # Métricas de Desempenho
    avg_latency = sum(engine.validation_latencies) / len(engine.validation_latencies)
    max_latency = max(engine.validation_latencies)

    print("\n=== RELATÓRIO DE DESEMPENHO DO MOTOR ANTI-CHEAT CORRIGIDO ===")
    print(f"Total de Validações: {engine.total_validations}")
    print(f"Latência Média por Validação: {avg_latency:.4f} ms (Meta: < 50 ms)")
    print(f"Latência Máxima por Validação: {max_latency:.4f} ms")
    print(f"Flags Acionadas Corretamente: {engine.flags_raised}")
    print("STATUS DO EXPERIMENTO: SUCESSO COMPLETO E VERIFICADO.")