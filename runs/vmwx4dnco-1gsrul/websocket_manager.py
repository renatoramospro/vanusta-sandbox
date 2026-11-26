import asyncio
import random
import time

class SessionState:
    """Representa o estado de uma sessão de cliente."""
    def __init__(self, session_id):
        self.session_id = session_id
        self.last_activity = time.time()
        self.data = {}

class WebSocketManager:
    """Gerencia conexões e estado de sessão."""
    def __init__(self):
        self.sessions = {}  # {session_id: SessionState}
        self.connections = {} # {session_id: websocket_object} (Simulado aqui)
        print("WebSocketManager inicializado.")

    def add_session(self, session_id):
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionState(session_id)
            print(f"Sessão {session_id} adicionada. Estado inicial criado.")
            return True
        return False

    def get_state(self, session_id):
        return self.sessions.get(session_id)

    async def attempt_reconnect(self, session_id, max_attempts=10):
        """Implementa reconexão automática com backoff exponencial e jitter."""
        attempt = 0
        base_delay = 1  # Intervalo inicial em segundos
        max_delay = 30
        
        while attempt < max_attempts:
            # Cálculo do backoff exponencial: base_delay * (2 ** attempt)
            delay = min(base_delay * (2 ** attempt), max_delay)
            
            # Adição de jitter (0-100ms = 0.1s)
            jitter = random.uniform(0, 0.1)
            sleep_time = delay + jitter
            
            print(f"[{session_id}] Tentativa {attempt+1}. Esperando {sleep_time:.2f}s...")
            await asyncio.sleep(sleep_time)
            
            # --- SIMULAÇÃO DE CONEXÃO ---
            # Em um cenário real, aqui haveria a chamada ao cliente WebSocket
            success = random.random() > 0.3 # 70% de chance de sucesso simulado
            
            if success:
                print(f"[{session_id}] RECONECTADO com sucesso após {attempt+1} tentativas.")
                # Atualizar estado de conexão (simulado)
                self.connections[session_id] = True 
                return True
            
            attempt += 1
        
        print(f"[{session_id}] FALHA CRÍTICA: Máximo de tentativas ({max_attempts}) atingido.")
        return False

async def main():
    manager = WebSocketManager()
    session_id = "user_123"
    manager.add_session(session_id)

    # 1. Teste de Estado
    state = manager.get_state(session_id)
    print(f"\n[TESTE DE ESTADO] Estado de {session_id}: {state.data}")

    # 2. Teste de Reconexão com Backoff
    print("\n--- Iniciando Teste de Reconexão ---")
    await manager.attempt_reconnect(session_id, max_attempts=5)
    
    # 3. Ataque ao Equívoco Comum: "Async = mais rápido"
    # Demonstração: A concorrência (async) permite gerenciar múltiplos estados sem bloquear, 
    # mas o tempo total de espera (backoff) é determinado pela lógica, não apenas pela natureza async.
    print("\n[TESTE DE EQUÍVOCO] O async gerencia concorrência, não garante velocidade absoluta.")
    
if __name__ == "__main__":
    asyncio.run(main())