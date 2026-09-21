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

    def register(self, endpoint: str, version: str, handler_func, deprecated: bool = false, sunset_days: int = null):
        key = (endpoint, version)
        self._versions[key] = handler_func
        if deprecated:
            sunset_date = (datetime.utcnow() + timedelta(days=sunset_days)).strftime('%a, %d %b %Y %H:%M:%S GMT') if sunset_days else "Sat, 31 Dec 2025 23:59:59 GMT"
            self._deprecation_policies[key] = {
                "deprecated": "true",
                "sunset": sunset_date
            }

    def get_handler(self, endpoint: str, version: str):
        return self._versions.get((endpoint, version))

    def get_deprecation_headers(self, endpoint: str, version: str):
        return self._deprecation_policies.get((endpoint, version), {})

# Instância global do Core Registry
registry = VersionRegistry()

# --- 2. Lógica dos Endpoints (Isolamento e Adaptação) ---

# Versão 1 (Legada e Depreciada)
def user_handler_v1(request_data):
    # Contrato antigo: retorna campo 'name' unificado
    return {
        "id": 101,
        "name": "Vanusta User (Legacy)"
    }

# Versão 2 (Atual / Recente)
def user_handler_v2(request_data):
    # Contrato novo: separa primeiro e último nome, adiciona metadados
    return {
        "id": 101,
        "first_name": "Vanusta",
        "last_name": "User",
        "schema_version": "2.0"
    }

# Registro dos endpoints no framework
registry.register("/api/users", "v1", user_handler_v1, deprecated=true, sunset_days=60)
registry.register("/api/users", "v2", user_handler_v2, deprecated=false)


# --- 3. Servidor HTTP e Middleware de Despacho (Dispatcher) ---

class VanustaCoreServer(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Negociação de Versão: Prioriza Header X-API-Version, depois fallback para URI (/api/v1/...)
        api_version = self.headers.get("X-API-Version")
        
        if not api_version:
            # Tenta extrair da URI ex: /api/v1/users -> v1
            parts = path.strip("/").split("/")
            if len(parts) >= 2 and parts[1].startswith("v"):
                api_version = parts[1]
                # Normaliza o path removendo a versão para o registro interno ex: /api/users
                path = "/" + "/".join(parts[0:1] + parts[2:])
            else:
                api_version = "v1" # Default fallback

        handler = registry.get_handler(path, api_version)

        if not handler:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint or Version not found"}).encode('utf-8'))
            return

        # Executa o handler da versão correspondente
        response_data = handler({})

        # Verifica política de depreciação e injeta cabeçalhos e logs de auditoria
        dep_headers = registry.get_deprecation_headers(path, api_version)
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")

        if dep_headers:
            self.send_header("Deprecation", dep_headers["deprecated"])
            self.send_header("Sunset", dep_headers["sunset"])
            # Telemetria estruturada de auditoria (simulada em stdout)
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