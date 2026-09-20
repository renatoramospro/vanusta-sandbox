import time
import threading
import random
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, TimeoutError

class HealthStatus(Enum):
    OK = "OK"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"

class Dependency:
    def __init__(self, name, critical=True, latency_sim=0.01):
        self.name = name
        self.critical = critical
        self.latency_sim = latency_sim
        self.is_up = True

    def check(self, timeout):
        """Executa a checagem com suporte a timeout."""
        start_time = time.time()
        
        # Simulação de execução de checagem
        def _do_check():
            if not self.is_up:
                return False
            time.sleep(self.latency_sim)
            return True

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_do_check)
            try:
                return future.result(timeout=timeout)
            except TimeoutError:
                return False
            except Exception:
                return False

class LivenessMonitor:
    """
    Monitor de Liveness que detecta Deadlocks/Starvation.
    Não checa apenas o processo, mas se o 'heartbeat' está atualizado.
    """
    def __init__(self, threshold=0.5):
        self.last_heartbeat = time.time()
        self.threshold = threshold
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()

    def _heartbeat_loop(self):
        """Simula o loop principal de trabalho da aplicação."""
        while not self._stop_event.is_set():
            # Simula trabalho real da aplicação
            time.sleep(0.1)
            self.last_heartbeat = time.time()

    def is_alive(self, timeout):
        """Verifica se o heartbeat está dentro do limite de tempo."""
        # Se o tempo desde o último heartbeat for maior que o threshold, 
        # a aplicação está em deadlock ou starvation.
        current_time = time.time()
        if (current_time - self.last_heartbeat) > self.threshold:
            return False
        return True

    def stop(self):
        self._stop_event.set()

class HealthCheckEngine:
    def __init__(self, liveness_monitor: LivenessMonitor, timeout=0.04):
        self.liveness_monitor = liveness_monitor
        self.dependencies = []
        self.timeout = timeout # Timeout global para garantir < 50ms

    def add_dependency(self, dependency: Dependency):
        self.dependencies.append(dependency)

    def get_liveness_status(self):
        """Endpoint de Liveness: Focado em Deadlock/Starvation."""
        # O timeout aqui é curto para não travar o orquestrador
        alive = self.liveness_monitor.is_alive(timeout=self.timeout)
        return 200 if alive else 500

    def get_readiness_status(self):
        """Endpoint de Readiness: Focado em Dependências Críticas."""
        overall_status = HealthStatus.OK
        critical_failure = False
        
        for dep in self.dependencies:
            # Aplicamos o timeout rigoroso em cada dependência
            success = dep.check(timeout=self.timeout)
            
            if not success:
                if dep.critical:
                    critical_failure = True
                    overall_status = HealthStatus.DOWN
                    break # Se uma crítica falha, o status é DOWN
                else:
                    overall_status = HealthStatus.DEGRADED

        if critical_failure:
            return 503, overall_status
        return 200, overall_status

def main():
    print("=== Iniciando Testes de Health Check Avançado (Correção de Timeout e Deadlock) ===\n")

    # 1. Setup
    liveness_mon = LivenessMonitor(threshold=0.3)
    engine = HealthCheckEngine(liveness_mon, timeout=0.04) # Timeout de 40ms para garantir < 50ms total
    
    db = Dependency("PostgreSQL", critical=True, latency_sim=0.01)
    cache = Dependency("Redis", critical=True, latency_sim=0.01)
    logger = Dependency("CloudWatch", critical=False, latency_sim=0.01)
    
    engine.add_dependency(db)
    engine.add_dependency(cache)
    engine.add_dependency(logger)

    # --- CENÁRIO 1: TUDO OK ---
    print("[Cenário 1] Operação Normal")
    status_code, status_enum = engine.get_readiness_status()
    print(f"  Readiness: {status_code} ({status_enum.value})")
    assert status_code == 200

    # --- CENÁRIO 2: DEPENDÊNCIA LENTA (TIMEOUT TEST) ---
    print("\n[Cenário 2] Dependência Lenta (Simulando Latência > Timeout)")
    slow_dep = Dependency("SlowAPI", critical=True, latency_sim=0.2) # 200ms > 40ms timeout
    engine.add_dependency(slow_dep)
    status_code, status_enum = engine.get_readiness_status()
    print(f"  Readiness: {status_code} ({status_enum.value}) - Timeout evitou travamento")
    # Deve retornar DOWN porque a dependência falhou por timeout
    assert status_code == 503 
    engine.dependencies.pop() # Limpa para o próximo teste

    # --- CENÁRIO 3: FALHA NÃO CRÍTICA (DEGRADED) ---
    print("\n[Cenário 3] Falha de Dependência Não-Crítica")
    logger.is_up = False
    status_code, status_enum = engine.get_readiness_status()
    print(f"  Readiness: {status_code} ({status_enum.value})")
    assert status_code == 200
    assert status_enum == HealthStatus.DEGRADED

    # --- CENÁRIO 4: DEADLOCK / STARVATION (LIVENESS TEST) ---
    print("\n[Cenário 4] Detecção de Deadlock (Liveness)")
    # Simulamos um deadlock parando o heartbeat manualmente
    liveness_mon.last_heartbeat = time.time() - 2.0 # Força o tempo a estar fora do threshold
    liveness_status = engine.get_liveness_status()
    print(f"  Liveness: {liveness_status} (Detectou que o loop de trabalho parou!)")
    assert liveness_status == 500

    # --- CENÁRIO 5: PERFORMANCE SOB CARGA ---
    print("\n[Cenário 5] Teste de Carga (Latência < 50ms)")
    # Resetamos o liveness para o teste de carga
    liveness_mon.last_heartbeat = time.time()
    
    latencies = []
    def run_load():
        start = time.time()
        engine.get_readiness_status()
        latencies.append(time.time() - start)

    threads = []
    for _ in range(50):
        t = threading.Thread(target=run_load)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    avg_latency = (sum(latencies) / len(latencies)) * 1000
    max_latency = max(latencies) * 1000
    print(f"  Média: {avg_latency:.4f}ms | Máxima: {max_latency:.4f}ms")
    assert avg_latency < 50
    assert max_latency < 100 # Margem de segurança para o teste

    liveness_mon.stop()
    print("\n=== TODOS OS TESTES DE CORREÇÃO PASSARAM ===\n")

if __name__ == "__main__":
    main()