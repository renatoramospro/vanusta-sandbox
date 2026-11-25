import time
import threading
import random
from collections import deque

# --- Configurações da Missão ---
RATE_LIMIT_PER_SECOND = 100.0
BURST_CAPACITY = 20
TOTAL_REQUESTS = 10000
TEST_DURATION = 10.0  # segundos
NUM_WORKERS = 50

# --- Estruturas de Estado por Chave ---
class TokenBucket:
    def __init__(self, capacity, rate):
        self.capacity = capacity
        self.rate = rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def allow(self, cost=1):
        with self.lock:
            self.refill()
            if self.tokens >= cost:
                self.tokens -= cost
                return True
            return False

class SlidingWindow:
    def __init__(self, capacity, window_seconds):
        self.capacity = capacity
        self.window_seconds = window_seconds
        # Deque armazena timestamps das requisições
        self.timestamps = deque()
        self.lock = threading.Lock()

    def allow(self):
        with self.lock:
            now = time.time()
            # Remove timestamps fora da janela deslizante
            while self.timestamps and self.timestamps[0] < now - self.window_seconds:
                self.timestamps.popleft()
            
            # Verifica se o número de requisições dentro da janela é menor que a capacidade
            if len(self.timestamps) < self.capacity:
                self.timestamps.append(now)
                return True
            return False

# --- Rate Limiter Híbrido (Thread-Safe por Chave) ---
class HybridRateLimiter:
    def __init__(self, rate_limit, burst, window_sec):
        # Estrutura para armazenar estados por chave (simulando um cache com TTL implícito)
        self.key_states = {}
        self.global_lock = threading.Lock()
        
        # Configuração: 100 req/s -> Janela de 1s com capacidade 100
        self.window_capacity = int(rate_limit)
        self.window_seconds = 1.0
        
        # Configuração: Burst 20, Taxa 100/s
        self.bucket_capacity = burst
        self.bucket_rate = rate_limit

    def _get_state(self, key):
        with self.global_lock:
            if key not in self.key_states:
                # Inicializa os componentes para a nova chave
                self.key_states[key] = {
                    "tb": TokenBucket(self.bucket_capacity, self.bucket_rate),
                    "sw": SlidingWindow(self.window_capacity, self.window_seconds)
                }
            return self.key_states[key]

    # Lógica de Decisão: Prioriza TB para burst, usa SW para garantir a média.
    # Aceita se TB permitir OU se SW permitir (para não ser excessivamente restritivo,
    # mas o critério de sucesso exige que o limite seja o mais estrito, então usamos E).
    # CORREÇÃO: Para garantir o limite estrito (100/s), a decisão deve ser E (AND).
    def allow(self, key: str) -> bool:
        state = self._get_state(key)
        
        # Decisão estrita: Deve passar por ambos para garantir tanto o burst quanto a média
        tb_allowed = state["tb"].allow()
        sw_allowed = state["sw"].allow()
        
        return tb_allowed and sw_allowed

# --- Simulação de Carga ---
def worker(limiter: HybridRateLimiter, worker_id: int, results: list, start_time: float):
    key = f"user_{worker_id % 10}" # Quota por 10 chaves
    
    # Simula requisições em um intervalo aleatório para imitar tráfego real
    for i in range(TOTAL_REQUESTS // NUM_WORKERS + 1):
        # Pausa curta para simular latência e distribuir a carga
        time.sleep(random.uniform(0.001, 0.01)) 
        
        if time.time() - start_time > TEST_DURATION + 1: # Limita o tempo de execução
            break
            
        if limiter.allow(key):
            results.append(True) # Aceito
        else:
            results.append(False) # Rejeitado

# --- Execução do Experimento ---
if __name__ == "__main__":
    print("--- Iniciando Experimento de Rate Limiter Híbrido ---")
    
    # Inicializa o limitador
    limiter = HybridRateLimiter(
        rate_limit=RATE_LIMIT_PER_SECOND, 
        burst=BURST_CAPACITY, 
        window_sec=1.0
    )
    
    results = []
    threads = []
    start_time = time.time()
    
    # Inicia os workers
    for i in range(NUM_WORKERS):
        t = threading.Thread(target=worker, args=(limiter, i, results, start_time))
        threads.append(t)
        t.start()
        
    # Espera todos os threads terminarem
    for t in threads:
        t.join()
        
    end_time = time.time()
    
    accepted_count = sum(results)
    rejected_count = len(results) - accepted_count
    
    print("\n--- Resultados Finais ---")
    print(f"Tempo total de execução: {end_time - start_time:.2f}s")
    print(f"Total de requisições processadas: {len(results)}")
    print(f"Requisições ACEITAS: {accepted_count}")
    print(f"Requisições REJEITADAS: {rejected_count}")
    
    # Critério de Sucesso: 100 req/s * 10s + Burst 20 = 1020
    expected_accepted = int(RATE_LIMIT_PER_SECOND * TEST_DURATION) + BURST_CAPACITY
    
    print("\n--- Verificação dos Critérios de Sucesso ---")
    
    # Critério 1: Limite teórico (1020)
    if accepted_count == expected_accepted:
        print(f"✅ CRITÉRIO 1 (Limite Teórico): SUCESSO. Aceitos ({accepted_count}) == Esperado ({expected_accepted}).")
    else:
        print(f"❌ CRITÉRIO 1 (Limite Teórico): FALHA. Aceitos ({accepted_count}) != Esperado ({expected_accepted}).")

    # Critério 2: Erro < 1% em 10000 requisições (Taxa de rejeição esperada: 10000 - 1020 = 8980)
    # A taxa de rejeição deve ser ~89.8%. O critério <1% se refere a Falsos Positivos (aceitar o que deveria ser rejeitado).
    # Como a lógica é AND (estrita), Falsos Positivos são 0.
    if rejected_count >= (TOTAL_REQUESTS - expected_accepted) * 0.99: # Verifica se a rejeição está próxima do esperado
        print("✅ CRITÉRIO 2 (Taxa de Rejeição): SUCESSO. Rejeições próximas ao esperado (~89.8%).")
    else:
        print("❌ CRITÉRIO 2 (Taxa de Rejeição): FALHA. Rejeições muito distantes do esperado.")

    # Critério 3: Thread-Safety (Verificado pela contagem exata)
    if len(results) == TOTAL_REQUESTS and accepted_count == expected_accepted:
        print("✅ CRITÉRIO 3 (Thread-Safety): SUCESSO. Contagem exata alcançada sob concorrência.")
    else:
        print("❌ CRITÉRIO 3 (Thread-Safety): FALHA. Contagem total ou aceita incorreta, indicando race condition ou falha de execução.")

    # Ataque ao Equívoco Comum (TB || SW):
    # Se usássemos OR (TB || SW), o limitador seria mais frouxo. O TB sozinho aceitaria 20, depois 100/s.
    # A SW sozinha aceitaria 100/s. Usar OR resultaria em aceitar mais que 1020 (ex: 10000), violando o limite estrito.
    print("\n--- Ataque ao Equívoco Comum (TB || SW) ---")
    print("Se a lógica fosse OR (TB || SW), o limitador seria mais frouxo, permitindo mais de 1020 requisições, violando o limite estrito.")
    print("A lógica AND (TB && SW) garante que ambos os requisitos (burst e média) são atendidos simultaneamente.")