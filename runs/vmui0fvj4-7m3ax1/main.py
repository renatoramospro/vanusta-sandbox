import time
import threading
from concurrent.futures import ThreadPoolExecutor

class TokenBucketRateLimiter:
    """
    Limitador de taxa baseado no algoritmo Token Bucket, thread-safe,
    utilizando reabastecimento preguiçoso (lazy refill) com time.monotonic().
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
        """
        Tenta adquirir tokens. Retorna 200 se bem-sucedido ou 429 se exceder o limite.
        """
        with self.lock:
            now = time.monotonic()
            self._refill(now)
            
            if self.tokens >= tokens_requested:
                self.tokens -= tokens_requested
                return 200  # HTTP 200 OK
            else:
                return 429  # HTTP 429 Too Many Requests

    def update_limits(self, new_capacity: float, new_refill_rate: float):
        """
        Permite ajustes dinâmicos de capacidade e taxa de reabastecimento em tempo de execução.
        """
        with self.lock:
            now = time.monotonic()
            self._refill(now)
            self.capacity = float(new_capacity)
            self.refill_rate = float(new_refill_rate)
            # Garante que os tokens atuais não excedam a nova capacidade
            self.tokens = min(self.tokens, self.capacity)


class UnsafeTokenBucket:
    """
    Versão intencionalmente sem thread-safety para demonstrar race conditions.
    """
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

        # Race condition crítica entre a leitura e a escrita
        if self.tokens >= 1:
            # Pequeno atraso artificial para forçar a intercalação de threads
            time.sleep(0.0001)
            self.tokens -= 1
            return 200
        return 429


def test_concurrent_load_and_rate_limiting():
    print("=== Iniciando Teste Concorrente com 1000 Requisições ===")
    # Capacidade 50, taxa 10 tokens/s. Rajada inicial de 50.
    limiter = TokenBucketRateLimiter(capacity=50, refill_rate=10.0)
    
    total_requests = 1000
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(lambda _: limiter.acquire(), range(total_requests)))
    
    successes = results.count(200)
    rate_limited = results.count(429)
    
    print(f"Total de requisições: {total_requests}")
    print(f"Sucessos (HTTP 200): {successes}")
    print(f"Rejeitadas (HTTP 429): {rate_limited}")
    
    # Validação rigorosa: as primeiras 50 requisições esgotam a rajada inicial exata.
    # Como o teste executa extremamente rápido (< 1 segundo), o refill é desprezível.
    assert successes == 50, f"Esperado exatamente 50 sucessos na rajada, obtido {successes}"
    assert rate_limited == 950, f"Esperado 950 rejeições, obtido {rate_limited}"
    print(">>> Sucesso: O limitador thread-safe cumpriu estritamente os limites de rajada.")


def test_race_condition_demonstration():
    print("\n=== Demonstrando o Impacto de Race Conditions (Sem Lock) ===")
    unsafe_limiter = UnsafeTokenBucket(capacity=10, refill_rate=0.0)
    
    # 50 threads concorrentes disputando 10 tokens iniciais
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(lambda _: unsafe_limiter.acquire(), range(50)))
    
    successes = results.count(200)
    print(f"Requisições bem-sucedidas sem lock: {successes} (Capacidade máxima era 10)")
    
    # Em um ambiente sem lock com alta concorrência, ocorre sobreconsumo devido à condição de corrida.
    # Garantimos que a falha lógica seja observada (sucessos > capacidade).
    assert successes > 10, f"Deveria ter ocorrido race condition permitindo mais de 10 sucessos, mas obteve {successes}"
    print(">>> Contraexemplo validado: A ausência de sincronização permitiu vazamento de tokens (sobreconsumo).")


def test_dynamic_adjustment():
    print("\n=== Testando Ajustes Dinâmicos de Parâmetros ===")
    limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1.0)
    assert limiter.capacity == 10.0
    
    # Altera capacidade e taxa dinamicamente
    limiter.update_limits(new_capacity=100.0, new_refill_rate=50.0)
    assert limiter.capacity == 100.0
    assert limiter.refill_rate == 50.0
    print(">>> Ajustes dinâmicos aplicados e verificados com sucesso.")


if __name__ == "__main__":
    test_concurrent_load_and_rate_limiting()
    test_race_condition_demonstration()
    test_dynamic_adjustment()
    print("\n>>> TODOS OS TESTES EXECUTADOS E APROVADOS COM SUCESSO.")