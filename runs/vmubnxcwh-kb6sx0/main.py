import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime, timedelta

# --- 1. Framework de Versionamento e Depreciação ---

class VersionRegistry:
    """Gerenciador central de versões de endpoints e suas políticas de depreciação."""
    def __init__(self):
        self._versions = {}
        self._deprecation_policies = {}

    def register(self, endpoint: str, version: str, handler_func, deprecated: bool = False, sunset_days: int = None):
        key = (endpoint, version)
        self._versions[key] = handler_func
        if deprecated:
            sunset_date = datetime.utcnow() + timedelta(days=sunset_days) if sunset_days else None
            self._deprecation_policies[key] = {
                "deprecated": True,
                "sunset": sunset_date.strftime('%a, %d %b %Y %H:%M:%S GMT') if sunset_date else "No Sunset Date"
            }

    def get_handler(self, endpoint: str, version: str):
        return self._versions.get((endpoint, version))

    def get_deprecation_info(self, endpoint: str, version: str):
        return self._deprecation_policies.get((endpoint, version))

# Instancia o registro global do Vanusta-Core
registry = VersionRegistry()

# --- 2. Definição de Handlers por Versão (Isolamento de Contrato) ---

def handle_get_users_v1(handler):
    # Versão antiga contendo payload legado
    return {"version": "v1", "users": [{"id": 1, "name": "Alice Legacy"}]}

def handle_get_users_v2(handler):
    # Versão atualizada com nova estrutura de dados (não quebra clientes da v2)
    return {"version": "v2", "data": [{"user_id": 1, "full_name": "Alice Legacy", "status": "ACTIVE"}]}

# Registro dos endpoints críticos com políticas de depreciação na v1
registry.register("/api/users", "v1", handle_get_users_v1, deprecated=True, sunset_days=30)
registry.register("/api/users", "v2", handle_get_users_v2, deprecated=False)


# --- 3. Servidor HTTP e Dispatcher de Roteamento ---

class VanustaCoreServer(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Estratégia de Roteamento Híbrida: Via Header ou Prefixo de URI
        api_version = self.headers.get("X-API-Version")
        
        if path.startswith("/api/v1/"):
            api_version = "v1"
            path = path.replace("/v1", "", 1)
        elif path.startswith("/api/v2/"):
            api_version = "v2"
            path = path.replace("/v2", "", 1)
        elif not api_version:
            api_version = "v1" # Versão padrão de fallback caso não informada

        handler_func = registry.get_handler(path, api_version)

        if not handler_func:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint or version not found"}).encode('utf-8'))
            return

        # Executa a lógica de negócio mapeada
        response_data = handler_func(self)

        # Processamento de Depreciação e Cabeçalhos HTTP
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        
        dep_info = registry.get_deprecation_info(path, api_version)
        if dep_info:
            self.send_header("Deprecation", "true")
            self.send_header("Sunset", dep_info["sunset"])
            # Telemetria / Auditoria de uso de versões obsoletas
            print(f"[AUDIT-LOG] WARNING: Client accessed deprecated endpoint {path} using version {api_version}")

        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def log_message(self, format, *args):
        # Silencia logs padrão do http.server para manter o output limpo
        pass


# --- 4. Teste Automatizado do Framework ---
if __name__ == "__main__":
    import threading
    import urllib.request

    server = HTTPServer(('127.0.0.1', 8089), VanustaCoreServer)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    base_url = "http://127.0.0.1:8089"

    print("--- Testando Requisição na Versão 1 (Depreciada via URI) ---")
    req_v1 = urllib.request.Request(f"{base_url}/api/v1/users")
    with urllib.request.urlopen(req_v1) as response:
        print(f"Status: {response.status}")
        print(f"Deprecation Header: {response.headers.get('Deprecation')}")
        print(f"Sunset Header: {response.headers.get('Sunset')}")
        print(f"Body: {response.read().decode('utf-8')}")

    print("\n--- Testando Requisição na Versão 2 (Atual via Header) ---")
    req_v2 = urllib.request.Request(f"{base_url}/api/users", headers={"X-API-Version": "v2"})
    with urllib.request.urlopen(req_v2) as response:
        print(f"Status: {response.status}")
        print(f"Deprecation Header: {response.headers.get('Deprecation')}")
        print(f"Body: {response.read().decode('utf-8')}")

    server.shutdown()