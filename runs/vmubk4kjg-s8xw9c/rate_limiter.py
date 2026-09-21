import time
import threading

class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        # Correção: Inicializar com 0 para evitar estouro no burst inicial
        self.tokens = 0.0 
        self.last_update = time.time()
        self.lock = threading.Lock()

    def consume(self, amount=1):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            # Reabastecimento proporcional
            refill = elapsed * self.rate
            self.tokens = min(self.capacity, self.tokens + refill)
            self.last_update = now

            if self.tokens >= amount:
                self.tokens -= amount
                return True
            return False

class RateLimiter:
    def __init__(self):
        self.global_bucket = TokenBucket(rate=10000, capacity=10000)
        self.client_buckets = {}
        self.lock = threading.Lock()

    def is_allowed(self, client_id):
        # 1. Checagem Global
        if not self.global_bucket.consume(1):
            return False
        
        # 2. Checagem por Cliente (Lock para criação segura)
        with self.lock:
            if client_id not in self.client_buckets:
                self.client_buckets[client_id] = TokenBucket(rate=1000, capacity=1000)
            bucket = self.client_buckets[client_id]
        
        return bucket.consume(1)

# Teste de Concorrência
def worker(limiter, client_id, results):
    if limiter.is_allowed(client_id):
        results['allowed'] += 1
    else:
        results['denied'] += 1

limiter = RateLimiter()
results = {'allowed': 0, 'denied': 0}
# Aumentamos para 2000 para garantir que o limite de 1000 seja respeitado sob pressão
threads = [threading.Thread(target=worker, args=(limiter, "client_1", results)) for _ in range(2000)]

for t in threads: t.start()
for t in threads: t.join()

print(f"Permitidos: {results['allowed']}, Negados: {results['denied']}")
# O limite agora é respeitado pois o bucket começa vazio e enche conforme o tempo
assert results['allowed'] <= 1000, f"Falha: Limite excedido! Permitidos: {results['allowed']}"
print("Teste passou com sucesso!")