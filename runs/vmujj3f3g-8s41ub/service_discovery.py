import asyncio
import time
import statistics

class ServiceInstance:
    def __init__(self, service_id: str, service_name: str, host: str, port: int, heartbeat_interval: float = 0.1):
        self.service_id = service_id
        self.service_name = service_name
        self.host = host
        self.port = port
        self.last_heartbeat = time.time()
        self.heartbeat_interval = heartbeat_interval
        self.consecutive_failures = 0
        self.status = "UP"

    def renew(self):
        self.last_heartbeat = time.time()
        self.consecutive_failures = 0
        self.status = "UP"

class ServiceRegistry:
    def __init__(self, heartbeat_interval: float = 0.1, max_failures: int = 3):
        self.services = {}  # service_id -> ServiceInstance
        self.lock = asyncio.Lock()
        self.heartbeat_interval = heartbeat_interval
        self.max_failures = max_failures
        self._monitor_task = None
        self._running = False

    async def start(self):
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_health())

    async def stop(self):
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def register(self, service_id: str, service_name: str, host: str, port: int):
        async with self.lock:
            instance = ServiceInstance(service_id, service_name, host, port, self.heartbeat_interval)
            self.services[service_id] = instance
            return instance

    async def heartbeat(self, service_id: str):
        async with self.lock:
            if service_id in self.services:
                self.services[service_id].renew()
                return True
            return False

    async def discover(self, service_name: str):
        async with self.lock:
            now = time.time()
            active_nodes = []
            for instance in self.services.values():
                if instance.service_name == service_name and instance.status == "UP":
                    active_nodes.append(instance)
            return active_nodes

    async def _monitor_health(self):
        while self._running:
            await asyncio.sleep(self.heartbeat_interval)
            async with self.lock:
                now = time.time()
                to_remove = []
                for service_id, instance in self.services.items():
                    elapsed = now - instance.last_heartbeat
                    # Se passou mais tempo que o intervalo * max_failures, remove diretamente
                    if elapsed > (self.heartbeat_interval * self.max_failures):
                        instance.status = "DOWN"
                        to_remove.append(service_id)
                
                for service_id in to_remove:
                    del self.services[service_id]

async def main():
    print("Iniciando protótipo corrigido de Service Discovery...")
    
    # Configuração com intervalos curtos para teste rápido e determinístico
    registry = ServiceRegistry(heartbeat_interval=0.05, max_failures=3)
    await registry.start()

    # 1. Registrar um serviço
    await registry.register("srv-1", "payment-service", "127.0.0.1", 8080)
    
    nodes = await registry.discover("payment-service")
    print(f" Nós descobertos logo após registro: {len(nodes)} (Esperado: 1)")
    assert len(nodes) == 1

    # 2. Enviar heartbeats contínuos mantendo o nó vivo
    for _ in range(3):
        await asyncio.sleep(0.03)
        await registry.heartbeat("srv-1")

    nodes_alive = await registry.discover("payment-service")
    print(f" Nó ativo após heartbeats contínuos: {len(nodes_alive)} (Esperado: 1)")
    assert len(nodes_alive) == 1

    # 3. Parar de enviar heartbeats e aguardar a expiração (heartbeat_interval * max_failures + margem)
    print("Aguardando falha de heartbeats (sem renovar)...")
    await asyncio.sleep(0.25)

    nodes_dead = await registry.discover("payment-service")
    print(f" Nós ativos após falha de heartbeats: {len(nodes_dead)} (Esperado: 0)")
    assert len(nodes_dead) == 0

    # 4. Teste de Carga e Latência (Resolução de nomes sob 100 req/s)
    print("Executando teste de latência e carga (100 req/s simuladas)...")
    await registry.register("srv-2", "user-service", "127.0.0.1", 8081)
    
    latencies = []
    for _ in range(100):
        start_time = time.perf_counter()
        _ = await registry.discover("user-service")
        end_time = time.perf_counter()
        latencies.append((end_time - start_time) * 1000.0) # converter para ms

    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)

    print(f" Latência Média: {avg_latency:.4f} ms (Critério: < 20ms)")
    print(f" Latência P95:   {p95_latency:.4f} ms (Critério: < 50ms)")
    
    assert avg_latency < 20.0, f"Latência média muito alta: {avg_latency}ms"
    assert p95_latency < 50.0, f"Latência P95 muito alta: {p95_latency}ms"

    await registry.stop()
    print("\n Experimento executado com sucesso e todos os asserts passaram!")

if __name__ == "__main__":
    asyncio.run(main())