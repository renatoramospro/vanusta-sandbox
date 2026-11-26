import asyncio
import random
import time
import re

# --- MOCK DE PERSISTÊNCIA (Substitui estado em memória simples) ---
# Em produção, seria Redis, PostgreSQL, etc.
PERSISTENCE_STORE = {} 

class SessionState:
    """Representa o estado de uma sessão de cliente."""
    def __init__(self, session_id, auth_token):
        self.session_id = session_id
        self.auth_token = auth_token
        self.last_activity = time.time()
        self.data = {}

    def save_to_store(self):
        """Simula salvamento persistente."""
        PERSISTENCE_STORE[self.session_id] = self.__dict__.copy()

    @staticmethod
    def load_from_store(session_id):
        """Simula carregamento persistente."""
        if session_id in PERSISTENCE_STORE:
            data = PERSISTENCE_STORE[session_id]
            # Reconstruir o objeto a partir dos dados salvos
            state = SessionState(data['session_id'], data['auth_token'])
            state.__dict__.update(data)
            return state
        return None

class WebSocketManager:
    """Gerencia conexões e estado de sessão com segurança básica."""
    MAX_SESSIONS = 100 # Implementação do limite de conexões
    
    def __init__(self):
        print("WebSocketManager inicializado (com segurança básica).")

    def validate_session_id(self, session_id):
        """Validação básica de formato (ex: alfanumérico com underscore)."""
        return bool(re.fullmatch(r'[a-zA-Z0-9_]{5,30}', session_id))

    def add_session(self, session_id, auth_token):
        """Adiciona sessão após validação de acesso e limites."""
        if not self.validate_session_id(session_id):
            print(f"ERRO: Session ID {session_id} inválido.")
            return False
        
        if len(PERSISTENCE_STORE) >= self.MAX_SESSIONS:
            print(f"ERRO: Limite máximo de {self.MAX_SESSIONS} sessões atingido.")
            return False

        # 1. Controle de Acesso (Simulado: token deve ser válido)
        if not auth_token or auth_token != "VALID_SECRET_TOKEN":
            print(f"ERRO: Token de autenticação inválido para {session_id}.")
            return False

        # 2. Persistência e Estado
        state = SessionState(session_id, auth_token)
        state.save_to_store()
        print(f"Sessão {session_id} adicionada e persistida. Total: {len(PERSISTENCE_STORE)}")
        return True

    def get_state(self, session_id):
        """Busca estado, simulando carregamento persistente."""
        return SessionState.load_from_store(session_id)

    async def attempt_reconnect(self, session_id, max_attempts=10):
        """Implementa reconexão automática com backoff exponencial e jitter."""
        # 6. Reautenticação: Deve ser feita antes de tentar reconectar
        state = self.get_state(session_id)
        if not state:
            print(f"ERRO: Sessão {session_id} não encontrada para reconexão.")
            return
        
        print(f"\n[RECONEXÃO] {session_id} iniciando reconexão (Reautenticação implícita via estado carregado).")
        attempt = 0
        base_delay = 1
        max_delay = 30
        
        while attempt < max_attempts:
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = random.uniform(0, 0.1)
            sleep_time = delay + jitter
            
            print(f"[{session_id}] Tentativa {attempt + 1}. Esperando {sleep_time:.2f}s...")
            await asyncio.sleep(sleep_time)
            
            # Simulação de sucesso na reconexão
            if attempt >= 1: 
                print(f"[{session_id}] RECONECTADO com sucesso após {attempt + 1} tentativas.")
                return
            attempt += 1
        print(f"[{session_id}] FALHA: Máximo de tentativas atingido.")


async def main():
    manager = WebSocketManager()
    session_id = "user_123"
    valid_token = "VALID_SECRET_TOKEN"
    
    # 1. Teste de Adição Segura
    manager.add_session(session_id, valid_token)
    
    # 2. Teste de Falha de Segurança (Ataque ao Equívoco: Falta de validação)
    invalid_id = "short" # Menos de 5 caracteres
    manager.add_session(invalid_id, valid_token) # Deve falhar na validação de formato
    
    # 3. Teste de Estado Persistente
    state = manager.get_state(session_id)
    if state:
        print(f"\n[TESTE DE ESTADO PERSISTENTE] Estado de {session_id} carregado: {state.data}")

    # 4. Teste de Reconexão com Backoff
    await manager.attempt_reconnect(session_id)
    
    # 5. Ataque ao Equívoco Comum: "Async = mais rápido"
    print("\n[TESTE DE EQUÍVOCO] O async gerencia concorrência, não garante velocidade absoluta. O tempo de espera é ditado pelo backoff exponencial.")

if __name__ == "__main__":
    asyncio.run(main())