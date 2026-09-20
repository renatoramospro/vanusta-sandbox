import threading
import time
from enum import Enum
from typing import Callable, Any, Type, Tuple

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreakerError(Exception):
    """Exceção lançada quando o circuito está aberto."""
    pass

class BusinessError(Exception):
    """Exceção de negócio que não deve afetar o circuito."""
    pass

class DependencyError(Exception):
    """Exceção de infraestrutura que deve disparar o circuito."""
    pass

class CircuitBreaker:
    def __init__(
        self, 
        failure_threshold: int = 3, 
        recovery_timeout: float = 1.0,
        expected_exceptions: Tuple[Type[Exception], ...] = (DependencyError,)
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self._lock = threading.Lock()
        self._half_open_test_in_progress = False

    def _check_state_transition(self):
        """Verifica se o tempo de espera expirou para tentar recuperar o circuito."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self._half_open_test_in_progress = False

    def _on_success(self):
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0

    def _on_failure(self, error: Exception):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        with self._lock:
            self._check_state_transition()
            
            if self.state == CircuitState.OPEN:
                raise CircuitBreakerError("Circuito está ABERTO. Fail-fast ativado.")
            
            if self.state == CircuitState.HALF_OPEN:
                if self._half_open_test_in_progress:
                    raise CircuitBreakerError("Circuito em teste (HALF_OPEN). Aguarde a sonda.")
                self._half_open_test_in_progress = True

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exceptions as e:
            self._on_failure(e)
            raise e
        except Exception as e:
            # Exceções não mapeadas (ex: BusinessError) não afetam o circuito
            raise e
        finally:
            # CORREÇÃO CRÍTICA: Garante que a flag de sonda seja liberada 
            # mesmo se a função lançar uma exceção inesperada.
            with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    self._half_open_test_in_progress = False

class UnstableService:
    def __init__(self):
        self.cb_instance = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        self.fail_mode = None

    def do_work(self, mode: str):
        if mode == "fail_infra":
            raise DependencyError("Falha de infraestrutura")
        if mode == "fail_business":
            raise BusinessError("Erro de negócio")
        if mode == "success":
            return "OK"
        return "Normal"

    def __call__(self, mode: str):
        return self.cb_instance.call(self.do_work, mode)

def test_mission():
    unstable_service = UnstableService()
    
    print("=== INICIANDO TESTES DE CORREÇÃO ===")

    print("\n1. Testando Diferenciação de Exceções (Cenário 2)...")
    try:
        unstable_service("fail_business")
    except BusinessError:
        print("Capturado BusinessError (Correto: não deve afetar o circuito)")
    
    assert unstable_service.cb_instance.state == CircuitState.CLOSED
    print("Status: PASSOU (Erro de negócio não abriu o circuito)")

    print("\n2. Testando Controle de Sonda no Half-Open (Cenário 3)...")
    # Abrindo o circuito
    for _ in range(3):
        try:
            unstable_service("fail_infra")
        except DependencyError:
            pass
    
    assert unstable_service.cb_instance.state == CircuitState.OPEN
    print("Circuito está OPEN. Aguardando timeout...")
    time.sleep(1.1) # Espera o recovery_timeout

    results = []
    def worker():
        try:
            res = unstable_service("success")
            results.append(f"Sucesso: {res}")
        except Exception as e:
            results.append(f"Erro: {type(e).__name__}")

    threads = []
    for _ in range(5):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"Resultados das threads no Half-Open: {results}")
    
    successes = [r for r in results if "Sucesso" in r]
    blockages = [r for r in results if "CircuitBreakerError" in r]
    
    # Validação: Apenas 1 thread deve ter conseguido a vaga de teste
    assert len(successes) == 1
    assert len(blockages) == 4
    print("Status: PASSOU (Apenas uma sonda permitida no Half-Open)")

    print("\n3. Testando Recuperação Final...")
    assert unstable_service.cb_instance.state == CircuitState.CLOSED
    print("Status: PASSOU (Circuito voltou para CLOSED)")
    print("\n=== TODOS OS TESTES DE CORREÇÃO PASSARAM ===")

if __name__ == "__main__":
    test_mission()