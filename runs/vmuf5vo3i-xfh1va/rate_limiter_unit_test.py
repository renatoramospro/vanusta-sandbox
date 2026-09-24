import time
import threading
import unittest
import math

class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        # time.monotonic() evita problemas com retrocessos no relógio do sistema
        self.last_update = time.monotonic()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1) -> tuple[bool, int]:
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.last_update = now

            # Se porventura houver qualquer inconsistência, garantimos elapsed não negativo
            if elapsed > 0:
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0
            else:
                missing_tokens = tokens - self.tokens
                # Retry-After deve ser um inteiro positivo em segundos (arredondado para cima)
                retry_after = math.ceil(missing_tokens / self.refill_rate)
                return False, retry_after

class RateLimiterMiddleware:
    def __init__(self, capacity: float, refill_rate: float, cleanup_ttl: float = 300.0):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets = {}
        self.cleanup_ttl = cleanup_ttl
        self.lock = threading.Lock()

    def get_bucket(self, ip: str) -> TokenBucket:
        with self.lock:
            if ip not in self.buckets:
                self.buckets[ip] = TokenBucket(self.capacity, self.refill_rate)
            return self.buckets[ip]

    def allow_request(self, ip: str) -> tuple[bool, int]:
        bucket = self.get_bucket(ip)
        return bucket.consume(1)


class TestTokenBucketUnit(unittest.TestCase):
    
    def test_token_bucket_initial_capacity(self):
        """Valida se o balde inicia cheio e permite o consumo imediato."""
        bucket = TokenBucket(capacity=2.0, refill_rate=1.0)
        
        allowed, retry = bucket.consume(1)
        self.assertTrue(allowed)
        self.assertEqual(retry, 0)

        allowed, retry = bucket.consume(1)
        self.assertTrue(allowed)
        self.assertEqual(retry, 0)

    def test_token_bucket_overflow(self):
        """Valida o estouro de cota e o cálculo correto do Retry-After como inteiro."""
        bucket = TokenBucket(capacity=1.0, refill_rate=0.5) # 1 token máx, recarrega 0.5 tokens/s
        
        # Consome o único token disponível
        allowed, _ = bucket.consume(1)
        self.assertTrue(allowed)

        # Próxima requisição deve estourar
        allowed, retry_after = bucket.consume(1)
        self.assertFalse(allowed)
        self.assertIsInstance(retry_after, int, "Retry-After deve ser serializado como inteiro em segundos")
        self.assertGreaterEqual(retry_after, 1, "Retry-After deve indicar ao menos 1 segundo de espera")
        print(f"\n[OK] Estouro validado. Retry-After retornado: {retry_after} segundos (inteiro HTTP válido)")

    def test_token_refill_mechanism(self):
        """Valida a recarga gradual de tokens com o passar do tempo real (simulado ou real)."""
        bucket = TokenBucket(capacity=1.0, refill_rate=10.0) # 10 tokens por segundo
        
        # Esvazia o balde
        bucket.consume(1)
        
        # Aguarda 0.15 segundos (deve recarregar 1.5 tokens, limitados à capacidade de 1.0)
        time.sleep(0.15)

        allowed, _ = bucket.consume(1)
        self.assertTrue(allowed, "O balde deveria ter recarregado tokens suficientes após a pausa")
        print("[OK] Recarga de tokens validada com sucesso.")

    def test_rate_limiter_middleware_ip_isolation(self):
        """Valida que o middleware isola corretamente os baldes por endereço IP."""
        limiter = RateLimiterMiddleware(capacity=1.0, refill_rate=1.0)
        ip_a = "192.168.1.10"
        ip_b = "10.0.0.5"

        # Esgota o IP A
        self.assertTrue(limiter.allow_request(ip_a)[0])
        self.assertFalse(limiter.allow_request(ip_a)[0])

        # IP B deve continuar com o balde cheio independentemente do IP A
        self.assertTrue(limiter.allow_request(ip_b)[0], "IPs diferentes devem possuir baldes isolados")
        print(f"[OK] Isolamento por IP validado para {ip_a} e {ip_b}.")

if __name__ == '__main__':
    unittest.main()