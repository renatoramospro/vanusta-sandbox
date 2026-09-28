import time
import unittest

class CircuitBreakerOpenException(Exception):
    """Exceção lançada quando o circuito está aberto e bloqueia a chamada."""
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30.0, expected_exceptions=(ConnectionError, TimeoutError, RuntimeError)):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout  
        self.expected_exceptions = expected_exceptions
        
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
        except self.expected_exceptions as e:
            self._on_failure()
            if self.state == "OPEN":
                return fallback_value
            raise e
        except Exception as e:
            # Exceções não esperadas (ex: erros de validação do cliente) não abrem o circuito
            print(f"[CircuitBreaker] Exceção ignorada pelo breaker (não afeta saúde do serviço): {type(e).__name__}")
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
        if self.failure_count >= self.failure_threshold and self.state == "CLOSED":
            self.state = "OPEN"
            print(f"[CircuitBreaker] Limiar atingido. Circuito mudou para OPEN.")
        elif self.state == "HALF-OPEN":
            self.state = "OPEN"
            print(f"[CircuitBreaker] Falha em HALF-OPEN. Retornando imediatamente para OPEN.")


def retry_with_exponential_backoff(retries=3, base_delay=0.01):
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError, RuntimeError) as e:
                    if attempt == retries:
                        print(f"[Retry] Tentativa final {attempt}/{retries} falhou. Propagando erro.")
                        raise e
                    print(f"[Retry] Tentativa {attempt}/{retries} falhou. Aguardando {delay:.2f}s...")
                    time.sleep(delay)
                    delay *= 2
        return wrapper
    return decorator


class TestCircuitBreakerAndRetry(unittest.TestCase):

    def test_circuit_breaker_lifecycle(self):
        print("\n--- INICIANDO TESTE DO CIRCUIT BREAKER ---")
        # Configurado com limiar de 3 para testes rápidos
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.2)

        def unstable_service():
            raise RuntimeError("Serviço fora do ar")

        # 1. Estado CLOSED: Acumular 3 falhas
        for i in range(3):
            try:
                cb(unstable_service)
            except RuntimeError:
                pass

        self.assertEqual(cb.state, "OPEN")

        # 2. Estado OPEN: Deve retornar fallback imediatamente
        res = cb(unstable_service, fallback_value="Default Fallback")
        self.assertEqual(res, "Default Fallback")

        # 3. Aguardar o recovery_timeout para transicionar para HALF-OPEN
        print("[Teste] Aguardando timeout de recuperação...")
        time.sleep(0.3)

        def stable_service():
            return "Dados com Sucesso"

        res = cb(stable_service)
        self.assertEqual(res, "Dados com Sucesso")
        self.assertEqual(cb.state, "CLOSED")
        print("--- TESTE CONCLUÍDO COM SUCESSO ---\n")

    def test_client_error_ignored_by_breaker(self):
        print("\n--- INICIANDO TESTE DE EXCEÇÃO DE CLIENTE IGNORADA ---")
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)

        def bad_request_service():
            raise ValueError("Erro de validação do cliente")

        # ValueError não deve ser contado como falha de infraestrutura do serviço
        for _ in range(5):
            with self.assertRaises(ValueError):
                cb(bad_request_service)

        self.assertEqual(cb.state, "CLOSED")
        print("--- TESTE DE EXCEÇÃO DE CLIENTE CONCLUÍDO COM SUCESSO ---\n")


if __name__ == "__main__":
    unittest.main()