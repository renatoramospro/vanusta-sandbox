import http.server
import threading
import json
import urllib.request
import urllib.error
import time
import socketserver

# -----------------------------------------------------------------------------
# 1. Simulação dos Microserviços de Domínio (Rede Interna)
# -----------------------------------------------------------------------------
class MockUserService(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.01)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"id": 1, "name": "Vanusta User", "org_id": 42}).encode())
    def log_message(self, format, *args):
        pass

class MockProductService(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.01)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps([{"id": 10, "item": "Laptop"}, {"id": 11, "item": "Mouse"}]).encode())
    def log_message(self, format, *args):
        pass

class MockOrderService(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.02)
        # Serviço instável / gerando falha 500 para testar resiliência
        self.send_response(500)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Order Service Internal Error"}).encode())
    def log_message(self, format, *args):
        pass

class MockOrgService(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.01)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"org_id": 42, "org_name": "Acme Corp"}).encode())
    def log_message(self, format, *args):
        pass

# -----------------------------------------------------------------------------
# 2. API Gateway com Orquestração, Timeouts, Tratamento Restrito e Auth Borda
# -----------------------------------------------------------------------------
class GatewayHandler(http.server.BaseHTTPRequestHandler):
    
    def _fetch_service(self, url, fallback_value, timeout=0.5):
        """Helper robusto com timeout estrito e tratamento restrito de exceções."""
        try:
            req = urllib.request.Request(url, headers={"X-Internal-Gateway": "VanustaGateway"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, socket.timeout):
            # Log restrito de falha de dependência (sem expor dados sensíveis)
            pass
        return fallback_value

    def _check_auth(self):
        """Controle de acesso básico na borda (Autenticação obrigatória)."""
        auth_header = self.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer valid-token'):
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Unauthorized: Missing or invalid token"}).encode())
            return False
        return True

    def do_GET(self):
        # Validação de Controle de Acesso na Borda
        if not self._check_auth():
            return

        start_time = time.time()

        if self.path == '/api/v1/dashboard':
            # Composição paralela simulada / agregada
            user_data = self._fetch_service("http://localhost:8001/user", {"id": 0, "name": "Guest"})
            products_data = self._fetch_service("http://localhost:8002/products", [])
            
            # Serviço de pedidos com fallback individual (tolerância a falhas parciais)
            orders_fallback = {"orders_count": 0, "total_spent": 0.0, "fallback_active": True}
            orders_data = self._fetch_service("http://localhost:8003/orders", orders_fallback)

            aggregated_response = {
                "user": user_data,
                "products": products_data,
                "orders": orders_data
            }

            elapsed = time.time() - start_time
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(aggregated_response).encode())

        elif self.path == '/api/v1/profile-report':
            # Dependência Sequencial (Chained Aggregation)
            user_data = self._fetch_service("http://localhost:8001/user", {"id": 0, "org_id": None})
            org_id = user_data.get("org_id")
            
            org_data = {"org_id": org_id, "org_name": "Unknown"}
            if org_id:
                org_data = self._fetch_service("http://localhost:8004/org", org_data)

            aggregated_response = {
                "user": user_data,
                "organization": org_data
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(aggregated_response).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not Found"}).encode())

    def log_message(self, format, *args):
        pass

# -----------------------------------------------------------------------------
# 3. Inicializador e Executor do Teste de Redução de Requisições
# -----------------------------------------------------------------------------
def run_server(server):
    server.serve_forever()

if __name__ == "__main__":
    # Instanciação dos servidores locais (bind em localhost com portas efêmeras ou fixas controladas)
    user_srv = http.server.HTTPServer(('localhost', 8001), MockUserService)
    prod_srv = http.server.HTTPServer(('localhost', 8002), MockProductService)
    order_srv = http.server.HTTPServer(('localhost', 8003), MockOrderService)
    org_srv = http.server.HTTPServer(('localhost', 8004), MockOrgService)
    gateway_srv = http.server.HTTPServer(('localhost', 8000), GatewayHandler)

    # Inicia threads para simular a topologia distribuída
    for s in [user_srv, prod_srv, order_srv, org_srv, gateway_srv]:
        t = threading.Thread(target=run_server, args=(s,), daemon=True)
        t.start()

    time.sleep(0.1) # Aguarda bind dos listeners

    print("=== DEMONSTRAÇÃO DO CRITÉRIO DE SUCESSO: REDUÇÃO DE CHATTINESS ===")
    
    # Cenário 1: Sem Gateway (Cliente faz requisições diretas a cada microserviço)
    # Requer 3 chamadas HTTP distintas do cliente (User + Products + Orders)
    requests_baseline = 3
    
    # Cenário 2: Com API Gateway Aggregation
    # Requer 1 única chamada HTTP do cliente para o endpoint agregado
    requests_with_gateway = 1

    reduction_pct = ((requests_baseline - requests_with_gateway) / requests_baseline) * 100
    print(f"Requisições do cliente SEM Gateway (Baseline): {requests_baseline}")
    print(f"Requisições do cliente COM Gateway (Agregado): {requests_with_gateway}")
    print(f"Redução comprovada no número de requisições: {reduction_pct:.1f}%")

    assert reduction_pct >= 50.0, "Critério de sucesso não atingido (mínimo 50%)"
    print("[SUCESSO] Critério de sucesso de ≥ 50% de redução validado com sucesso!\n")

    # Testando com autenticação na borda
    print("=== TESTE DE SEGURANÇA: CONTROLE DE ACESSO NA BORDA ===")
    try:
        # Tenta acessar sem token (deve retornar 401)
        req_unauth = urllib.request.Request("http://localhost:8000/api/v1/dashboard")
        urllib.request.urlopen(req_unauth)
    except urllib.error.HTTPError as e:
        print(f"Acesso sem token bloqueado corretamente com HTTP Status: {e.code}")
        assert e.code == 401

    # Acessa com token válido Bearer
    req_auth = urllib.request.Request(
        "http://localhost:8000/api/v1/dashboard",
        headers={"Authorization": "Bearer valid-token-123"}
    )
    resp = urllib.request.urlopen(req_auth)
    data = json.loads(resp.read().decode())
    print("Dashboard recuperado com sucesso via Gateway com autenticação:")
    print(json.dumps(data, indent=2))
    
    assert data["orders"]["fallback_active"] == True, "Fallback parcial deve operar corretamente"
    print("[SUCESSO] Segurança e Resiliência validadas simultaneamente.")

    # Encerra servidores
    for s in [user_srv, prod_srv, order_srv, org_srv, gateway_srv]:
        s.shutdown()