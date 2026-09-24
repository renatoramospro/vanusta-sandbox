import time
import threading
import unittest
import math

class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float):
        if capacity <= 0:
            raise ValueError("Capacity must be greater than 0")
        if refill_rate <= 0:
            raise ValueError("Refill rate must be greater than 0")
            
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
        self.cleanup_ttl = cleanup_ttl
        self.buckets: dict[str, TokenBucket] = {}
        self.lock = threading.Lock()

    def get_bucket(self, client_ip: str) -> TokenBucket:
        with self.lock:
            if client_ip not in self.buckets:
                self.buckets[client_ip] = TokenBucket(self.capacity, self.refill_rate)
            return self.buckets[client_ip]

    def allow_request(self, client_ip: str, tokens: int = 1) -> tuple[bool, int]:
        bucket = self.get_bucket(client_ip)
        return bucket.consume(tokens)


class TestTokenBucketAndRateLimiter(unittest.TestCase):

    def test_constructor_invalid_parameters(self):
        """Valida que o construtor rejeita taxas de recarga zero ou negativas para evitar ZeroDivisionError."""
        with self.assertRaises(ValueError):
            TokenBucket(capacity=10.0, refill_rate=0.0)
        with self.assertRaises(ValueError):
            TokenBucket(capacity=10.0, refill_rate=-1.5)
        with self.assertRaises(ValueError):
            TokenBucket(capacity=0.0, refill_rate=1.0)
        print("[OK] Construtor validado contra parâmetros inválidos (zero/negativos).")

    def test_token_bucket_exhaustion_and_retry_after(self):
        """Valida o estouro de cota e a serialização correta do Retry-After (inteiro em segundos)."""
        bucket = TokenBucket(capacity=2.0, refill_rate=1.0)
        
        # Consome todos os tokens
        allowed1, retry1 = bucket.consume(2)
        self.assertTrue(allowed1)
        self.assertEqual(retry1, 0)

        # Estouro de cota
        allowed2, retry_after = bucket.consume(1)
        self.assertFalse(allowed2, "A requisição deve ser negada ao estourar a cota")
        self.assertIsInstance(retry_after, int, "Retry-After deve ser um inteiro em segundos")
        self.assertGreaterEqual(retry_after, 1, "Retry-After deve indicar ao menos 1 segundo de espera")
        print(f"\n[OK] Estouro validado. Retry-After retornado: {retry_after} segundos (inteiro HTTP válido)")

    def test_token_refill_mechanism(self):
        """Valida a recarga gradual de tokens com o passar do tempo real."""
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