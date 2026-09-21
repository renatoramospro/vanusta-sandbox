import collections

class GameInput:
    def __init__(self, sequence, dx):
        self.sequence = sequence
        self.dx = dx

class Network:
    """Simula uma rede com latência (RTT) e entrega de pacotes."""
    def __init__(self, rtt_frames):
        self.rtt_frames = rtt_frames
        self.queue = collections.deque() # (delivery_frame, data)

    def send(self, current_frame, data):
        # O pacote leva RTT/2 para ir e RTT/2 para voltar
        delivery_frame = current_frame + (self.rtt_frames // 2)
        self.queue.append((delivery_frame, data))

    def receive(self, current_frame):
        received = []
        # Remove pacotes que já deveriam ter chegado
        while self.queue and self.queue[0][0] <= current_frame:
            received.append(self.queue.popleft()[1])
        return received

class Server:
    def __init__(self, speed):
        self.position = 0.0
        self.speed = speed
        self.last_processed_sequence = 0

    def process_input(self, game_input):
        # Autoridade absoluta: processa o input e atualiza o ACK
        self.position += game_input.dx
        self.last_processed_sequence = game_input.sequence

    def get_state(self):
        return {"pos": self.position, "ack": self.last_processed_sequence}

class Client:
    def __init__(self, speed):
        self.predicted_position = 0.0
        self.speed = speed
        self.input_history = [] # Lista de GameInput
        self.next_sequence = 1
        self.last_server_ack = 0

    def generate_input(self):
        dx = self.speed
        new_input = GameInput(self.next_sequence, dx)
        self.input_history.append(new_input)
        self.predicted_position += dx
        self.next_sequence += 1
        return new_input

    def reconcile(self, server_state):
        # 1. Atualiza o último ACK recebido para evitar pacotes Out-of-Order
        if server_state["ack"] <= self.last_server_ack:
            return # Ignora pacotes atrasados (Out-of-Order)
        
        self.last_server_ack = server_state["ack"]

        # 2. PRUNING: Remove inputs que o servidor já confirmou
        self.input_history = [i for i in self.input_history if i.sequence > self.last_server_ack]

        # 3. REPLAY: Reseta para a posição do servidor e re-simula os pendentes
        self.predicted_position = server_state["pos"]
        for inp in self.input_history:
            self.predicted_position += inp.dx

def run_simulation_test():
    # Configurações
    TOTAL_STEPS = 100
    SPEED = 1.0
    RTT = 15  # 15 frames de RTT (simulando ~250ms para ser rigoroso)
    
    client = Client(SPEED)
    server = Server(SPEED)
    
    # Redes separadas para simular ida e volta (Client -> Server e Server -> Client)
    client_to_server_net = Network(RTT)
    server_to_client_net = Network(RTT)

    max_divergence = 0.0

    print(f"Iniciando simulação: {TOTAL_STEPS} passos, RTT={RTT} frames...")

    for frame in range(TOTAL_STEPS):
        # --- 1. CLIENT SIDE ---
        # Cliente gera e prevê movimento
        current_input = client.generate_input()
        client_to_server_net.send(frame, current_input)

        # Cliente recebe estados do servidor (Reconciliação)
        server_updates = server_to_client_net.receive(frame)
        for state in server_updates:
            client.reconcile(state)

        # --- 2. SERVER SIDE ---
        # Servidor recebe inputs do cliente
        inputs_to_process = client_to_server_net.receive(frame)
        for inp in inputs_to_process:
            server.process_input(inp)
        
        # Servidor envia estado para o cliente
        server_to_client_net.send(frame, server.get_state())

        # --- 3. MÉTRICA DE RIGOR (Divergência de Estado) ---
        # A divergência não é (client.pos - server.pos), mas sim:
        # O quanto o cliente está longe do que o servidor será após processar os pendentes.
        pending_dx = sum(i.dx for i in client.input_history)
        expected_server_future_pos = server.position + pending_dx
        
        divergence = abs(client.predicted_position - expected_server_future_pos)
        if divergence > max_divergence:
            max_divergence = divergence

    print(f"Simulação concluída.")
    print(f"Erro máximo de divergência registrado: {max_divergence:.5f} unidades.")

    # Critério de sucesso: Erro < 0.1
    # Se a reconciliação for perfeita, a divergência deve ser virtualmente zero.
    assert max_divergence < 0.1, f"FALHA: Divergência ({max_divergence}) excedeu o limite de 0.1!"
    print("Critério de sucesso atendido: Reconciliação atômica validada.")

if __name__ == "__main__":
    run_simulation_test()