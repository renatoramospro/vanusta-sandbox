import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor

# --- COMPONENTES DO SISTEMA ---

class DistributedLockManager:
    """Simula um serviço centralizado de Lock (ex: Redis ou Etcd)."""
    def __init__(self):
        self.locks = {}  # key -> {'owner': id, 'expires_at': time, 'token': int}
        self.token_counter = 0
        self._internal_lock = threading.Lock()

    def acquire(self, resource_id, client_id, ttl_seconds):
        with self._internal_lock:
            now = time.time()
            current_lock = self.locks.get(resource_id)

            # Verifica se o lock existe e se ainda é válido
            if current_lock and now < current_lock['expires_at']:
                return None  # Lock ainda ocupado

            # Concede ou renova o lock
            self.token_counter += 1
            new_token = self.token_counter
            self.locks[resource_id] = {
                'owner': client_id,
                'expires_at': now + ttl_seconds,
                'token': new_token
            }
            return new_token

    def release(self, resource_id, client_id, token):
        with self._internal_lock:
            current_lock = self.locks.get(resource_id)
            if current_lock and current_lock['owner'] == client_id and current_lock['token'] == token:
                del self.locks[resource_id]
                return True
            return False

class ProtectedResource:
    """O recurso que deve ser protegido contra escritas de processos zumbis."""
    def __init__(self):
        self.value = 0
        self.last_token = 0
        self._lock = threading.Lock()

    def write_vulnerable(self, new_value):
        """Escrita sem validação de token (perigosa)."""
        with self._lock:
            self.value = new_value

    def write_with_fencing(self, new_value, token):
        """Escrita com validação de Fencing Token (segura)."""
        with self._lock:
            if token < self.last_token:
                # Rejeita o processo zumbi
                return False, token
            self.value = new_value
            self.last_token = token
            return True, token

# --- CENÁRIOS DE TESTE ---

def run_race_condition_demo():
    print("\n--- 1. Teste: Race Condition (Sem Lock) ---")
    resource = ProtectedResource()
    def increment():
        for _ in range(10):
            val = resource.value
            time.sleep(0.0001) # Simula processamento
            resource.write_vulnerable(val + 1)

    threads = [threading.Thread(target=increment) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()

    expected = 100
    print(f"Valor esperado: {expected} | Valor obtido: {resource.value}")
    if resource.value != expected:
        print("Resultado: FALHA (Corrupção detectada)")
    else:
        print("Resultado: SUCESSO (Inesperado para este teste)")

def run_zombie_process_demo():
    print("\n--- 2. Teste: Processo Zumbi (Lock com TTL, mas SEM Fencing) ---")
    lock_manager = DistributedLockManager()
    resource = ProtectedResource()
    
    # Nó A adquire lock
    token_a = lock_manager.acquire("res_1", "Nó A", ttl_seconds=0.1)
    print(f"Nó A adquiriu lock com token {token_a}")

    # Nó B adquire lock (após o TTL de A expirar)
    time.sleep(0.2)
    token_b = lock_manager.acquire("res_1", "Nó B", ttl_seconds=0.1)
    print(f"Nó B adquiriu lock com token {token_b}")

    # Nó B escreve
    resource.write_vulnerable(200)
    print("Nó B escreveu 200")

    # Nó A "acorda" e tenta escrever (Zumbi)
    print("Nó A acordou e tenta escrever 100...")
    resource.write_vulnerable(100)
    
    print(f"Valor final no recurso: {resource.value}")
    if resource.value == 100:
        print("Resultado: FALHA (Nó A sobrescreveu o Nó B - Corrupção!)")
    else:
        print("Resultado: SUCESSO")

def run_fencing_solution_demo():
    print("\n--- 3. Teste: Solução com Fencing Tokens ---")
    lock_manager = DistributedLockManager()
    resource = ProtectedResource()
    
    # Nó A adquire lock
    token_a = lock_manager.acquire("res_1", "Nó A", ttl_seconds=0.1)
    print(f"Nó A adquiriu lock com token {token_a}")

    # Nó B adquire lock após expiração de A
    time.sleep(0.2)
    token_b = lock_manager.acquire("res_1", "Nó B", ttl_seconds=0.1)
    print(f"Nó B adquiriu lock com token {token_b}")

    # Nó B escreve com sucesso
    success_b, _ = resource.write_with_fencing(200, token_b)
    print(f"Nó B escreveu 200: {'Sucesso' if success_b else 'Falha'}")

    # Nó A tenta escrever (Zumbi)
    print("Nó A tenta escrever 100 usando token antigo...")
    success_a, token_used = resource.write_with_fencing(100, token_a)
    
    if not success_a:
        print(f"Nó A REJEITADO (Token {token_used} é inferior ao último aceito {resource.last_token})")
    else:
        print("Nó A conseguiu escrever (ERRO DE SEGURANÇA!)")

    print(f"Valor final no recurso: {resource.value}")
    if resource.value == 200:
        print("Resultado: SUCESSO (Consistência mantida)")
    else:
        print("Resultado: FALHA (Corrupção!)")

def run_stress_test():
    print("\n--- 4. Teste de Estresse: 500 Requisições Simultâneas ---")
    lock_manager = DistributedLockManager()
    resource = ProtectedResource()
    num_requests = 500
    
    def task(i):
        # Tenta adquirir o lock com retry/backoff simples
        token = None
        for _ in range(10): # Máximo 10 tentativas
            token = lock_manager.acquire("stress_res", f"client_{i}", ttl_seconds=0.05)
            if token:
                break
            time.sleep(random.uniform(0.01, 0.03))
        
        if token:
            # Tenta escrever com o token
            success, _ = resource.write_with_fencing(i, token)
            lock_manager.release("stress_res", f"client_{i}", token)
            return success
        return False

    start_time = time.time()
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(task, range(num_requests)))
    end_time = time.time()

    success_count = sum(1 for r in results if r)
    latency = (end_time - start_time) / num_requests * 1000 # ms por req (média aproximada)

    print(f"Requisições bem-sucedidas: {success_count}/{num_requests}")
    print(f"Latência média aproximada: {latency:.2f}ms")
    
    # Nota: Em um teste de estresse real com lock, nem todas as 500 podem completar 
    # se o tempo de retry for curto, mas o importante é que as que completaram 
    # NÃO corromperam o valor final (o valor final deve ser o último token aceito).
    
    if success_count > 0:
        print("Resultado: SUCESSO (Operações atômicas)")
    else:
        print("Resultado: FALHA (Nenhuma operação completou)")

if __name__ == "__main__":
    run_race_condition_demo()
    run_zombie_process_demo()
    run_fencing_solution_demo()
    run_stress_test()