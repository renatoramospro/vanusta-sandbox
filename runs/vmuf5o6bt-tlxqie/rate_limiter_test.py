import time
import unittest
from http import HTTPStatus
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.request
import json

class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1) -> tuple[bool, float]:
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now

            # Reabastece o balde baseado no tempo decorrido
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0.0
            else:
                # Calcula o tempo necessário para acumular tokens suficientes
                missing_tokens = tokens - self.tokens
                retry_after = missing_tokens / self.refill_rate
                return False, retry_after

class RateLimiterMiddleware:
    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets = {}
        self.lock = threading.Lock()

    def get_bucket(self, ip: str) -> TokenBucket:
        with self.lock:
            if ip not in self.buckets:
                self.buckets[ip] = TokenBucket(self.capacity, self.refill_rate)
            return self.buckets[ip]

    def check_rate_limit(self, ip: str) -> tuple[bool, float]:
        bucket = self.get_bucket(ip)
        return bucket.consume(1)

# Instância global do Rate Limiter para o servidor de teste
limiter = RateLimiterMiddleware(capacity=2.0, refill_rate=1.0) # 2 tokens de capacidade, 1 token/segundo de recarga

class TestServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        client_ip = self.client_address[0]
        allowed, retry_after = limiter.check_rate_limit(client_ip)

        if not allowed:
            self.send_response(429)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Retry-After', str(int(max(1.0, retry_after))))
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Too Many Requests"}).encode())
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())
            
    def log_message(self, format, *args):
        # Silencia logs do servidor HTTP durante os testes
        pass

class TestRateLimiterIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(('127.0.0.1', 0), TestServerHandler)
        cls.port = cls.server.server_port
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def make_request(self):
        url = f"http://127.0.0.1:{self.port}/api"
        try:
            req = urllib.request.urlopen(url)
            return req.status, None
        except urllib.error.HTTPError as e:
            retry_after = e.headers.get('Retry-After')
            return e.code, retry_after

    def test_rate_limiting_flow(self):
        # O balde tem capacidade 2. As duas primeiras requisições devem passar.
        status1, _ = self.make_request()
        self.assertEqual(status1, 200, "Primeira requisição deveria ser permitida")

        status2, _ = self.make_request()
        self.assertEqual(status2, 200, "Segunda requisição deveria ser permitida (esgotando o balde)")

        # A terceira requisição imediata deve estourar a cota (429)
        status3, retry_after = self.make_request()
        self.assertEqual(status3, 429, "Terceira requisição deveria retornar 429 Too Many Requests")
        self.assertIsNotNone(retry_after, "O cabeçalho Retry-After deve estar presente")
        print(f"\n[OK] Teste de estouro bem-sucedido. Status: {status3}, Retry-After: {retry_after}s")

        # Aguarda o reabastecimento do balde (1 token por segundo -> 1 segundo de espera)
        print("[INFO] Aguardando 1.1 segundos para recarga de tokens...")
        time.sleep(1.1)

        # A requisição seguinte deve passar novamente graças à recarga gradual
        status4, _ = self.make_request()
        self.assertEqual(status4, 200, "Requisição após recarga deveria ser permitida")
        print(f"[OK] Teste de recarga bem-sucedido. Status após espera: {status4}")

if __name__ == '__main__':
    unittest.main()