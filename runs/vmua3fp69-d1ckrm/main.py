import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor

class FencingError(Exception):
    """Exceção lançada quando um token de fencing é obsoleto."""
    pass

class DistributedLockManager:
    """Simula um serviço de lock distribuído (como Redis ou Etcd)."""
    def __init__(self):
        self.locks = {}  # resource_id -> (owner_id, token, expiry)
        self.token_counter = 0
        self.lock = threading.Lock()

    def acquire(self, resource_id, client_id, ttl):
        with self.lock:
            now = time.time()
            current_lock = self.locks.get(resource_id)

            # Se o lock não existe ou expirou
            if not current_lock or now > current_lock[2]:
                self.token_counter += 1
                new_token = self.token_counter
                self.locks[resource_id] = (client_id, new_token, now + ttl)
                return new_token
            return None

class ProtectedResource:
    """Simula um recurso (ex: Banco de Dados) que exige Fencing Tokens."""
    def __init__(self):
        self.value = 0
        self.last_token = 0
        self.lock = threading.Lock()

    def write(self, new_value, token):
        with self.lock:
            if token < self.last_token:
                raise FencingError(f"Rejeitado: Token {token} é obsoleto. Último aceito: {self.last_token}")
            self.last_token = token
            self.value = new_value

def run_race_condition_demo():
    print("\n--- 1. Teste: Race Condition (Sem Lock) ---")
    resource = ProtectedResource()
    
    def increment():
        for _ in range(100):
            current = resource.value
            # Simula tempo de processamento entre leitura e escrita
            time.sleep(0.0001)
            resource.value = current + 1

    threads = [threading.Thread(target=increment) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()
    
    print(f"Valor esperado: 1000 | Valor obtido: {resource.value}")
    print("Resultado: " + ("FALHA (Corrupção)" if resource.value != 1000 else "SUCESSO"))

def run_zombie_process_demo():
    print("\n--- 2. Teste: Processo Zumbi (Lock com TTL, mas SEM Fencing) ---")
    lock_manager = DistributedLockManager()
    # Recurso simplificado que NÃO checa tokens (vulnerável)
    class VulnerableResource:
        def __init__(self): self.value = 0
        def write(self, val): self.value = val

    resource = VulnerableResource()
    
    # Nó A pega o lock
    token_a = lock_manager.acquire("res_1", "Nó_A", ttl=0.1)
    print(f"Nó A adquiriu lock com token {token_a}")

    # Nó A sofre uma "pausa" (simulando GC ou rede) que dura mais que o TTL
    time.sleep(0.2) 

    # Nó B pega o lock (pois o de A expirou)
    token_b = lock_manager.acquire("res_1", "Nó_B", ttl=0.1)
    print(f"Nó B adquiriu lock com token {token_b}")
    resource.write(200, token_b) # Nó B escreve 200
    print(f"Nó B escreveu 200. Valor atual: {resource.value}")

    # Nó A "acorda" e tenta escrever com seu token antigo
    print("Nó A acordou e tenta escrever...")
    resource.write(100, token_a) # Nó A sobrescreve o que B fez!
    
    print(f"Valor final: {resource.value}")
    print("Resultado: " + ("FALHA (Sobrescrita por Zumbi)" if resource.value == 100 else "SUCESSO"))

def run_fencing_solution_demo():
    print("\n--- 3. Teste: Solução com Fencing Tokens ---")
    lock_manager = DistributedLockManager()
    resource = ProtectedResource()

    # Nó A pega o lock
    token_a = lock_manager.acquire("res_1", "Nó_A", ttl=0.1)
    print(f"Nó A adquiriu lock com token {token_a}")

    # Nó A sofre pausa
    time.sleep(0.2)

    # Nó B pega o lock
    token_b = lock_manager.acquire("res_1", "Nó_B", ttl=0.1)
    print(f"Nó B adquiriu lock com token {token_b}")
    resource.write(200, token_b)
    print(f"Nó B escreveu 200. Valor atual: {resource.value}")

    # Nó A tenta escrever
    print("Nó A tenta escrever com token obsoleto...")
    try:
        resource.write(100, token_a)
    except FencingError as e:
        print(f"Sucesso: {e}")

    print(f"Valor final protegido: {resource.value}")

def run_stress_test():
    print("\n--- 4. Teste de Estresse (500 requisições simultâneas) ---")
    lock_manager = DistributedLockManager()
    resource = ProtectedResource()
    num_requests = 500
    
    start_time = time.time()

    def worker(i):
        # Tenta adquirir o lock com um TTL curto
        token = None
        attempts = 0
        while token is None and attempts < 100:
            token = lock_manager.acquire("stress_res", f"client_{i}", ttl=0.05)
            if token is None:
                time.sleep(0.001) # Backoff
                attempts += 1
        
        if token:
            # Operação crítica: ler, incrementar e escrever
            # Nota: Em um sistema real, a leitura também deve ser protegida
            # Aqui simulamos a atomicidade do incremento via lock
            current_val = resource.value
            resource.write(current_val + 1, token)
            return True
        return False

    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(worker, range(num_requests)))

    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
    success_count = sum(1 for r in results if r)

    print(f"Requisições completadas com sucesso: {success_count}/{num_requests}")
    print(f"Valor final do recurso: {resource.value}")
    print(f"Tempo total: {duration_ms:.2f}ms")
    print(f"Latência média estimada por tentativa: {duration_ms/num_requests:.4f}ms")

    if resource.value == num_requests and success_count == num_requests:
        print("RESULTADO: SUCESSO (Consistência mantida)")
    else:
        print("RESULTADO: FALHA (Colisão ou perda de escrita)")

if __name__ == "__main__":
    run_race_condition_demo()
    run_zombie_process_demo()
    run_fencing_solution_demo()
    run_stress_test()