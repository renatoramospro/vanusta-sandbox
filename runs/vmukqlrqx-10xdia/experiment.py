import http.server
import threading
import json
import urllib.request
import time
import socketserver

# 1. Simulação dos Microserviços de Domínio
class MockUserService(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.02)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"id": 1, "name": "Vanusta User", "org_id": 42}).encode())
    def log_message(self, format, *args):
        pass

class MockProductService(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.02)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps([{"id": 10, "item": "Laptop"}, {"id": 11, "item": "Mouse"}]).encode())
    def log_message(self, format, *args):
        pass

# Simulação de microserviço instável/fora do ar para testar falha parcial
class MockFailingOrderService(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.05)
        # Simula erro interno no serviço de pedidos
        self.send_response(500)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Order Service Down"}).encode())
    def log_message(self, format, *args):
        pass

class MockOrgService(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.02)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"org_id": 42, "org_name": "Acme Corp"}).encode())
    def log_message(self, format, *args):
        pass


# 2. API Gateway com Padrão de Aggregation, Fallback e Dependência Sequencial
class RobustApiGateway(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/v1/dashboard':
            # Composição com Tolerância a Falhas Parciais (Fallback)
            
            # 1. User Service
            try:
                user_req = urllib.request.urlopen("http://localhost:8001/user", timeout=1)
                user_data = json.loads(user_req.read().decode())
            except Exception:
                user_data = {"id": None, "name": "Indisponível"}

            # 2. Product Service
            try:
                prod_req = urllib.request.urlopen("http://localhost:8002/products", timeout=1)
                prod_data = json.loads(prod_req.read().decode())
            except Exception:
                prod_data = []

            # 3. Order Service (Simulando falha parcial)
            try:
                order_req = urllib.request.urlopen("http://localhost:8003/orders", timeout=1)
                order_data = json.loads(order_req.read().decode())
            except Exception:
                # Fallback graceful: retorna estrutura vazia em vez de derrubar a página inteira
                order_data = {"orders_count": 0, "total_spent": 0.0, "fallback_active": True}

            composite_response = {
                "user": user_data,
                "products": prod_data,
                "orders": order_data
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(composite_response).encode())

        elif self.path == '/api/v1/profile-report':
            # Dependência Sequencial (Chained Aggregation):
            # Passo 1: Busca dados do usuário para extrair o org_id
            try:
                user_req = urllib.request.urlopen("http://localhost:8001/user", timeout=1)
                user_data = json.loads(user_req.read().decode())
                org_id = user_data.get("org_id")
            except Exception:
                org_id = None

            # Passo 2: Usa o org_id obtido para consultar o serviço de Organização
            org_data = {}
            if org_id:
                try:
                    org_req = urllib.request.urlopen(f"http://localhost:8004/orgs?id={org_id}", timeout=1)
                    org_data = json.loads(org_req.read().decode())
                except Exception:
                    org_data = {"error": "Org service unavailable"}

            report = {
                "user": user_data,
                "organization": org_data
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(report).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

# Função auxiliar para iniciar servidores em background
def run_server(handler, port):
    server = socketserver.TCPServer(("127.0.0.1", port), handler)
    server.serve_forever()

if __name__ == '__main__':
    # Inicializando microserviços em portas distintas
    threading.Thread(target=run_server, args=(MockUserService, 8001), daemon=True).start()
    threading.Thread(target=run_server, args=(MockProductService, 8002), daemon=True).start()
    threading.Thread(target=run_server, args=(MockFailingOrderService, 8003), daemon=True).start()
    threading.Thread(target=run_server, args=(MockOrgService, 8004), daemon=True).start()
    
    # Inicializando o API Gateway na porta 8000
    threading.Thread(target=run_server, args=(RobustApiGateway, 8000), daemon=True).start()
    
    time.sleep(0.5) # Aguarda inicialização

    print("=== TESTE 1: Resiliência a Falhas Parciais (Fallback no Dashboard) ===")
    start_t = time.time()
    resp = urllib.request.urlopen("http://localhost:8000/api/v1/dashboard")
    data = json.loads(resp.read().decode())
    duration = time.time() - start_t
    
    print(f"Resposta consolidada com sucesso (tempo: {duration:.4f}s):")
    print(json.dumps(data, indent=2))
    
    # Validações estritas
    assert data["user"]["name"] == "Vanusta User", "Falha no serviço de usuário"
    assert data["orders"]["fallback_active"] == True, "Fallback do serviço de pedidos não acionado"
    print("[SUCESSO] Fallback por serviço individual operou corretamente sem derrubar a requisição.")

    print("\n=== TESTE 2: Dependência Sequencial (Chained Aggregation) ===")
    resp_seq = urllib.request.urlopen("http://localhost:8000/api/v1/profile-report")
    data_seq = json.loads(resp_seq.read().decode())
    print("Relatório sequencial consolidado:")
    print(json.dumps(data_seq, indent=2))
    
    assert data_seq["organization"]["org_name"] == "Acme Corp", "Falha na agregação sequencial"
    print("[SUCESSO] Agregação sequencial executada com sucesso com base em IDs intermediários.")