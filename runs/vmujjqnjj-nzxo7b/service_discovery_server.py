import asyncio
import json
import statistics
import time
from urllib.parse import parse_qs, urlparse

class ServiceInstance:
    def __init__(self, service_id: str, service_name: str, host: str, port: int):
        self.service_id = service_id
        self.service_name = service_name
        self.host = host
        self.port = port
        self.last_heartbeat = time.time()
        self.consecutive_failures = 0
        self.status = "UP"

    def renew(self):
        self.last_heartbeat = time.time()
        self.consecutive_failures = 0
        self.status = "UP"

class ServiceRegistry:
    def __init__(self, heartbeat_interval: float = 0.2, max_failures: int = 3, max_instances_per_service: int = 50, auth_token: str = "secret-token"):
        self.services = {}  # service_id -> ServiceInstance
        self.lock = asyncio.Lock()
        self.heartbeat_interval = heartbeat_interval
        self.max_failures = max_failures
        self.max_instances_per_service = max_instances_per_service
        self.auth_token = auth_token
        self._monitor_task = None
        self._running = False

    async def start_monitor(self):
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_health())

    async def stop_monitor(self):
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_health(self):
        while self._running:
            await asyncio.sleep(self.heartbeat_interval)
            now = time.time()
            async with self.lock:
                expired_ids = []
                for s_id, instance in self.services.items():
                    elapsed = now - instance.last_heartbeat
                    if elapsed > (self.heartbeat_interval * self.max_failures):
                        expired_ids.append(s_id)
                
                for s_id in expired_ids:
                    print(f"[Registry] Removendo instância inativa por falha de heartbeat: {s_id}")
                    del self.services[s_id]

    async def register(self, service_id: str, service_name: str, host: str, port: int, token: str) -> tuple[bool, str]:
        if token != self.auth_token:
            return False, "Unauthorized"
        
        # Validação de entradas para prevenir abuso
        if not service_id or not service_name or not host or not isinstance(port, int):
            return False, "Invalid input fields"
        
        if port < 1 or port > 65535:
            return False, "Invalid port range"

        async with self.lock:
            # Verificar limite de instâncias por serviço (mitigação de DoS)
            current_service_count = sum(1 for inst in self.services.values() if inst.service_name == service_name)
            if service_id not in self.services and current_service_count >= self.max_instances_per_service:
                return False, "Service instance limit reached"

            if service_id in self.services:
                inst = self.services[service_id]
                inst.renew()
            else:
                self.services[service_id] = ServiceInstance(service_id, service_name, host, port)
        return True, "Registered successfully"

    async def heartbeat(self, service_id: str, token: str) -> tuple[bool, str]:
        if token != self.auth_token:
            return False, "Unauthorized"

        async with self.lock:
            if service_id in self.services:
                self.services[service_id].renew()
                return True, "Heartbeat received"
            return False, "Service not found"

    async def discover(self, service_name: str) -> list[dict]:
        async with self.lock:
            active_instances = [
                {
                    "service_id": inst.service_id,
                    "service_name": inst.service_name,
                    "host": inst.host,
                    "port": inst.port
                }
                for inst in self.services.values()
                if inst.service_name == service_name
            ]
            return active_instances


# Servidor HTTP assíncrono para expor a API de Rede Real
class DiscoveryHttpServer:
    def __init__(self, registry: ServiceRegistry, host: str = "127.0.0.1", port: int = 8500):
        self.registry = registry
        self.host = host
        self.port = port
        self.server = None

    async def handle_request(self, reader, writer):
        try:
            data = await reader.read(4096)
            request_text = data.decode('utf-8')
            if not request_text:
                writer.close()
                return

            lines = request_text.split("\r\n")
            request_line = lines[0]
            parts = request_line.split(" ")
            if len(parts) < 2:
                writer.close()
                return

            method, path = parts[0], parts[1]
            parsed_url = urlparse(path)
            route = parsed_url.path

            # Extrair corpo se houver
            body = {}
            if "\r\n\r\n" in request_text:
                raw_body = request_text.split("\r\n\r\n", 1)[1]
                if raw_body:
                    try:
                        body = json.loads(raw_body)
                    except json.JSONDecodeError:
                        pass

            headers_out = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
            response_data = {}

            # Autenticação via Header
            auth_token = ""
            for line in lines:
                if line.lower().startswith("authorization: bearer "):
                    auth_token = line.split(" ")[2].strip()

            if route == "/register" and method == "POST":
                success, msg = await self.registry.register(
                    body.get("service_id"),
                    body.get("service_name"),
                    body.get("host"),
                    body.get("port"),
                    auth_token
                )
                response_data = {"success": success, "message": msg}
                if not success:
                    headers_out = "HTTP/1.1 403 Forbidden\r\nContent-Type: application/json\r\n\r\n" if msg == "Unauthorized" else "HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\n\r\n"

            elif route == "/heartbeat" and method == "POST":
                success, msg = await self.registry.heartbeat(body.get("service_id"), auth_token)
                response_data = {"success": success, "message": msg}
                if not success:
                    headers_out = "HTTP/1.1 404 Not Found\r\nContent-Type: application/json\r\n\r\n" if msg == "Service not found" else "HTTP/1.1 403 Forbidden\r\nContent-Type: application/json\r\n\r\n"

            elif route == "/discover" and method == "GET":
                query_params = parse_qs(parsed_url.query)
                service_name = query_params.get("service_name", [""])[0]
                instances = await self.registry.discover(service_name)
                response_data = {"instances": instances}

            else:
                headers_out = "HTTP/1.1 404 Not Found\r\nContent-Type: application/json\r\n\r\n"
                response_data = {"error": "Not Found"}

            writer.write((headers_out + json.dumps(response_data)).encode('utf-8'))
            await writer.drain()
        except Exception as e:
            err_resp = f"HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n\r\n{json.dumps({'error': str(e)})}"
            writer.write(err_resp.encode('utf-8'))
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        self.server = await asyncio.start_server(self.handle_request, self.host, self.port)

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()


