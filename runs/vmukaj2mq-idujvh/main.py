import time
import math

class RedisTokenBucketSecureMock:
    """
    Simulação robusta e segura do script Lua para Token Bucket no Redis,
    incluindo validação estrita de parâmetros, tratamento de clock drift e TTL dinâmico.
    """
    def __init__(self, capacity: float, refill_rate: float):
        if capacity <= 0 or refill_rate <= 0:
            raise ValueError("Capacity e Refill Rate devem ser maiores que zero.")
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self.storage = {} # Simula o Redis: {key: {"tokens": float, "last_updated": float}}

    def execute_lua_script(self, key: str, requested: float, now: float) -> tuple:
        # Validação estrita de entradas no nível de execução
        if requested <= 0:
            raise ValueError("O custo da requisição (requested) deve ser maior que zero.")
        if not math.isfinite(now) or not math.isfinite(requested):
            raise ValueError("Parâmetros numéricos inválidos.")

        # Simulação do comportamento atômico do Redis HGET
        data = self.storage.get(key)
        tokens = self.capacity
        last_updated = now

        if data:
            tokens = float(data["tokens"])
            last_updated = float(data["last_updated"])

        # Mitigação de clock drift (proteção contra retrocesso de relógio)
        delta = now - last_updated
        if delta < 0:
            delta = 0.0

        # Reabastecimento de tokens
        tokens = min(self.capacity, tokens + delta * self.refill_rate)
        last_updated = now

        allowed = 0
        if tokens >= requested:
            tokens -= requested
            allowed = 1

        # Atualização atômica do estado no Redis (substituindo HMSET legado por HSET)
        self.storage[key] = {
            "tokens": tokens,
            "last_updated": last_updated
        }

        # Cálculo de TTL dinâmico seguro para prevenir OOM por chaves efêmeras
        time_to_fill = math.ceil((self.capacity - tokens) / self.refill_rate)
        ttl = max(60, time_to_fill + 30)

        return (allowed, tokens, ttl)

def run_secure_simulation():
    print("Iniciando simulação segura do Rate Limiting (Token Bucket)...")
    
    # Inicializa o bucket com capacidade 10 e taxa de 5 tokens/segundo
    limiter = RedisTokenBucketSecureMock(capacity=10.0, refill_rate=5.0)
    key = "rate_limit:user:secure_test"
    
    current_time = 1000.0

    # Teste 1: Requisições normais dentro do limite
    print("\n--- Teste 1: Requisições Normais ---")
    for i in range(3):
        allowed, tokens, ttl = limiter.execute_lua_script(key, requested=1.0, now=current_time)
        print(f"Req {i+1}: Permitida={allowed}, Tokens Restantes={tokens:.2f}, TTL={ttl}s")
        assert allowed == 1

    # Teste 2: Consumo de burst (esgotar os tokens restantes)
    print("\n--- Teste 2: Esgotamento por Burst ---")
    allowed, tokens, ttl = limiter.execute_lua_script(key, requested=10.0, now=current_time)
    print(f"Tentativa de Burst (10 reqs): Permitida={allowed}, Tokens={tokens:.2f}")
    assert allowed == 0 # Deve ser rejeitado por falta de tokens

    # Teste 3: Avanço de tempo (reabastecimento)
    print("\n--- Teste 3: Reabastecimento após 2 segundos ---")
    current_time += 2.0  # Passaram 2 segundos -> +10 tokens (limitado à capacidade 10)
    allowed, tokens, ttl = limiter.execute_lua_script(key, requested=2.0, now=current_time)
    print(f"Req após reabastecimento: Permitida={allowed}, Tokens={tokens:.2f}")
    assert allowed == 1

    # Teste 4: Mitigação de Clock Drift (retrocesso de relógio)
    print("\n--- Teste 4: Mitigação de Clock Drift (Relógio Retrocedeu) ---")
    current_time -= 5.0 # Relógio retrocedeu indevidamente
    allowed, tokens, ttl = limiter.execute_lua_script(key, requested=1.0, now=current_time)
    print(f"Req com relógio retrocedido: Permitida={allowed}, Tokens={tokens:.2f} (delta tratado como 0)")
    assert allowed == 1

    # Teste 5: Validação de entradas inválidas (Segurança)
    print("\n--- Teste 5: Validação de Entradas Maliciosas/Inválidas ---")
    try:
        limiter.execute_lua_script(key, requested=0, now=current_time)
    except ValueError as e:
        print(f"Capturado erro esperado para requested=0: {e}")

    print("\nTodos os testes de segurança, validação e funcionamento passaram com sucesso!")

if __name__ == "__main__":
    run_secure_simulation()