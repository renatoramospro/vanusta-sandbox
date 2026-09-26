import time

class CircuitBreakerOpenException(Exception):
    """Exceção lançada quando o circuito está aberto e rejeita requisições (fail-fast)."""
    pass

class CircuitBreaker:
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, failure_threshold=3, success_threshold=5, recovery_timeout=0.2):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.recovery_timeout = recovery_timeout
        
        self.state = self.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change_time = time.time()

    def _to_state(self, new_state):
        if self.state != new_state:
            print(f"[CB] Transicionando de {self.state} para {new_state}.")
            self.state = new_state
            self.last_state_change_time = time.time()
            if new_state == self.OPEN:
                self.success_count = 0
            elif new_state == self.CLOSED:
                self.failure_count = 0
                self.success_count = 0
            elif new_state == self.HALF_OPEN:
                self.success_count = 0

    def call(self, func, *args, **kwargs):
        now = time.time()

        # Verifica se o estado OPEN deve expirar para HALF_OPEN
        if self.state == self.OPEN:
            if now - self.last_state_change_time > self.recovery_timeout:
                self._to_state(self.HALF_OPEN)
            else:
                raise CircuitBreakerOpenException("Circuito ABERTO: chamada rejeitada por fail-fast.")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            # Se for nossa própria exceção de circuito aberto, repassa sem alterar contadores
            if isinstance(e, CircuitBreakerOpenException):
                raise
            self._on_failure()
            raise

    def _on_success(self):
        if self.state == self.HALF_OPEN:
            self.success_count += 1
            print(f"[CB] Sucesso no estado HALF-OPEN ({self.success_count}/{self.success_threshold})")
            if self.success_count >= self.success_threshold:
                self._to_state(self.CLOSED)
        elif self.state == self.CLOSED:
            # Reseta falhas em caso de sucesso no estado fechado
            self.failure_count = 0

    def _on_failure(self):
        if self.state == self.HALF_OPEN:
            print("[CB] Falha detectada no estado HALF-OPEN. Retornando imediatamente para OPEN.")
            self._to_state(self.OPEN)
        elif self.state == self.CLOSED:
            self.failure_count += 1
            print(f"[CB] Falha detectada no CLOSED. Contador: {self.failure_count}/{self.failure_threshold}")
            if self.failure_count >= self.failure_threshold:
                self._to_state(self.OPEN)


def unstable_service(should_fail):
    if should_fail:
        raise RuntimeError("Serviço externo falhou!")
    return "OK"

def test_circuit_breaker_lifecycle():
    print("Iniciando testes rigorosos do Circuit Breaker...")
    cb = CircuitBreaker(failure_threshold=3, success_threshold=3, recovery_timeout=0.1)

    # 1. Estado inicial
    assert cb.state == CircuitBreaker.CLOSED
    print("✓ Estado inicial verificado: CLOSED")

    # 2. Induzir falhas até abrir
    for _ in range(3):
        try:
            cb.call(unstable_service, True)
        except RuntimeError:
            pass
    assert cb.state == CircuitBreaker.OPEN
    print("✓ Circuito aberto após 3 falhas consecutivas.")

    # 3. Testar transição HALF_OPEN -> OPEN (Falha na sondagem)
    print("Aguardando recovery_timeout para teste de falha em HALF_OPEN...")
    time.sleep(0.12)
    
    # A próxima chamada deve entrar em HALF_OPEN mas falhar, reabrindo o circuito imediatamente
    try:
        cb.call(unstable_service, True)
    except RuntimeError:
        pass
    
    assert cb.state == CircuitBreaker.OPEN
    print("✓ Circuito retornou para OPEN após falha no estado HALF-OPEN.")

    # 4. Aguardar novamente e validar recuperação completa (HALF_OPEN -> CLOSED)
    print("Aguardando recovery_timeout para recuperação completa...")
    time.sleep(0.12)

    for _ in range(3):
        res = cb.call(unstable_service, False)
        assert res == "OK"

    assert cb.state == CircuitBreaker.CLOSED
    print("✓ Circuito retornou para CLOSED após sucessos em HALF-OPEN.")
    print("Todos os testes executados e validados com sucesso!")

if __name__ == "__main__":
    test_circuit_breaker_lifecycle()