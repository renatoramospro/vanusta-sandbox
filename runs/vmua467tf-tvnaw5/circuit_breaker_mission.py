import time
import threading
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreakerError(Exception):
    """Exceção lançada quando o circuito está aberto (fail-fast)."""
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=2):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
        self._lock = threading.Lock()

    def call(self, func, *args, **kwargs):
        with self._lock:
            self._check_state()
            
            if self.state == CircuitState.OPEN:
                raise CircuitBreakerError("Circuito está ABERTO. Fail-fast ativado.")

        # Se chegou aqui, estamos em CLOSED ou HALF_OPEN
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _check_state(self):
        """Verifica se o tempo de espera expirou para tentar o HALF_OPEN."""
        if self.state == CircuitState.OPEN and self.last_failure_time:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                print(f"--- [Estado] Transição automática: OPEN -> HALF_OPEN ---")
                self.state = CircuitState.HALF_OPEN

    def _on_success(self):
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                print(f"--- [Estado] Recuperação detectada: HALF_OPEN -> CLOSED ---")
            self.state = CircuitState.CLOSED
            self.failure_count = 0

    def _on_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
                if self.state != CircuitState.OPEN:
                    print(f"--- [Estado] Limite de falhas atingido: {self.failure_count} -> OPEN ---")
                self.state = CircuitState.OPEN

# --- Simulação de Dependência Externa ---

class ExternalService:
    def __init__(self):
        self.should_fail = False

    def request(self):
        if self.should_fail:
            raise ConnectionError("Falha na dependência externa!")
        return "Sucesso!"

# --- Testes de Comportamento ---

def run_experiment():
    service = ExternalService()
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=2)

    print("1. Testando fluxo normal (CLOSED)...")
    for _ in range(3):
        print(f"Resultado: {cb.call(service.request)}")

    print("\n2. Provocando falhas para abrir o circuito...")
    service.should_fail = True
    for i in range(3):
        try:
            cb.call(service.request)
        except Exception as e:
            print(f"Falha {i+1}: {e}")

    print("\n3. Testando Fail-Fast (Circuito deve estar OPEN)...")
    try:
        cb.call(service.request)
    except CircuitBreakerError as e:
        print(f"Capturado esperado: {e}")

    print("\n4. Aguardando tempo de recuperação (Sleep Window)...")
    time.sleep(2.1)

    print("\n5. Testando Recuperação (HALF_OPEN -> CLOSED)...")
    service.should_fail = False  # Serviço voltou a funcionar
    print(f"Resultado após recuperação: {cb.call(service.request)}")
    print(f"Estado final: {cb.state}")

    print("\n6. Testando Concorrência (Thread-Safety)...")
    # Vamos disparar várias threads simultâneas enquanto o circuito está fechado
    # para garantir que o contador e o estado não corrompam.
    def concurrent_task(idx):
        try:
            res = cb.call(service.request)
            return f"T{idx}: {res}"
        except Exception as e:
            return f"T{idx}: {e}"

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(concurrent_task, range(10)))
    
    for r in results:
        print(r)

if __name__ == "__main__":
    run_experiment()