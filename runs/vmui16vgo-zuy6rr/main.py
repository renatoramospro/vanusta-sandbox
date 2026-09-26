import time
import threading
import math
from concurrent.futures import ThreadPoolExecutor

class TokenBucketRateLimiter:
    """
    Limitador de taxa baseado no algoritmo Token Bucket, thread-safe,
    utilizando reabastecimento preguiçoso (lazy refill) com time.monotonic(),
    validação rigorosa de parâmetros de entrada e suporte a ajustes dinâmicos seguros.
    
    NOTA DE ARQUITETURA (Segurança e Distribuição):
    Esta implementação é LOCAL AO PROCESSO. Em ambientes com múltiplos workers,
    réplicas ou containers (ex: Gunicorn, Kubernetes), o estado em memória não é
    compartilhado entre instâncias. Para proteção global em arquiteturas distribuídas,
    utilize um armazenamento centralizado como Redis (com contadores atômicos ou scripts Lua).
    """
    def __init__(self, capacity: float, refill_rate: float):
        # Validação defensiva de parâmetros iniciais
        if not math.isfinite(capacity) or capacity <= 0:
            raise ValueError(f"Capacidade inválida: {capacity}. Deve ser um número finito > 0.")
        if not math.isfinite(refill_rate) or refill_rate < 0:
            raise ValueError(f"Taxa de reabastecimento inválida: {refill_rate}. Deve ser um número finito >= 0.")
            
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

    def _refill(self, now: float):
        elapsed = now - self.last_refill
        if elapsed > 0:
            new_tokens = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now

    def acquire(self, tokens_requested: int = 1) -> int:
        # Validação defensiva do argumento de consumo
        if not isinstance(tokens_requested, int) or tokens_requested <= 0:
            raise ValueError(f"Tokens solicitados devem ser um inteiro positivo, recebido: {tokens_requested}")
        
        if tokens_requested > self.capacity:
            # Requisição impossível de ser atendida pois excede o teto total do balde
            return 429

        with self.lock:
            now = time.monotonic()
            self._refill(now)
            
            if self.tokens >= tokens_requested:
                self.tokens -= tokens_requested
                return 200
            else:
                return 429

    def update_limits(self, new_capacity: float, new_refill_rate: float):
        # Validação defensiva para ajustes dinâmicos
        if not math.isfinite(new_capacity) or new_capacity <= 0:
            raise ValueError(f"Nova capacidade inválida: {new_capacity}. Deve ser > 0.")
        if not math.isfinite(new_refill_rate) or new_refill_rate < 0:
            raise ValueError(f"Nova taxa de reabastecimento inválida: {new_refill_rate}. Deve ser >= 0.")

        with self.lock:
            now = time.monotonic()
            self._refill(now)
            self.capacity = float(new_capacity)
            self.refill_rate = float(new_refill_rate)
            # Invariante mantida: tokens atuais nunca ultrapassam a nova capacidade reduzida
            self.tokens = min(self.tokens, self.capacity)


class UnsafeTokenBucket:
    """Implementação intencionalmente sem lock para demonstração de race condition."""
    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate

    def acquire(self) -> int:
        if self.tokens >= 1:
            time.sleep(0.0001)  # Simula atraso para induzir race condition
            self.tokens -= 1
            return 200
        return 429


def test_input_validation_security():
    print("\n=== Testando Validação Defensiva de Parâmetros ===")
    
    # Validação de capacidade inválida
    try:
        TokenBucketRateLimiter(capacity=-10, refill_rate=5)
        raise AssertionError("Deveria ter rejeitado capacidade negativa.")
    except ValueError as e:
        print(f"Capturado com sucesso (capacidade negativa): {e}")

    # Validação de taxa inválida (NaN / Infinito)
    try:
        TokenBucketRateLimiter(capacity=100, refill_rate=float('inf'))
        raise AssertionError("Deveria ter rejeitado taxa infinita.")
    except ValueError as e:
        print(f"Capturado com sucesso (taxa infinita): {e}")

    # Validação de tokens solicitados inválidos
    limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1)
    try:
        limiter.acquire(tokens_requested=0)
        raise AssertionError("Deveria ter rejeitado 0 tokens solicitados.")
    except ValueError as e:
        print(f"Capturado com sucesso (tokens solicitados zero): {e}")

    # Validação de tokens solicitados superiores à capacidade máxima
    status = limiter.acquire(tokens_requested=15)
    assert status == 429, f"Esperado 429 para requisição acima da capacidade, obteve {status}"
    print(">>> Sucesso na segurança: Parâmetros inválidos e excessivos bloqueados adequadamente.")


def test_concurrent_load_and_rate_limiting():
    print("\n=== Iniciando Teste Concorrente com 1000 Requisições ===")
    limiter = TokenBucketRateLimiter(capacity=50, refill_rate=0.0)
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(lambda _: limiter.acquire(1), range(1000)))
    
    successes = results.count(200)
    rejections = results.count(429)
    
    print(f"Total de requisições: 1000")
    print(f"Sucessos (HTTP 200): {successes}")
    print(f"Rejeitadas (HTTP 429): {rejections}")
    
    assert successes == 50, f"Esperado exatamente 50 sucessos, obteve {successes}"
    assert rejections == 950, f"Esperado exatamente 950 rejeições, obteve {rejections}"
    print(">>> Sucesso: O limitador thread-safe cumpriu estritamente os limites de rajada.")


def test_adversarial_dynamic_reduction():
    print("\n=== Testando Cenário Adversarial de Redução Dinâmica de Capacidade ===")
    limiter = TokenBucketRateLimiter(capacity=100.0, refill_rate=10.0)
    time.sleep(0.1)
    
    # Reduz dinamicamente a capacidade para 20.0
    limiter.update_limits(new_capacity=20.0, new_refill_rate=5.0)
    
    print(f"Capacidade nova: {limiter.capacity}")
    print(f"Tokens atuais após redução: {limiter.tokens}")
    
    assert limiter.tokens <= limiter.capacity, f"Violação: tokens ({limiter.tokens}) > capacidade ({limiter.capacity})"
    assert limiter.tokens == 20.0, f"Esperado 20.0, obteve {limiter.tokens}"
    print(">>> Sucesso adversarial: A redução dinâmica limitou corretamente o volume de tokens ao novo teto.")


def test_race_condition_demonstration():
    print("\n=== Demonstrando o Impacto de Race Conditions (Sem Lock) ===")
    unsafe_limiter = UnsafeTokenBucket(capacity=10, refill_rate=0.0)
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(lambda _: unsafe_limiter.acquire(), range(50)))
    
    successes = results.count(200)
    print(f"Requisições bem-sucedidas sem lock: {successes} (Capacidade máxima era 10)")
    assert successes > 10, f"Deveria ter ocorrido race condition, obteve {successes}"
    print(">>> Contraexemplo validado: A ausência de sincronização permitiu vazamento de tokens (sobreconsumo).")


if __name__ == "__main__":
    test_input_validation_security()
    test_concurrent_load_and_rate_limiting()
    test_adversarial_dynamic_reduction()
    test_race_condition_demonstration()
    print("\n>>> TODOS OS TESTES EXECUTADOS E APROVADOS COM SUCESSO.")