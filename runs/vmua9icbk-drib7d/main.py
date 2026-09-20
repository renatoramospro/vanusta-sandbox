import threading
import time
import uuid
from enum import Enum
from typing import Dict, Any, Optional

# --- Domínio de Negócio ---

class ExecutionStatus(Enum):
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class BusinessService:
    """Simula um serviço que realiza uma operação custosa (ex: cobrança)."""
    def __init__(self):
        self.execution_count = 0
        self.lock = threading.Lock()

    def execute(self, data: str) -> str:
        # Simula um delay de processamento para aumentar a janela de race condition
        time.sleep(0.05) 
        with self.lock:
            self.execution_count += 1
        return f"Sucesso: Processado '{data}'"

# --- Infraestrutura de Idempotência ---

class IdempotencyStore:
    """Simula um armazenamento distribuído (como Redis) com operações atômicas."""
    def __init__(self):
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def try_lock_and_start(self, key: str) -> bool:
        """Simula o comando SET key value NX (Set if Not eXists)."""
        with self._lock:
            if key in self._storage:
                return False
            self._storage[key] = {"status": ExecutionStatus.STARTED, "response": None}
            return True

    def set_completed(self, key: str, response: Any):
        with self._lock:
            if key in self._storage:
                self._storage[key] = {"status": ExecutionStatus.COMPLETED, "response": response}

    def get_entry(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._storage.get(key)

# --- Middlewares ---

class RobustIdempotencyMiddleware:
    """Implementação correta usando atomicidade e estados."""
    def __init__(self, store: IdempotencyStore):
        self.store = store

    def handle(self, key: str, service_call, *args):
        start_time = time.perf_counter()
        
        # 1. Tenta obter o lock atômico (SET NX)
        if not self.store.try_lock_and_start(key):
            entry = self.store.get_entry(key)
            if entry and entry["status"] == ExecutionStatus.STARTED:
                return "ERROR: 409 Conflict (Processamento em curso)", 0
            elif entry and entry["status"] == ExecutionStatus.COMPLETED:
                return entry["response"], 0 # Retorna cache
            return "ERROR: 500 Internal Error", 0

        # 2. Executa a lógica de negócio
        try:
            result = service_call(*args)
            self.store.set_completed(key, result)
            latency = (time.perf_counter() - start_time) * 1000
            return result, latency
        except Exception:
            # Em caso de erro, poderíamos remover a chave para permitir retry
            return "ERROR: 500", 0

class BrokenIdempotencyMiddleware:
    """Implementação errada (Check-then-Act) vulnerável a Race Conditions."""
    def __init__(self, store: IdempotencyStore):
        self.store = store

    def handle(self, key: str, service_call, *args):
        start_time = time.perf_counter()
        
        # ERRO: A verificação e a escrita não são atômicas
        entry = self.store.get_entry(key)
        if entry and entry["status"] == ExecutionStatus.COMPLETED:
            return entry["response"], 0
        
        # Janela de vulnerabilidade: se duas threads chegarem aqui, ambas prosseguem
        # Simulando o tempo de rede/processamento entre o check e o set
        time.sleep(0.01) 
        
        # Forçando o estado de started de forma não atômica
        self.store._storage[key] = {"status": ExecutionStatus.STARTED, "response": None}
        
        try:
            result = service_call(*args)
            self.store.set_completed(key, result)
            latency = (time.perf_counter() - start_time) * 1000
            return result, latency
        except Exception:
            return "ERROR: 500", 0

# --- Test Runner ---

def run_test(middleware_class, store_class, label):
    print(f"\n--- Testando: {label} ---")
    service = BusinessService()
    store = store_class()
    middleware = middleware_class(store)
    
    idempotency_key = str(uuid.uuid4())
    payload = "transacao_123"
    
    threads = []
    results = []
    latencies = []

    def worker():
        res, lat = middleware.handle(idempotency_key, service.execute, payload)
        results.append(res)
        if lat > 0: latencies.append(lat)

    # Dispara 100 requisições simultâneas
    for _ in range(100):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Validação
    unique_results = set(results)
    # O número de execuções reais do serviço deve ser 1
    actual_executions = service.execution_count
    
    print(f"Execuções reais do serviço: {actual_executions}")
    print(f"Resultados únicos recebidos: {len(unique_results)}")
    if latencies:
        print(f"Overhead médio do middleware: {sum(latencies)/len(latencies):.4f}ms")

    success = (actual_executions == 1)
    print(f"RESULTADO: {'✅ PASSOU' if success else '❌ FALHOU'}")
    return success

if __name__ == "__main__":
    # Teste 1: Middleware Robusto
    robust_pass = run_test(RobustIdempotencyMiddleware, IdempotencyStore, "Middleware Robusto (Atômico)")
    
    # Teste 2: Middleware Quebrado
    broken_pass = run_test(BrokenIdempotencyMiddleware, IdempotencyStore, "Middleware Quebrado (Check-then-Act)")

    if robust_pass and not broken_pass:
        print("\nConclusão: O experimento demonstrou que a atomicidade é essencial para evitar duplicidade.")
    else:
        print("\nConclusão: O experimento não atingiu o comportamento esperado.")