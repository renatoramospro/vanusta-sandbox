import time
import math

class NetworkSimulation:
    """ Simula uma rede com atraso (latency_ms) e variação (jitter). """
    def __init__(self, latency_ms=150):
        self.latency_s = latency_ms / 1000.0
        self.inbox = []

    def send(self, packet, sender, receiver_id):
        # Simula o envio com atraso fixo de metade do RTT (one-way delay)
        delivery_time = time.time() + (self.latency_s / 2.0)
        self.inbox.append((delivery_time, packet, sender, receiver_id))

    def receive(self, current_time, receiver_id):
        ready_packets = []
        remaining = []
        for delivery_time, packet, sender, rcvr in self.inbox:
            if rcvr == receiver_id and current_time >= delivery_time:
                ready_packets.append((packet, sender))
            else:
                remaining.append((delivery_time, packet, sender, rcvr))
        self.inbox = remaining
        return ready_packets

class Server:
    """ Autoridade central do jogo. """
    def __init__(self):
        self.position = 0.0
        self.last_processed_input_seq = 0

    def handle_input(self, input_seq, move_delta):
        self.position += move_delta
        self.last_processed_input_seq = input_seq

    def get_state(self):
        return {
            "position": self.position,
            "ack_seq": self.last_processed_input_seq
        }

class ClientWithPrediction:
    """ Cliente com predição, histórico de inputs e reconciliação. """
    def __init__(self):
        self.predicted_position = 0.0
        self.input_sequence = 0
        self.pending_inputs = [] # Lista de (seq, delta)
        self.server_authoritative_position = 0.0

    def move(self, delta):
        self.input_sequence += 1
        self.pending_inputs.append((self.input_sequence, delta))
        # Predição imediata local
        self.predicted_position += delta
        return self.input_sequence

    def reconcile(self, server_state):
        self.server_authoritative_position = server_state["position"]
        ack_seq = server_state["ack_seq"]

        # Remove inputs já processados pelo servidor do buffer pendente
        self.pending_inputs = [inp for inp in self.pending_inputs if inp[0] > ack_seq]

        # Re-simulação (Rollback & Re-apply)
        recalculated_pos = self.server_authoritative_position
        for _, delta in self.pending_inputs:
            recalculated_pos += delta

        # Aplica a posição corrigida
        self.predicted_position = recalculated_pos

class EntityInterpolator:
    """ Gerencia buffer de estados para interpolação suave de entidades remotas. """
    def __init__(self, interpolation_delay_s=0.1):
        self.buffer = [] # Lista de (timestamp, position)
        self.delay = interpolation_delay_s

    def add_snapshot(self, timestamp, position):
        self.buffer.append((timestamp, position))
        # Mantém apenas o histórico necessário
        if len(self.buffer) > 20:
            self.buffer.pop(0)

    def interpolate(self, current_time):
        render_time = current_time - self.delay

        # Encontra os dois snapshots que cercam o render_time
        older = None
        newer = None

        for i in range(len(self.buffer) - 1):
            if self.buffer[i][0] <= render_time <= self.buffer[i+1][0]:
                older = self.buffer[i]
                newer = self.buffer[i+1]
                break

        if older and newer:
            t0, p0 = older
            t1, p1 = newer
            factor = (render_time - t0) / (t1 - t0)
            return p0 + (p1 - p0) * factor
        elif self.buffer:
            # Fallback para o mais recente se não houver intervalo completo
            return self.buffer[-1][1]
        return 0.0

def run_simulation_test():
    print("Iniciando simulação de rede com RTT de 150ms...")
    network = NetworkSimulation(latency_ms=150)
    server = Server()
    client = ClientWithPrediction()
    interpolator = EntityInterpolator(interpolation_delay_s=0.1)

    start_time = time.time()
    sim_time = start_time

    max_error = 0.0
    steps = 100
    dt = 0.016 # ~60 FPS

    for step in range(steps):
        sim_time += dt

        # 1. Cliente gera input a cada passo (movimenta 1.0 unidade por passo)
        seq = client.move(1.0)
        network.send({"seq": seq, "delta": 1.0}, sender="client", receiver_id="server")

        # 2. Servidor recebe e processa inputs
        server_packets = network.receive(sim_time, receiver_id="server")
        for pkt, _ in server_packets:
            server.handle_input(pkt["seq"], pkt["delta"])

        # 3. Servidor envia estado atualizado periodicamente de volta ao cliente
        if step % 5 == 0:
            state = server.get_state()
            network.send(state, sender="server", receiver_id="client")
            # Simula também o envio para o interpolador (entidade remota)
            interpolator.add_snapshot(sim_time, server.position)

        # 4. Cliente recebe pacotes do servidor e reconcilia
        client_packets = network.receive(sim_time, receiver_id="client")
        for pkt, _ in client_packets:
            client.reconcile(pkt)

        # 5. Avaliação do Erro (Diferença entre Predição do Cliente e Servidor Autoritativo)
        current_error = abs(client.predicted_position - server.position)
        if current_error > max_error:
            max_error = current_error

    print(f"Simulação concluída com sucesso após {steps} passos.")
    print(f"Erro máximo de sincronização registrado: {max_error:.5f} unidades.")

    # Critério de sucesso: Erro inferior a 0.1 unidades
    assert max_error < 0.1, f"FALHA: Erro de sincronização ({max_error}) excedeu o limite de 0.1!"
    print("Critério de sucesso atendido: Erro inferior a 0.1 unidades validado com sucesso sob 150ms de latência.")

if __name__ == "__main__":
    run_simulation_test()