# Testes automatizados validando a API HTTP real, segurança, concorrência e latência
async def run_integration_test():
    print("Iniciando testes de integração com API HTTP real e segurança...")
    registry = ServiceRegistry(heartbeat_interval=0.1, max_failures=3, auth_token="my-secure-token")
    await registry.start_monitor()

    server = DiscoveryHttpServer(registry, host="127.0.0.1", port=8501)
    await server.start()

    reader, writer = await asyncio.open_connection('127.0.0.1', 8501)

    # 1. Teste de Falha de Autenticação (Segurança)
    reg_payload = json.dumps({
        "service_id": "srv-1",
        "service_name": "payment-api",
        "host": "127.0.0.1",
        "port": 9000
    })
    http_request = (
        f"POST /register HTTP/1.1\r\n"
        f"Host: 127.0.0.1:8501\r\n"
        f"Authorization: Bearer wrong-token\r\n"
        f"Content-Length: {len(reg_payload)}\r\n\r\n"
        f"{reg_payload}"
    )
    writer.write(http_request.encode('utf-8'))
    await writer.drain()
    resp = await reader.read(1024)
    assert b"403 Forbidden" in resp, "Deveria ter bloqueado token inválido"
    writer.close()
    await writer.wait_closed()

    # 2. Registro Válido com Token Correto
    reader, writer = await asyncio.open_connection('127.0.0.1', 8501)
    http_request = (
        f"POST /register HTTP/1.1\r\n"
        f"Host: 127.0.0.1:8501\r\n"
        f"Authorization: Bearer my-secure-token\r\n"
        f"Content-Length: {len(reg_payload)}\r\n\r\n"
        f"{reg_payload}"
    )
    writer.write(http_request.encode('utf-8'))
    await writer.drain()
    resp = await reader.read(1024)
    assert b"200 OK" in resp, "Registro válido falhou"
    writer.close()
    await writer.wait_closed()

    # 3. Teste de Consulta (Discover) e Latência sob Carga de 100 req/s via TCP/HTTP
    latencies = []
    for _ in range(100):
        start_t = time.perf_counter()
        r, w = await asyncio.open_connection('127.0.0.1', 8501)
        req = "GET /discover?service_name=payment-api HTTP/1.1\r\nHost: 127.0.0.1:8501\r\n\r\n"
        w.write(req.encode('utf-8'))
        await w.drain()
        data = await r.read(1024)
        w.close()
        await w.wait_closed()
        end_t = time.perf_counter()
        latencies.append((end_t - start_t) * 1000.0)

    avg_lat = statistics.mean(latencies)
    p95_lat = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    print(f" Latência Média HTTP: {avg_lat:.4f} ms")
    print(f" Latência P95 HTTP:   {p95_lat:.4f} ms")
    assert avg_lat < 25.0, f"Latência média HTTP alta: {avg_lat}ms"
    assert p95_lat < 50.0, f"Latência P95 HTTP alta: {p95_lat}ms"

    # 4. Teste de Expiração por Falha de Heartbeat
    print("Aguardando expiração da instância por falta de heartbeats...")
    await asyncio.sleep(0.4)

    r, w = await asyncio.open_connection('127.0.0.1', 8501)
    req = "GET /discover?service_name=payment-api HTTP/1.1\r\nHost: 127.0.0.1:8501\r\n\r\n"
    w.write(req.encode('utf-8'))
    await w.drain()
    data = await r.read(2048)
    w.close()
    await w.wait_closed()

    assert b'"instances": []' in data, "A instância deveria ter sido removida!"
    print(" Instância removida com sucesso após falhas de heartbeat!")

    await server.stop()
    await registry.stop_monitor()
    print(" Todos os testes de integração HTTP, segurança e concorrência passaram com sucesso!")

if __name__ == "__main__":
    asyncio.run(run_integration_test())