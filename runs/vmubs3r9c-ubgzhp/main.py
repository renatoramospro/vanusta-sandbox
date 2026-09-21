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

    def __len__(self) -> int:
        return len(self.buffer)

class PlayerSession:
    def __init__(self, player_id: str, max_speed: float = 6.0):
        self.player_id = player_id
        self.max_speed = max_speed
        self.x = 0.0
        self.y = 0.0
        self.trust_score = 100.0
        self.dt_history = CircularBuffer(max_size=30)
        self.last_update_time = time.time()

class AntiCheatEngine:
    def __init__(self):
        self.players = {}
        self.validation_latencies = []
        self.total_validations = 0
        self.flags_raised = 0

    def register_player(self, player_id: str, max_speed: float = 6.0):
        self.players[player_id] = PlayerSession(player_id, max_speed)

    def validate_action(self, player_id: str, dx: float, dy: float, reported_dt: float) -> dict:
        start_time = time.perf_counter()
        self.total_validations += 1

        player = self.players.get(player_id)
        if not player:
            return {"player_id": player_id, "anomaly": True, "reason": "unknown_player", "trust_score": 0.0}

        # Clamping de dt para evitar divisões por zero ou valores absurdos
        clamped_dt = max(0.01, min(reported_dt, 1.0))
        
        # Desacoplamento temporal: Armazena o dt reportado no histórico estatístico
        player.dt_history.append(clamped_dt)

        # Se houver histórico suficiente, calcula o dt médio suavizado para tolerar jitter de rede
        mean_dt = player.dt_history.mean() if len(player.dt_history) > 5 else clamped_dt

        # Distância Euclidiana do movimento reivindicado
        distance = math.sqrt(dx**2 + dy**2)

        # Velocidade cinemática calculada usando o dt suavizado/tolerante a jitter
        effective_speed = distance / mean_dt

        # Tolerância adaptativa baseada na desviação padrão do jitter de rede
        dt_std = player.dt_history.std_dev()
        adaptive_speed_limit = player.max_speed * (1.0 + min(dt_std * 2.0, 0.5))

        is_anomaly = False
        reason = "none"

        # Verificação de Limite Rígido (Camada 1 & 2 com tolerância a jitter)
        if effective_speed > adaptive_speed_limit:
            is_anomaly = True
            reason = "speedhack_detected"
            player.trust_score = max(0.0, player.trust_score - 25.0)
            self.flags_raised += 1
        else:
            # Recuperação gradual de trust score para jogo legítimo
            player.trust_score = min(100.0, player.trust_score + 1.0)

        # Atualiza posição autoritativa se não for anomalia severa
        if not is_anomaly or effective_speed <= adaptive_speed_limit * 1.1:
            player.x += dx
            player.y += dy

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        self.validation_latencies.append(latency_ms)

        return {
            "player_id": player_id,
            "anomaly": is_anomaly,
            "reason": reason,
            "trust_score": player.trust_score,
            "latency_ms": latency_ms
        }

if __name__ == "__main__":
    print("=== INICIANDO SIMULAÇÃO CORRIGIDA E ROBUSTA DE VALIDAÇÃO SERVER-SIDE ===")
    
    engine = AntiCheatEngine()
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