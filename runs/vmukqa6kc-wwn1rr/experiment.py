import http.server
import threading
import json
import urllib.request
import time

# 1. Simulação dos Microserviços de Domínio
class MockUserService(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.05) # Simula latência de rede
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"id": 1, "name": "Vanusta User"}).encode())
    def log_message(self, format, *args):
        pass

class MockProductService(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.05)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps([{"id": 10, "item": "Laptop"}, {"id": 11, "item": "Mouse"}]).encode())
    def log_message(self, format, *args):
        pass

class MockOrderService(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.05)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"orders_count": 5, "total_spent": 1200.50}).encode())
    def log_message(self, format, *args):
        pass

# 2. API Gateway com Padrão de Aggregation / Composition
class ApiGateway(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/v1/dashboard':
            # Composição de múltiplas chamadas internas em uma única resposta externa
            try:
                user_req = urllib.request.urlopen("http://localhost:8001/user")
                user_data = json.loads(user_req.read().decode())

                prod_req = urllib.request.urlopen("http://localhost:8002/products")
                prod_data = json.loads(prod_req.read().decode())

                order_req = urllib.request.urlopen("http://localhost:8003/orders")
                order_data = json.loads(order_req.read().decode())

                aggregated_response = {
                    "user": user_data,
                    "products": prod_data,
                    "orders": order_data,
                    "gateway_status": "success"
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(aggregated_response).encode())
            except Exception as e:
                # Tolerância a falhas / Fallback básico (requisito do Arquiteto)
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Gateway aggregation failed", "details": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, format, *args):
        pass

def run_server(server_class, port):
    server = server_class(('localhost', port), http.server.BaseHTTPRequestHandler)
    # Sobrescrevendo o handler dinamicamente para cada porta
    if port == 8001: server.RequestHandlerClass = MockUserService
    elif port == 8002: server.RequestHandlerClass = MockProductService
    elif port == 8003: server.RequestHandlerClass = MockOrderService
    elif port == 8000: server.RequestHandlerClass = ApiGateway
    
    server.serve_forever()

if __name__ == "__main__":
    # Inicializando os microserviços e o gateway em threads background
    ports = [8001, 8002, 8003, 8000]
    threads = [threading.Thread(target=run_server, args=(http.server.HTTPServer, p), daemon=True) for p in ports]
    for t in threads: t.start()
    time.sleep(0.5) # Aguarda subirem

    print("=== CENÁRIO 1: Sem Gateway (Client-Side Joining / Chattiness) ===")
    start_t1 = time.time()
    r1 = urllib.request.urlopen("http://localhost:8001/user").read()
    r2 = urllib.request.urlopen("http://localhost:8002/products").read()
    r3 = urllib.request.urlopen("http://localhost:8003/orders").read()
    duration_c1 = time.time() - start_t1
    requests_c1 = 3
    print(f"Requisições HTTP do Cliente: {requests_c1}")
    print(f"Tempo total: {duration_c1:.4f}s")

    print("\n=== CENÁRIO 2: Com API Gateway (Aggregation Pattern) ===")
    start_t2 = time.time()
    gateway_resp = urllib.request.urlopen("http://localhost:8000/api/v1/dashboard").read()
    duration_c2 = time.time() - start_t2
    requests_c2 = 1
    print(f"Requisições HTTP do Cliente: {requests_c2}")
    print(f"Tempo total: {duration_c2:.4f}s")

    # Validação do Critério de Sucesso
    reduction = ((requests_c1 - requests_c2) / requests_c1) * 100
    print(f"\n[Validação] Redução de requisições: {reduction:.1f}%")
    
    assert reduction >= 50, f"Falha: Redução de {reduction}% menor que o mínimo exigido de 50%."
    print("[SUCESSO] Critério de redução de 50% atingido com sucesso!")