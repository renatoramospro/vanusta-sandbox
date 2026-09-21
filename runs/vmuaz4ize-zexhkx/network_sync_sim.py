import time

class InputCommand:
    def __init__(self, seq, dx):
        self.seq = seq
        self.dx = dx

class State:
    def __init__(self, seq, x):
        self.seq = seq
        self.x = x

class Server:
    def __init__(self):
        self.x = 0.0
        self.last_processed_seq = 0

    def process_input(self, cmd, force_error=False):
        # O servidor é a autoridade. 
        # Se force_error for True, simulamos um evento externo (ex: vento ou colisão)
        error_amount = 0.5 if force_error else 0.0
        self.x += cmd.dx + error_amount
        self.last_processed_seq = cmd.seq
        return State(self.last_processed_seq, self.x)

class Client:
    def __init__(self, server):
        self.server = server
        self.x = 0.0  # Posição lógica (física)
        self.visual_x = 0.0  # Posição visual (renderização)
        self.seq_counter = 0
        self.input_history = [] # Buffer de inputs enviados mas não confirmados
        self.error_threshold = 0.05

    def apply_input(self, dx):
        self.seq_counter += 1
        cmd = InputCommand(self.seq_counter, dx)
        
        # 1. Client-Side Prediction
        self.x += dx
        self.input_history.append(cmd)
        return cmd

    def on_server_update(self, server_state):
        # 2. Server Reconciliation
        # Remove inputs que o servidor já processou
        self.input_history = [i for i in self.input_history if i.seq > server_state.seq]

        # Verificar divergência: Precisamos saber onde o cliente ESTAVA quando o servidor processou esse seq
        # Para simplificar o experimento, vamos comparar a posição atual com a esperada após o rollback
        
        # Simulamos o rollback: voltamos para a posição do servidor
        temp_x = server_state.x
        
        # 3. Re-simulação (Rollback & Re-simulate)
        # Re-aplicamos todos os inputs que ainda estão no buffer (pendentes)
        for cmd in self.input_history:
            temp_x += cmd.dx
        
        # Calcular erro entre a posição predita e a re-simulada
        error = abs(self.x - temp_x)
        
        if error > self.error_threshold:
            print(f"[CLIENT] Divergência detectada! Erro: {error:.4f}. Executando Rollback/Re-simulação...")
            self.x = temp_x
        else:
            # Se o erro for pequeno, apenas limpamos o histórico (opcional dependendo da implementação)
            pass

    def update_visual(self):
        # 4. Visual Smoothing (Interpolação visual para esconder o salto da lógica)
        # Em um jogo real, isso rodaria a cada frame de renderização
        lerp_factor = 0.2
        self.visual_x += (self.x - self.visual_x) * lerp_factor

def run_experiment():
    server = Server()
    client = Client(server)
    
    print("--- Iniciando Simulação de Movimento ---")
    # Passo 1: Cliente se move por 5 frames
    for _ in range(5):
        cmd = client.apply_input(1.0)
        # Simula latência: o servidor processa o input com atraso
        server_state = server.process_input(cmd)
        # O cliente recebe o estado do servidor (com latência)
        client.on_server_update(server_state)
        client.update_visual()
        print(f"Frame: Client_X={client.x:.1f}, Visual_X={client.visual_x:.2f}")

    print("\n--- Introduzindo Erro no Servidor (Ex: Colisão/Vento) ---")
    # Passo 2: O servidor sofre um erro de posição (ex: o cliente bateu em algo que o servidor viu mas o cliente não)
    cmd = client.apply_input(1.0)
    # O servidor processa com um erro de 0.5 unidades
    server_state = server.process_input(cmd, force_error=True)
    
    # O cliente recebe o estado do servidor
    client.on_server_update(server_state)
    client.update_visual()
    
    print(f"Após Reconciliação -> Client_X (Lógica): {client.x:.2f}, Visual_X: {client.visual_x:.2f}")
    
    # Verificação de sucesso
    # O erro de posição após reconciliação deve ser < 0.05 em relação ao que o servidor determinou + inputs pendentes
    # No nosso caso, o cliente deve ter convergido para a lógica do servidor.
    
    # Teste de erro de posição (comparando com a autoridade do servidor)
    # Como não há mais inputs pendentes no buffer após o processamento do erro, 
    # o client.x deve ser exatamente o server.x
    final_error = abs(client.x - server.x)
    print(f"\nErro Final de Posição (Lógica vs Servidor): {final_error:.4f}")
    
    if final_error < 0.05:
        print("RESULTADO: SUCESSO - Reconciliação precisa.")
    else:
        print("RESULTADO: FALHA - Erro de posição acima do limite.")

if __name__ == "__main__":
    run_experiment()