import time
import threading
from concurrent.futures import ThreadPoolExecutor

class TokenBucketRateLimiter:
    """
    Limitador de taxa baseado no algoritmo Token Bucket, thread-safe,
    utilizando reabastecimento preguiçoso (lazy refill) com time.monotonic()
    e suporte a ajustes dinâmicos seguros de capacidade e taxa.
    """
    def __init__(self, capacity: float, refill_rate: float):
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
        with self.lock:
            now = time.monotonic()
            self._refill(now)
            
            if self.tokens >= tokens_requested:
                self.tokens -= tokens_requested
                return 200  # OK
            else:
                return 429  # Too Many Requests

    def update_limits(self, new_capacity: float, new_refill_rate: float):
        """
        Ajusta dinamicamente a capacidade e a taxa, garantindo que o reabastecimento
        seja aplicado e que os tokens atuais nunca excedam a nova capacidade (invariante).
        """
        with self.lock:
            now = time.monotonic()
            self._refill(now)
            self.capacity = float(new_capacity)
            self.refill_rate = float(new_refill_rate)
            # Correção essencial: restringe os tokens correntes ao novo teto máximo
            self.tokens = min(self.tokens, self.capacity)


class UnsafeTokenBucket:
    """Versão sem lock para fins de demonstração de race condition."""
    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()

    def acquire(self) -> int:
        now = time.monotonic()
        elapsed = now - self.last_refill
        if elapsed > 0:
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now

        if self.tokens >= 1:
            # Simula atraso não atômico para forçar condição de corrida
            time.sleep(0.0001)
            self.tokens -= 1
            return 200
        return 429


def test_concurrent_load_and_rate_limiting():
    print("=== Iniciando Teste Concorrente com 1000 Requisições ===")
    # Capacidade 50, refill 0 para testar apenas rajada esgotada
    limiter = TokenBucketRateLimiter(capacity=50, refill_rate=0.0)
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(lambda _: limiter.acquire(), range(1000)))
    
    successes = results.count(200)
    rejected = results.count(429)
    
    print(f"Total de requisições: {len(results)}")
    print(f"Sucessos (HTTP 200): {successes}")
    print(f"Rejeitadas (HTTP 429): {rejected}")
    
    assert successes == 50, f"Esperado exatamente 50 sucessos, obteve {successes}"
    assert rejected == 950, f"Esperado exatamente 950 rejeições, obteve {rejected}"
    print(">>> Sucesso: O limitador thread-safe cumpriu estritamente os limites de rajada.")


def test_adversarial_dynamic_reduction():
    print("\n=== Testando Cenário Adversarial de Redução Dinâmica de Capacidade ===")
    limiter = TokenBucketRateLimiter(capacity=100.0, refill_rate=10.0)
    
    # Consome alguns tokens para deixar o balde em um estado intermediário (ex: 90 tokens)
    limiter.tokens = 90.0
    assert limiter.tokens == 90.0
    
    # Reduz drasticamente a capacidade máxima para 20.0
    limiter.update_limits(new_capacity=20.0, new_refill_rate=5.0)
    
    print(f"Capacidade nova: {limiter.capacity}")
    print(f"Tokens atuais após redução: {limiter.tokens}")
    
    # Invariante crucial: os tokens não podem exceder a nova capacidade
    assert limiter.tokens <= limiter.capacity, f"Violação de invariante: tokens ({limiter.tokens}) > capacidade ({limiter.capacity})"
    assert limiter.tokens == 20.0, f"Esperado que os tokens fossem limitados a 20.0, mas obteve {limiter.tokens}"
    print(">>> Sucesso adversarial: A redução dinâmica limitou corretamente o volume de tokens ao novo teto.")


def test_race_condition_demonstration():
    print("\n=== Demonstrando o Impacto de Race Conditions (Sem Lock) ===")
    unsafe_limiter = UnsafeTokenBucket(capacity=10, refill_rate=0.0)
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(lambda _: unsafe_limiter.acquire(), range(50)))
    
    successes = results.count(200)
    print(f"Requisições bem-sucedidas sem lock: {successes} (Capacidade máxima era 10)")
    assert successes > 10, f"Deveria ter ocorrido race condition permitindo mais de 10 sucessos, mas obteve {successes}"
    print(">>> Contraexemplo validado: A ausência de sincronização permitiu vazamento de tokens (sobreconsumo).")


if __name__ == "__main__":
    test_concurrent_load_and_rate_limiting()
    test_adversarial_dynamic_reduction()
    test_race_condition_demonstration()
    print("\n>>> TODOS OS TESTES EXECUTADOS E APROVADOS COM SUCESSO.")