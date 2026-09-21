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
        self.total_validations += 1

        player = self.players.get(player_id)
        if not player:
            return {"error": "player_not_found"}

        # Correção contra Jitter: Limita o dt máximo para evitar divisão por zero ou saltos irreais de pacotes
        dt = max(0.001, min(reported_dt, 0.25))

        # Camada 1: Validação Cinemática Rigorosa (Speedhack / Teleport)
        distance = math.sqrt(dx**2 + dy**2)
        instant_speed = distance / dt

        # Margem de tolerância física para jitter de rede (15% acima da velocidade máxima nominal)
        hard_speed_limit = player.max_speed * 1.15
        
        is_speedhack = instant_speed > hard_speed_limit

        # Camada 2: Detecção de Anomalias Estatísticas (Z-Score com amortecimento para jitter)
        player.speed_history.append(instant_speed)
        mean_speed = player.speed_history.mean()
        std_speed = player.speed_history.std_dev()

        is_behavioral_anomaly = False
        if len(player.speed_history.buffer) >= 10 and std_speed > 0.001:
            z_score = (instant_speed - mean_speed) / std_speed
            # Exigimos Z-score > 4.5 e que exceda o limite estrito para evitar falsos positivos por jitter
            if z_score > 4.5 and instant_speed > player.max_speed * 1.1:
                is_behavioral_anomaly = True

        anomaly_detected = is_speedhack or is_behavioral_anomaly
        reason = "none"

        if is_speedhack:
            reason = "speedhack_detected"
            player.trust_score = max(0.0, player.trust_score - 25.0)
            self.flags_raised += 1
        elif is_behavioral_anomaly:
            reason = "behavioral_anomaly_zscore"
            player.trust_score = max(0.0, player.trust_score - 10.0)
            self.flags_raised += 1

        elapsed = (time.perf_counter() - start_time) * 1000.0
        self.validation_latencies.append(elapsed)

        return {
            "player_id": player_id,
            "anomaly": anomaly_detected,
            "reason": reason,
            "trust_score": player.trust_score,
            "latency_ms": elapsed
        }

if __name__ == "__main__":
    print("=== INICIANDO SIMULAÇÃO CORRIGIDA DE VALIDAÇÃO SERVER-SIDE ===")
    engine = ServerAntiCheatEngine()

    # Registra jogadores
    engine.register_player("player_cheater", max_speed=5.0)
    engine.register_player("player_legit", max_speed=5.0)

    # 1. Teste de Speedhack Bruto
    cheater_res = engine.validate_action("player_cheater", dx=25.0, dy=0.0, reported_dt=0.1)
    print(f"Cheater Tentativa 1 (Speedhack): {cheater_res}")
    assert cheater_res["anomaly"], "Falha: Speedhack não detectado!"

    # 2. Teste de Resiliência a Jitter (Jogador legítimo com variação de pacotes / lag spike)
    # Envia múltiplos pacotes normais para popular o histórico
    for _ in range(15):
        engine.validate_action("player_legit", dx=1.0, dy=0.0, reported_dt=0.05)

    # Simula um jitter de rede severo (pacote atrasado com dt maior e variação natural)
    lag_spike_res = engine.validate_action("player_legit", dx=1.2, dy=0.1, reported_dt=0.18)
    print(f"Teste de Resiliência a Jitter (Legítimo com Lag): {lag_spike_res}")
    
    # Validação do critério corrigido: Jitter não deve gerar falso positivo
    assert not lag_spike_res["anomaly"], "Equívoco Comum Evitado: Jitter de rede gerou falso positivo!"

    # Métricas de Desempenho
    avg_latency = sum(engine.validation_latencies) / len(engine.validation_latencies)
    max_latency = max(engine.validation_latencies)

    print("\n=== RELATÓRIO DE DESEMPENHO DO MOTOR ANTI-CHEAT ===")
    print(f"Total de Validações: {engine.total_validations}")
    print(f"Latência Média por Validação: {avg_latency:.4f} ms (Meta: < 50 ms)")
    print(f"Latência Máxima por Validação: {max_latency:.4f} ms")
    print(f"Flags Acionadas Corretamente: {engine.flags_raised}")
    print("STATUS DO EXPERIMENTO: SUCESSO COMPLETO E CORrigido.")