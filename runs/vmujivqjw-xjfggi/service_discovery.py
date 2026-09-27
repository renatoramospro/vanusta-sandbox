import asyncio
import time
import statistics

class ServiceInstance:
    def __init__(self, service_id: str, service_name: str, host: str, port: int):
        self.service_id = service_id
        self.service_name = service_name
        self.host = host
        self.port = port
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
            instance = ServiceInstance(service_id, service_name, host, port)
            self.services[service_id] = instance
            return instance

    async def heartbeat(self, service_id: str) -> bool:
        async with self.lock:
            if service_id in self.services:
                inst = self.services[service_id]
                inst.last_heartbeat = time.time()
                inst.consecutive_failures = 0
                inst.status = "UP"
                return True
            return False

    async def discover(self, service_name: str):
        async with self.lock:
            now = time.time()
            # Retorna apenas instâncias ativas
            return [
                {"id": inst.service_id, "host": inst.host, "port": inst.port}
                for inst in self.services.values()
                if inst.service_name == service_name and inst.status == "UP"
            ]

    async def _monitor_health(self):
        while self._running:
            await asyncio.sleep(self.heartbeat_interval)
            async with self.lock:
                now = time.time()
                to_remove = []
                for s_id, inst in self.services.items():
                    # Se o tempo desde o último heartbeat exceder o intervalo * max_failures
                    if now - inst.last_heartbeat > (self.heartbeat_interval * self.max_failures):
                        inst.consecutive_failures += 1
                        if inst.consecutive_failures >= self.max_failures:
                            inst.status = "DOWN"
                            to_remove.append(s_id)
                
                for s_id in to_remove:
                    del self.services[s_id]

async def main():
    print("Iniciando protótipo de Service Discovery...")
    registry = ServiceRegistry(heartbeat_interval=0.2, max_failures=3)
    await registry.start()

    # 1. Registrar serviço
    s_id = "payment-v1"
    await registry.register(s_id, "payment-service", "127.0.0.1", 8080)
    
    nodes = await registry.discover("payment-service")
    print(f" Nós descobertos logo após registro: {len(nodes)} (Esperado: 1)")
    assert len(nodes) == 1

    # 2. Simular envio de heartbeats por um tempo
    for _ in range(3):
        await asyncio.sleep(0.1)
        await registry.heartbeat(s_id)

    nodes_active = await registry.discover("payment-service")
    print(f" Nó ativo após heartbeats contínuos: {len(nodes_active)} (Esperado: 1)")
    assert len(nodes_active) == 1

    # 3. Simular falha de heartbeats (parar de enviar por tempo suficiente para 3 falhas)
    # 0.2s * 3 = 0.6s + margem
    print("Aguardando falha de heartbeats (sem renovar)...")
    await asyncio.sleep(0.8)

    nodes_dead = await registry.discover("payment-service")
    print(f" Nós ativos após falha de 3 heartbeats: {len(nodes_dead)} (Esperado: 0)")
    assert len(nodes_dead) == 0

    # 4. Teste de Carga e Latência (100 req/s simuladas)
    print("\nExecutando teste de carga (100 requisições)...")
    # Registrar novo nó para consulta
    load_s_id = "auth-v1"
    await registry.register(load_s_id, "auth-service", "127.0.0.1", 9090)

    latencies = []
    requests_count = 100
    start_test = time.time()

    for i in range(requests_count):
        t0 = time.time()
        await registry.discover("auth-service")
        t1 = time.time()
        latencies.append((t1 - t0) * 1000) # em milissegundos
        # Controle simples para aproximar a taxa de 100 req/s se necessário, 
        # mas aqui medimos a capacidade pura e a latência sob alta concorrência

    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18] # Aprox 95 percentil

    print(f" Latência Média: {avg_latency:.4f} ms (Critério: < 20ms)")
    print(f" Latência P95:   {p95_latency:.4f} ms (Critério: < 50ms)")
    
    assert avg_latency < 20.0, f"Latência média muito alta: {avg_latency}ms"
    assert p95_latency < 50.0, f"Latência P95 muito alta: {p95_latency}ms"

    await registry.stop()
    print("\n Experimento executado com sucesso e todos os asserts passaram!")

if __name__ == "__main__":
    asyncio.run(main())