import time
import math

class NetworkSimulation:
    """ Simula uma rede com atraso (latency_ms) e pacotes em trânsito. """
    def __init__(self, latency_ms=150):
        self.latency_seconds = latency_ms / 1000.0
        self.queue = [] # Lista de tuplas (delivery_time, packet_data, receiver_type)

    def send(self, current_time, data, receiver_type):
        delivery_time = current_time + self.latency_seconds
        self.queue.append((delivery_time, data, receiver_type))

    def receive(self, current_time, receiver_type):
        delivered = []
        remaining = []
        for item in self.queue:
            delivery_time, data, r_type = item
            if r_type == receiver_type and current_time >= delivery_time:
                delivered.append(data)
            else:
                remaining.append(item)
        self.queue = remaining
        return delivered

class GameInput:
    def __init__(self, sequence, dx):
        self.sequence = sequence
        self.dx = dx

class ServerAuthoritative:
    """ Servidor que processa inputs de forma autoritativa. """
    def __init__(self):
        self.position = 0.0
        self.last_processed_sequence = 0

    def process_input(self, game_input):
        self.position += game_input.dx
        self.last_processed_sequence = game_input.sequence

class ClientPrediction:
    """ Cliente com Predição, Histórico de Inputs e Reconciliação Corrigida. """
    def __init__(self):
        self.predicted_position = 0.0
        self.sequence_counter = 0
        self.pending_inputs = [] # Lista de GameInput

    def generate_input(self, dx):
        self.sequence_counter += 1
        inp = GameInput(self.sequence_counter, dx)
        self.pending_inputs.append(inp)
        # Predição imediata local
        self.predicted_position += dx
        return inp

    def reconcile(self, server_position, server_ack):
        # 1. Remove inputs antigos já processados pelo servidor
        self.pending_inputs = [inp for inp in self.pending_inputs if inp.sequence > server_ack]

        # 2. Reseta a posição para a autoritativa do servidor
        recomputed_position = server_position

        # 3. Re-simula todos os inputs ainda pendentes (não confirmados)
        for inp in self.pending_inputs:
            recomputed_position += inp.dx

        self.predicted_position = recomputed_position

def run_simulation_test():
    print("Iniciando simulação de rede com RTT de 150ms (Reconciliação Corrigida)...")
    
    network = NetworkSimulation(latency_ms=150)
    server = ServerAuthoritative()
    client = ClientPrediction()

    sim_time = 0.0
    dt = 0.016 # ~60 FPS
    steps = 100
    max_error = 0.0

    movement_speed = 1.0 # unidades por passo

    for step in range(steps):
        sim_time += dt

        # 1. Cliente gera input
        inp = client.generate_input(movement_speed)
        network.send(sim_time, inp, receiver_type="server")

        # 2. Servidor recebe e processa inputs disponíveis na rede
        server_packets = network.receive(sim_time, receiver_type="server")
        for packet in server_packets:
            server.process_input(packet)
            # Servidor envia de volta o estado atual e o ACK correspondente
            network.send(sim_time, {"pos": server.position, "ack": server.last_processed_sequence}, receiver_type="client")

        # 3. Cliente recebe estado do servidor e reconcilia
        client_packets = network.receive(sim_time, receiver_type="client")
        for packet in client_packets:
            client.reconcile(packet["pos"], packet["ack"])

        # 4. Avaliação do Erro (Diferença entre Predição do Cliente e Servidor Autoritativo)
        current_error = abs(client.predicted_position - server.position)
        if current_error > max_error:
            max_error = current_error

    print(f"Simulação concluída com sucesso após {steps} passos.")
    print(f"Erro máximo de sincronização registrado: {max_error:.5f} unidades.")

    # Critério de sucesso rigoroso: Erro inferior a 0.1 unidades
    assert max_error < 0.1, f"FALHA: Erro de sincronização ({max_error}) excedeu o limite de 0.1!"
    print("Critério de sucesso atendido: Erro inferior a 0.1 unidades validado com sucesso sob 150ms de latência.")

if __name__ == "__main__":
    run_simulation_test()