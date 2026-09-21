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
    def __init__(self, player_id: str, max_speed: float = 5.0):
        self.player_id = player_id
        self.max_speed = max_speed
        self.x = 0.0
        self.y = 0.0
        self.trust_score = 100.0  # Pontuação de infração / confiança
        self.speed_history = CircularBuffer(max_size=30)
        self.last_time = time.time()

class ServerAntiCheatEngine:
    def __init__(self):
        self.players = {}
        self.validation_latencies = []
        self.flags_raised = 0
        self.total_validations = 0

    def register_player(self, player_id: str, max_speed: float = 5.0):
        self.players[player_id] = PlayerSession(player_id, max_speed)

    def process_player_input(self, player_id: str, client_x: float, client_y: float, input_dx: float, input_dy: float, dt: float) -> dict:
        start_time = time.perf_counter()
        self.total_validations += 1

        if player_id not in self.players:
            return {"status": "error", "reason": "unknown_player"}

        player = self.players[player_id]

        # --- CAMADA 1: Validação Cinemática Rigorosa (Speedhack / Teleport) ---
        # O servidor recalcula a posição teórica baseada exclusivamente no input autorizado
        magnitude = math.hypot(input_dx, input_dy)
        expected_speed = (magnitude / dt) if dt > 0 else 0.0

        # Tolerância dinâmica para compensar jitter de rede (fator de folga de 20%)
        speed_limit_tolerance = player.max_speed * 1.2

        anomaly_detected = False
        reason = "ok"

        if expected_speed > speed_limit_tolerance:
            anomaly_detected = True
            reason = "speedhack_detected"
        
        # Verificação de Teleport (distância absoluta percorrida vs velocidade máxima teórica)
        dist_moved = math.hypot(client_x - player.x, client_y - player.y)
        max_possible_dist = player.max_speed * dt * 1.5 # margem de jitter

        if dist_moved > max_possible_dist and not anomaly_detected:
            anomaly_detected = True
            reason = "teleport_detected"

        # --- CAMADA 2: Detecção Estatística por Z-Score (Desvios Sutis) ---
        player.speed_history.append(expected_speed)
        mean_speed = player.speed_history.mean()
        std_speed = player.speed_history.std_dev()

        # Se houver histórico suficiente, checa desvio padrão anômalo (Z-score > 3.0)
        if len(player.speed_history.buffer) >= 10 and std_speed > 0:
            z_score = (expected_speed - mean_speed) / std_speed
            if z_score > 3.5:
                anomaly_detected = True
                reason = "behavioral_anomaly_zscore"

        # Atualização de Estado e Sistema de Confiança
        if anomaly_detected:
            player.trust_score -= 25.0
            self.flags_raised += 1
            # Servidor impõe correção autoritativa (rejeita a posição do cliente)
            # Mantém a posição anterior simulada pelo servidor
        else:
            # Estado aceito, servidor atualiza a posição oficial
            player.x = client_x
            player.y = client_y
            if player.trust_score < 100.0:
                player.trust_score = min(100.0, player.trust_score + 1.0) # Recuperação gradual

        elapsed = (time.perf_counter() - start_time) * 1000.0 # em milissegundos
        self.validation_latencies.append(elapsed)

        return {
            "player_id": player_id,
            "anomaly": anomaly_detected,
            "reason": reason,
            "trust_score": player.trust_score,
            "latency_ms": elapsed
        }

# --- TESTES E DEMONSTRAÇÃO DOS CONCEITOS ---
if __name__ == "__main__":
    engine = ServerAntiCheatEngine()
    
    # Registra dois jogadores
    engine.register_player("player_legit", max_speed=5.0)
    engine.register_player("player_cheater", max_speed=5.0)

    print("=== INICIANDO SIMULAÇÃO DE VALIDAÇÃO SERVER-SIDE ===")

    # Simulação de Jogador Legítimo (Movimentos dentro do limite, com leve jitter)
    dt = 0.05 # 20 ticks por segundo
    for i in range(20):
        res = engine.process_player_input("player_legit", client_x=i*0.2, client_y=0, input_dx=0.2, input_dy=0, dt=dt)
        assert not res["anomaly"], f"Falso positivo detectado no jogador legítimo no tick {i}!"

    # Simulação de Cheater (Ativando Speedhack súbito)
    cheater_res_1 = engine.process_player_input("player_cheater", client_x=10.0, client_y=0, input_dx=5.0, input_dy=0, dt=dt)
    print(f"Cheater Tentativa 1 (Speedhack bruto): {cheater_res_1}")
    assert cheater_res_1["anomaly"] == True, "Falha: Speedhack grosseiro não foi detectado!"

    # Simulação de Contraexemplo: Abordagem ingênua falharia com lag spikes (Verificação de Robustez)
    # Vamos testar se o sistema tolera um pico legítimo de rede (jitter) sem gerar falso positivo:
    lag_spike_res = engine.process_player_input("player_legit", client_x=5.5, client_y=0, input_dx=0.5, input_dy=0, dt=0.1) # dt maior por lag
    print(f"Teste de Resiliência a Jitter (Legítimo com Lag): {lag_spike_res}")
    assert not lag_spike_res["anomaly"], "Equívoco Comum Evitado: Jitter de rede gerou falso positivo!"

    # Métricas de Desempenho
    avg_latency = sum(engine.validation_latencies) / len(engine.validation_latencies)
    max_latency = max(engine.validation_latencies)

    print("\n=== RELATÓRIO DE DESEMPENHO DO MOTOR ANTI-CHEAT ===")
    print(f"Total de Validações: {engine.total_validations}")
    print(f"Latência Média por Validação: {avg_latency:.4f} ms (Meta: < 50 ms)")
    print(f"Latência Máxima por Validação: {max_latency:.4f} ms")
    print(f"Flags Acionadas Corretamente: {engine.flags_raised}")
    print("STATUS DO EXPERIMENTO: SUCESSO COMPLETO.")