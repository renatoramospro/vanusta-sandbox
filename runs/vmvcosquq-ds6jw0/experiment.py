import http.server
import threading
import time
import urllib.request

# Dicionário de mapeamento estático: Rota Dinâmica -> Lista de Assets para Preload
STATIC_DEPENDENCIES = {
    "/api/dashboard": [
        "</static/main.css>; rel=preload; as=style",
        "</static/logo.png>; rel=preload; as=image"
    ]
}

class PreloadMiddlewareHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        start_time = time.time()
        
        # Simulação de processamento de rota sem assets (ex: /api/health)
        if self.path == "/api/health":
            # Rota sem assets: latência deve ser estritamente mínima, sem overhead
            body = b'{"status": "ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Rota dinâmica com possíveis assets mapeados
        # Verifica se há dependências estáticas para esta rota (Preloading)
        preload_links = STATIC_DEPENDENCIES.get(self.path, [])

        # Simula processamento dinâmico de banco de dados/API
        time.sleep(0.01) 
        
        body = b'{"data": "dynamic content loaded"}'
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        
        # Injeta os cabeçalhos Link para preloading se houver dependências
        for link in preload_links:
            self.send_header("Link", link)
            
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def run_server(server):
    server.serve_forever()

if __name__ == "__main__":
    # Inicia o servidor de teste em uma thread separada
    server = http.server.HTTPServer(("127.0.0.1", 0), PreloadMiddlewareHandler)
    port = server.server_port
    t = threading.Thread(target=run_server, args=(server,), daemon=True)
    t.start()
    
    base_url = f"http://127.0.0.1:{port}"
    
    # 1. Testando Rota com Preload (/api/dashboard)
    req_dashboard = urllib.request.Request(f"{base_url}/api/dashboard")
    with urllib.request.urlopen(req_dashboard) as resp:
        headers = resp.headers.get_all("Link")
        print(f"[TESTE 1] Rota /api/dashboard - Cabeçalhos Link recebidos: {headers}")
        assert headers is not None, "Falha: Cabeçalhos de preload não encontrados!"
        assert len(headers) == 2, f"Esperado 2 links de preload, obtido {len(headers)}"

    # 2. Testando Rota Sem Assets (/api/health) - Validando ausência de impacto
    req_health = urllib.request.Request(f"{base_url}/api/health")
    with urllib.request.urlopen(req_health) as resp:
        headers_health = resp.headers.get_all("Link")
        print(f"[TESTE 2] Rota /api/health - Cabeçalhos Link recebidos: {headers_health}")
        assert headers_health is None, "Falha: Rota pura não deveria conter cabeçalhos de preload!"

    print("\n[SUCESSO] Experimento executado e validado com sucesso: Preloading ativo em rotas dinâmicas e isolamento perfeito em rotas puras.")