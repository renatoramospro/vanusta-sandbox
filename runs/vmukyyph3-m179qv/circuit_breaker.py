import time
import unittest

class CircuitBreakerOpenException(Exception):
    """Exceção lançada quando o circuito está aberto e bloqueia a chamada."""
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=0.5):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout  
        
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None

    def __call__(self, func, *args, fallback_value="Fallback Response", **kwargs):
        now = time.time()

        # 1. Verificar transição de OPEN para HALF-OPEN
        if self.state == "OPEN":
            if now - self.last_failure_time >= self.recovery_timeout:
                print(f"[CircuitBreaker] Timeout expirado. Mudando de OPEN para HALF-OPEN.")
                self.state = "HALF-OPEN"
            else:
                print(f"[CircuitBreaker] Estado: OPEN. Acionando fallback imediato.")
                return fallback_value

        # 2. Execução da chamada protegida
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            if self.state == "OPEN":
                return fallback_value
            raise e

    def _on_success(self):
        if self.state == "HALF-OPEN":
            print(f"[CircuitBreaker] Sucesso em HALF-OPEN. Fechando o circuito (CLOSED).")
            self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        print(f"[CircuitBreaker] Falha detectada. Contador consecutivo: {self.failure_count}")
        
        if self.state == "HALF-OPEN" or self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            print(f"[CircuitBreaker] Limiar atingido. Circuito mudou para OPEN.")


def retry_with_exponential_backoff(retries=3, base_delay=0.1):
    """Decorator para implementar Retry com backoff exponencial."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries:
                        print(f"[Retry] Tentativa {attempt}/{retries} falhou definitiva.")
                        raise e
                    print(f"[Retry] Tentativa {attempt}/{retries} falhou. Aguardando {delay:.2f}s...")
                    time.sleep(delay)
                    delay *= 2
        return wrapper
    return decorator


class TestCircuitBreakerAndRetry(unittest.TestCase):

    def test_circuit_breaker_lifecycle(self):
        print("\n--- INICIANDO TESTE DO CIRCUIT BREAKER ---")
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.3)

        def unstable_service():
            raise RuntimeError("Serviço fora do ar")

        # 1. Acumular falhas até abrir o circuito (limiar = 3)
        for i in range(3):
            try:
                cb(unstable_service, fallback_value="Default Fallback")
            except RuntimeError:
                pass  # Esperado enquanto o circuito está CLOSED

        # Após 3 falhas consecutivas, o circuito deve estar OPEN
        self.assertEqual(cb.state, "OPEN")

        # 2. Estado OPEN: Deve retornar fallback imediatamente sem chamar o serviço
        res = cb(unstable_service, fallback_value="Default Fallback")
        self.assertEqual(res, "Default Fallback")

        # 3. Aguardar o recovery_timeout para transicionar para HALF-OPEN
        print("[Teste] Aguardando timeout de recuperação...")
        time.sleep(0.4)

        # Serviço agora se recupera
        def stable_service():
            return "Dados com Sucesso"

        # Chamada em HALF-OPEN com sucesso deve fechar o circuito
        res = cb(stable_service)
        self.assertEqual(res, "Dados com Sucesso")
        self.assertEqual(cb.state, "CLOSED")
        print("--- TESTE CONCLUÍDO COM SUCESSO ---\n")

    def test_retry_mechanism(self):
        print("\n--- INICIANDO TESTE DE RETRY ---")
        
        attempts = {"count": 0}

        @retry_with_exponential_backoff(retries=3, base_delay=0.01)
        def flaky_service():
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise ValueError("Erro temporário")
            return "Sucesso na tentativa"

        result = flaky_service()
        self.assertEqual(result, "Sucesso na tentativa")
        self.assertEqual(attempts["count"], 3)
        print("--- TESTE DE RETRY CONCLUÍDO COM SUCESSO ---\n")


if __name__ == "__main__":
    unittest.main()