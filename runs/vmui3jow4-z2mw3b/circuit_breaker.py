import time

class CircuitBreakerOpenException(Exception):
    """Exceção lançada quando o circuito está aberto e rejeita requisições."""
    pass

class CircuitBreaker:
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, failure_threshold=3, success_threshold=5, recovery_timeout=1.0):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.recovery_timeout = recovery_timeout
        
        self.state = self.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def _to_open(self):
        self.state = self.OPEN
        self.last_failure_time = time.time()
        self.success_count = 0

    def _to_closed(self):
        self.state = self.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def _to_half_open(self):
        self.state = self.HALF_OPEN
        self.success_count = 0

    def call(self, func, *args, **kwargs):
        now = time.time()

        # Verifica se deve transicionar de OPEN para HALF_OPEN com base no tempo de recuperação
        if self.state == self.OPEN:
            if now - self.last_failure_time >= self.recovery_timeout:
                self._to_half_open()
            else:
                raise CircuitBreakerOpenException("Circuit Breaker está ABERTO. Chamada rejeitada.")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            if not isinstance(e, CircuitBreakerOpenException):
                self._on_failure()
            raise e

    def _on_success(self):
        if self.state == self.HALF_OPEN:
            self.success_count += 1
            print(f"[CB] Sucesso no estado HALF-OPEN ({self.success_count}/{self.success_threshold})")
            if self.success_count >= self.success_threshold:
                print("[CB] Limite de sucessos atingido. Transicionando para CLOSED.")
                self._to_closed()
        elif self.state == self.CLOSED:
            # Reseta contadores de falhas em caso de sucesso no estado fechado
            self.failure_count = 0

    def _on_failure(self):
        self.failure_count += 1
        print(f"[CB] Falha detectada. Contador de falhas: {self.failure_count}/{self.failure_threshold}")
        if self.state == self.CLOSED:
            if self.failure_count >= self.failure_threshold:
                print("[CB] Limite de falhas atingido. Transicionando para OPEN.")
                self._to_open()
        elif self.state == self.HALF_OPEN:
            print("[CB] Falha no estado HALF-OPEN. Retornando imediatamente para OPEN.")
            self._to_open()


# --- Testes Automatizados ---
def test_circuit_breaker_lifecycle():
    print("Iniciando testes do Circuit Breaker...")

    # Função simulada de serviço instável
    def unstable_service(should_fail):
        if should_fail:
            raise RuntimeError("Erro no serviço externo")
        return "OK"

    cb = CircuitBreaker(failure_threshold=3, success_threshold=5, recovery_timeout=0.2)

    # 1. Estado Inicial deve ser CLOSED
    assert cb.state == CircuitBreaker.CLOSED
    print("✓ Estado inicial verificado: CLOSED")

    # 2. Execuções com sucesso mantêm CLOSED
    assert cb.call(unstable_service, False) == "OK"
    assert cb.state == CircuitBreaker.CLOSED

    # 3. Induzir falhas consecutivas até abrir o circuito (limite = 3)
    for i in range(3):
        try:
            cb.call(unstable_service, True)
        except RuntimeError:
            pass

    # O circuito deve ter aberto após a 3ª falha
    assert cb.state == CircuitBreaker.OPEN
    print("✓ Circuito transicionou para OPEN após 3 falhas consecutivas.")

    # 4. Verificar falha rápida (fast-fail) quando OPEN
    try:
        cb.call(unstable_service, False)
        assert False, "Deveria ter lançado CircuitBreakerOpenException"
    except CircuitBreakerOpenException:
        print("✓ Requisições rejeitadas imediatamente enquanto OPEN.")

    # 5. Aguardar o recovery_timeout para transicionar para HALF_OPEN
    print("Aguardando tempo de recuperação (recovery_timeout)...")
    time.sleep(0.3)

    # A primeira chamada deve permitir o teste (HALF-OPEN) e se for bem-sucedida, contar para o limiar de sucesso
    # Vamos executar 5 sucessos consecutivos no estado HALF-OPEN
    for i in range(5):
        # Garante que o estado seja verificado ou mantenha-se em HALF_OPEN/CLOSED
        res = cb.call(unstable_service, False)
        assert res == "OK"

    # 6. O circuito deve ter retornado para CLOSED após 5 sucessos
    assert cb.state == CircuitBreaker.CLOSED
    print("✓ Circuito retornou com sucesso para o estado CLOSED após 5 requisições bem-sucedidas em HALF-OPEN.")

    print("Todos os testes do Circuit Breaker passaram com sucesso!")

if __name__ == "__main__":
    test_circuit_breaker_lifecycle()