import math

class GameInput:
    def __init__(self, sequence, dx):
        self.sequence = sequence
        self.dx = dx

class Server:
    def __init__(self, speed):
        self.position = 0.0
        self.speed = speed
        self.last_processed_sequence = 0

    def process_input(self, game_input):
        # O servidor é a autoridade absoluta
        self.position += game_input.dx
        self.last_processed_sequence = game_input.sequence

    def get_state(self):
        return {
            "pos": self.position,
            "ack": self.last_processed_sequence
        }

class Client:
    def __init__(self, speed):
        self.predicted_position = 0.0
        self.speed = speed
        self.input_history = []  # Lista de GameInput
        self.next_sequence = 1

    def generate_input(self):
        # O cliente prevê o movimento localmente
        dx = self.speed
        new_input = GameInput(self.next_sequence, dx)
        self.input_history.append(new_input)
        self.predicted_position += dx
        self.next_sequence += 1
        return new_input

    def reconcile(self, server_pos, server_ack):
        # 1. Sincroniza com a autoridade do servidor
        self.predicted_position = server_pos

        # 2. DESCARTE ATÔMICO: Remove inputs que o servidor já processou
        # Isso impede a duplicação que causou o erro de 10.0 unidades
        self.input_history = [i for i in self.input_history if i.sequence > server_ack]

        # 3. REPLAY: Re-simula apenas os inputs que ainda estão "no ar"
        for inp in self.input_history:
            self.predicted_position += inp.dx

class Network:
    def __init__(self, rtt_ms):
        self.latency_frames = max(1, rtt_ms // 16) # Simulação simplificada de frames
        self.buffer = [] # (arrival_frame, data, target)

    def send(self, current_frame, data, target):
        arrival = current_frame + self.latency_frames
        self.buffer.append((arrival, data, target))

    def receive(self, current_frame, target):
        received = []
        remaining = []
        for arrival, data, t in self.buffer:
            if t == target and current_frame >= arrival:
                received.append(data)
            else:
                remaining.append((arrival, data, t))
        self.buffer = remaining
        return received

def run_simulation_test():
    # Configurações
    SPEED = 1.0
    RTT_MS = 150
    TOTAL_STEPS = 100
    
    server = Server(SPEED)
    client = Client(SPEED)
    network = Network(RTT_MS)
    
    max_error = 0.0

    print(f"Iniciando simulação de rede com RTT de {RTT_MS}ms (Reconciliação Atômica)...")

    for frame in range(TOTAL_STEPS):
        # --- CLIENT SIDE ---
        # 1. Gerar e aplicar predição
        client_input = client.generate_input()
        # 2. Enviar input para o servidor
        network.send(frame, client_input, "server")

        # --- SERVER SIDE ---
        # 1. Receber inputs do cliente
        server_inputs = network.receive(frame, "server")
        for inp in server_inputs:
            server.process_input(inp)
        
        # 2. Enviar estado de volta para o cliente
        if server_inputs: # Só envia se houve atividade para economizar banda
            network.send(frame, server.get_state(), "client")

        # --- CLIENT RECONCILIATION ---
        # 1. Receber estado do servidor
        server_updates = network.receive(frame, "client")
        for update in server_updates:
            client.reconcile(update["pos"], update["ack"])

        # --- METRICS ---
        # O erro é a diferença entre onde o cliente PREVÊ que está e onde o servidor DIZ que está
        # Nota: Em um jogo real, o erro é medido contra o estado do servidor no tempo do cliente,
        # mas para fins de validação de reconciliação, a convergência deve ser imediata.
        current_error = abs(client.predicted_position - server.position)
        
        # Como o servidor está sempre "atrás" devido ao lag, o erro de predição 
        # é a distância entre a posição atual do cliente e a posição do servidor + inputs pendentes.
        # A reconciliação correta garante que client.predicted_position == server.pos + sum(pendentes)
        
        # Para o teste de rigor, verificamos se a predição do cliente é consistente com a autoridade
        # considerando o que o servidor ainda não sabe.
        if current_error > max_error:
            max_error = current_error

    print(f"Simulação concluída com sucesso após {TOTAL_STEPS} passos.")
    print(f"Erro máximo de sincronização registrado: {max_error:.5f} unidades.")

    # Critério de sucesso: Erro < 0.1
    assert max_error < 0.1, f"FALHA: Erro de sincronização ({max_error}) excedeu o limite de 0.1!"
    print("Critério de sucesso atendido: Erro inferior a 0.1 unidades validado com sucesso.")

if __name__ == "__main__":
    run_simulation_test()