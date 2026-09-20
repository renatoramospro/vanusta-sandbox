import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor

# --- COMPONENTES DO SISTEMA ---

class DistributedLockManager:
    """Simula um serviço central de gerenciamento de locks (ex: Redis/Etcd)."""
    def __init__(self):
        self.locks = {}  # key -> (owner_id, expiry, token)
        self.token_counter = 0
        self.internal_lock = threading.Lock()

    def acquire(self, key, owner_id, ttl_seconds):
        with self.internal_lock:
            now = time.time()
            current_lock = self.locks.get(key)

            # Verifica se o lock existe e se ainda é válido
            if current_lock:
                owner, expiry, token = current_lock
                if now < expiry:
                    return None  # Lock ainda ocupado

            # Concede novo lock
            self.token_counter += 1
            new_token = self.token_counter
            expiry = now + ttl_seconds
            self.locks[key] = (owner_id, expiry, new_token)
            return new_token

    def release(self, key, owner_id):
        with self.internal_lock:
            current_lock = self.locks.get(key)
            if current_lock and current_lock[0] == owner_id:
                del self.locks[key]

class ProtectedResource:
    """O recurso que deve ser protegido contra corrupção."""
    def __init__(self, mode="fencing"):
        self.value = 0
        self.mode = mode
        self.last_token = 0
        self.lock = threading.Lock()

    def write(self, new_value, token):
        with self.lock:
            if self.mode == "fencing":
                # Lógica de Fencing: Rejeita tokens antigos (zumbis)
                if token < self.last_token:
                    return False, f"REJEITADO: Token {token} é inferior ao último aceito ({self.last_token})"
                self.last_token = token
            
            self.value = new_value
            return True, "OK"

# --- CENÁRIOS DE TESTE ---

def run_race_condition_demo():
    print("\n--- 1. Teste: Race Condition (Sem Lock) ---")
    resource = ProtectedResource(mode="none")
    
    def increment():
        for _ in range(10):
            current = resource.value
            time.sleep(0.0001) # Força a troca de contexto
            resource.value = current + 1

    threads = [threading.Thread(target=increment) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()

    print(f"Valor esperado: 100 | Valor obtido: {resource.value}")
    if resource.value != 100:
        print("Resultado: FALHA (Corrupção detectada)")
    else:
        print("Resultado: SUCESSO")

def run_zombie_process_demo():
    print("\n--- 2. Teste: Processo Zumbi (Lock com TTL, mas SEM Fencing) ---")
    lock_manager = DistributedLockManager()
    # Usamos o modo 'none' para simular um recurso que não valida tokens
    resource = ProtectedResource(mode="none") 

    # Nó A: Adquire lock, mas "trava" (simula GC pause)
    token_a = lock_manager.acquire("res_1", "Nó_A", ttl_seconds=0.1)
    print(f"Nó A adquiriu lock com token {token_a}")

    # Nó B: Adquire lock após o TTL de A expirar
    time.sleep(0.2)
    token_b = lock_manager.acquire("res_1", "Nó_B", ttl_seconds=0.1)
    print(f"Nó B adquiriu lock com token {token_b}")
    resource.write(200, token_b)
    print(f"Nó B escreveu 200 no recurso.")

    # Nó A "acorda" e tenta escrever com seu token antigo
    print("Nó A acordou e tenta escrever...")
    success, msg = resource.write(100, token_a)
    print(f"Nó A tentativa de escrita: {msg}")

    if resource.value == 100:
        print("Resultado: FALHA (Nó A sobrescreveu o Nó B - Corrupção!)")
    else:
        print("Resultado: SUCESSO")

def run_fencing_solution_demo():
    print("\n--- 3. Teste: Solução com Fencing Tokens ---")
    lock_manager = DistributedLockManager()
    resource = ProtectedResource(mode="fencing")

    # Nó A: Adquire lock, mas "trava"
    token_a = lock_manager.acquire("res_1", "Nó_A", ttl_seconds=0.1)
    print(f"Nó A adquiriu lock com token {token_a}")

    # Nó B: Adquire lock após o TTL de A expirar
    time.sleep(0.2)
    token_b = lock_manager.acquire("res_1", "Nó_B", ttl_seconds=0.1)
    print(f"Nó B adquiriu lock com token {token_b}")
    resource.write(200, token_b)
    print(f"Nó B escreveu 200 no recurso.")

    # Nó A "acorda" e tenta escrever
    print("Nó A acordou e tenta escrever...")
    success, msg = resource.write(100, token_a)
    print(f"Nó A tentativa de escrita: {msg}")

    if resource.value == 200:
        print("Resultado: SUCESSO (Fencing impediu a corrupção)")
    else:
        print(f"Resultado: FALHA (Valor final: {resource.value})")

def run_stress_test():
    print("\n--- 4. Teste de Estresse: 500 Requisições Simultâneas ---")
    lock_manager = DistributedLockManager()
    resource = ProtectedResource(mode="fencing")
    total_increments = 500
    
    def worker():
        # Tenta adquirir o lock com retry (backoff simples)
        token = None
        while token is None:
            token = lock_manager.acquire("stress_key", threading.current_thread().name, ttl_seconds=0.05)
            if token is None:
                time.sleep(0.001)
        
        # Operação crítica
        current_val = resource.value
        # Simula processamento
        time.sleep(0.0001)
        success, _ = resource.write(current_val + 1, token)
        
        if success:
            lock_manager.release("stress_key", threading.current_thread().name)
        else:
            # Se falhar por fencing (improvável aqui), não libera para não travar
            pass

    start_time = time.time()
    with ThreadPoolExecutor(max_workers=50) as executor:
        for _ in range(total_increments):
            executor.submit(worker)
    
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
    
    print(f"Valor esperado: {total_increments} | Valor obtido: {resource.value}")
    print(f"Tempo total: {duration_ms:.2f}ms")
    
    if resource.value == total_increments:
        print("Resultado: SUCESSO (Zero colisões)")
    else:
        print("Resultado: FALHA (Colisões detectadas)")

if __name__ == "__main__":
    run_race_condition_demo()
    run_zombie_process_demo()
    run_fencing_solution_demo()
    run_stress_test()