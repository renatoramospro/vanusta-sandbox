import time
import threading

class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate  # tokens por segundo
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()

    def consume(self, amount=1):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            # Reabastecimento baseado no tempo decorrido
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
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
        
        # 2. Checagem por Cliente
        with self.lock:
            if client_id not in self.client_buckets:
                self.client_buckets[client_id] = TokenBucket(rate=1000, capacity=1000)
        
        return self.client_buckets[client_id].consume(1)

# Teste de Concorrência
def worker(limiter, client_id, results):
    if limiter.is_allowed(client_id):
        results['allowed'] += 1
    else:
        results['denied'] += 1

limiter = RateLimiter()
results = {'allowed': 0, 'denied': 0}
threads = [threading.Thread(target=worker, args=(limiter, "client_1", results)) for _ in range(1500)]

for t in threads: t.start()
for t in threads: t.join()

print(f"Permitidos: {results['allowed']}, Negados: {results['denied']}")
assert results['allowed'] <= 1000, "Falha: Limite de cliente excedido!"