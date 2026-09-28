import time
import unittest

class CircuitBreakerOpenException(Exception):
    """Exceção lançada quando o circuito está aberto e bloqueia a chamada."""
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=2.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout  # Reduzido para fins de teste rápido
        
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count_half_open = 0

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
        elif self.state == "CLOSED":
            # Reseta contador de falhas em caso de sucesso contínuo
            self.failure_count = 0

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        print(f"[CircuitBreaker] Falha detectada. Contador consecutivo: {self.failure_count}")

        if self.state == "HALF-OPEN":
            print(f"[CircuitBreaker] Falha em HALF-OPEN. Retornando para OPEN.")
            self.state = "OPEN"
        elif self.state == "CLOSED" and self.failure_count >= self.failure_threshold:
            print(f"[CircuitBreaker] Limite de falhas atingido ({self.failure_threshold}). Abrindo circuito (OPEN).")
            self.state = "OPEN"


def retry_with_backoff(retries=3, backoff_in_seconds=0.1):
    """Decorator para implementar Retry com Backoff Exponencial antes de registrar falha."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            x = 0
            while x < retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    x += 1
                    if x == retries:
                        raise e
                    sleep_time = backoff_in_seconds * (2 ** (x - 1))
                    print(f"[Retry] Tentativa {x} falhou. Tentando novamente em {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
        return wrapper
    return decorator


# --- TESTES AUTOMATIZADOS ---
class TestCircuitBreakerAndRetry(unittest.TestCase):
    
    def test_circuit_breaker_lifecycle(self):
        print("\n--- INICIANDO TESTE DO CIRCUIT BREAKER ---")
        
        # Serviço instável que sempre falha
        def unstable_service():
            raise RuntimeError("Serviço fora do ar")

        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.5)

        # 1. Estado CLOSED: As primeiras falhas incrementam o contador mas executam a função
        for i in range(3):
            res = cb(unstable_service, fallback_value="Default Fallback")
            self.assertEqual(res, "Default Fallback")

        # Após 3 falhas consecutivas, o circuito deve estar OPEN
        self.assertEqual(cb.state, "OPEN")

        # 2. Estado OPEN: Deve retornar fallback imediatamente sem chamar o serviço
        res = cb(unstable_service, fallback_value="Default Fallback")
        self.assertEqual(res, "Default Fallback")

        # 3. Aguardar o recovery_timeout para transicionar para HALF-OPEN
        print("[Teste] Aguardando timeout de recuperação...")
        time.sleep(0.6)

        # Serviço agora se recupera
        def stable_service():
            return "Dados com Sucesso"

        # Chamada em HALF-OPEN com sucesso deve fechar o circuito
        res = cb(stable_service)
        self.assertEqual(res, "Dados com Sucesso")
        self.assertEqual(cb.state, "CLOSED")
        print("--- TESTE CONCLUÍDO COM SUCESSO ---\n")


if __name__ == "__main__":
    unittest.main()