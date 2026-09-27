import time
import math

class SimulatedTokenBucketRedis:
    """Simula o comportamento atômico do script Lua do Redis para fins de validação."""
    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_update = time.time()

    def allow_request(self, tokens_requested: float = 1.0) -> bool:
        now = time.time()
        delta = max(0.0, now - self.last_update)
        
        # Reabastece tokens
        self.tokens = min(self.capacity, self.tokens + (delta * self.refill_rate))
        self.last_update = now

        if self.tokens >= tokens_requested:
            self.tokens -= tokens_requested
            return True
        return False

def run_simulation():
    print("Iniciando simulação de teste de carga para Token Bucket...")
    # Configuração: Burst de 10 tokens, reabastece 5 tokens por segundo
    bucket = SimulatedTokenBucketRedis(capacity=10.0, refill_rate=5.0)
    
    allowed_count = 0
    rejected_count = 0
    
    # Simula rajada inicial instantânea (15 requisições de uma vez)
    print("\n--- Cenário 1: Rajada inicial de 15 requisições (Burst=10) ---")
    for i in range(15):
        if bucket.allow_request():
            allowed_count += 1
        else:
            rejected_count += 1
            
    print(f"Resultado Rajada -> Permitidas: {allowed_count} (Esperado: 10), Rejeitadas: {rejected_count} (Esperado: 5)")
    assert allowed_count == 10, f"Esperado 10 permitidas, obtido {allowed_count}"
    assert rejected_count == 5, f"Esperado 5 rejeitadas, obtido {rejected_count}"

    # Aguarda 2 segundos (deve recuperar 2 segundos * 5 tokens/s = 10 tokens, limitado à capacidade de 10)
    print("\n--- Cenário 2: Aguardando 2 segundos para reabastecimento ---")
    time.sleep(2.0)
    
    allowed_count_2 = 0
    for i in range(5):
        if bucket.allow_request():
            allowed_count_2 += 1
            
    print(f"Requisições permitidas após reabastecimento: {allowed_count_2} (Esperado: 5)")
    assert allowed_count_2 == 5, f"Esperado 5 permitidas, obtido {allowed_count_2}"
    
    print("\nSimulação concluída com sucesso e dentro do modelo teórico previsto!")

if __name__ == "__main__":
    run_simulation()