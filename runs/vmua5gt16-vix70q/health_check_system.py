import time
import threading
import concurrent.futures
from enum import Enum
from typing import List, Dict, Any

class HealthStatus(Enum):
    OK = "OK"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"

class Dependency:
    def __init__(self, name: str, critical: bool = True):
        self.name = name
        self.critical = critical
        self.is_up = True

    def check(self) -> bool:
        return self.is_up

class HealthCheckService:
    def __init__(self):
        self.dependencies: List[Dependency] = []

    def add_dependency(self, dep: Dependency):
        self.dependencies.append(dep)

    def get_liveness(self) -> Dict[str, Any]:
        """
        Liveness deve ser extremamente leve. 
        Apenas confirma que o motor de execução está respondendo.
        """
        return {"status": "UP", "timestamp": time.time()}

    def get_readiness(self) -> Dict[str, Any]:
        """
        Readiness checa dependências críticas.
        Se uma crítica falhar -> DOWN (503).
        Se uma não-crítica falhar -> DEGRADED (200).
        """
        results = []
        overall_status = HealthStatus.OK
        critical_failure = False
        
        for dep in self.dependencies:
            is_ok = dep.check()
            results.append({"name": dep.name, "status": "OK" if is_ok else "DOWN"})
            
            if not is_ok:
                if dep.critical:
                    critical_failure = True
                    overall_status = HealthStatus.DOWN
                else:
                    if overall_status != HealthStatus.DOWN:
                        overall_status = HealthStatus.DEGRADED

        if critical_failure:
            return {"status": "DOWN", "details": results, "code": 503}
        
        return {"status": overall_status.value, "details": results, "code": 200}

def run_load_test(service: HealthCheckService, iterations: int = 100):
    """Simula carga para validar a latência < 50ms."""
    latencies = []
    
    def single_request():
        start = time.perf_counter()
        # Simulando chamada ao endpoint de readiness
        res = service.get_readiness()
        end = time.perf_counter()
        latencies.append((end - start) * 1000) # ms
        return res

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(single_request) for _ in range(iterations)]
        concurrent.futures.wait(futures)

    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    return avg_latency, max_latency

def main():
    print("=== Iniciando Testes de Subsistema de Health Check ===\n")
    
    # 1. Setup
    hc = HealthCheckService()
    db = Dependency("PostgreSQL", critical=True)
    cache = Dependency("Redis", critical=True)
    logger_svc = Dependency("CloudWatch-Logs", critical=False)
    
    hc.add_dependency(db)
    hc.add_dependency(cache)
    hc.add_dependency(logger_svc)

    # --- CENÁRIO 1: Operação Normal ---
    print("[Cenário 1] Operação Normal (Tudo OK)")
    readiness = hc.get_readiness()
    assert readiness["code"] == 200
    assert readiness["status"] == "OK"
    print(f"  Resultado: {readiness['status']} (Status Code: {readiness['code']})")

    # --- CENÁRIO 2: Falha de Dependência Não-Crítica (Degraded) ---
    print("\n[Cenário 2] Falha de Dependência Não-Crítica (CloudWatch Down)")
    logger_svc.is_up = False
    readiness = hc.get_readiness()
    assert readiness["code"] == 200
    assert readiness["status"] == "DEGRADED"
    print(f"  Resultado: {readiness['status']} (Status Code: {readiness['code']}) - O tráfego CONTINUA.")

    # --- CENÁRIO 3: Falha de Dependência Crítica (Readiness Down) ---
    print("\n[Cenário 3] Falha de Dependência Crítica (DB Down)")
    db.is_up = False
    readiness = hc.get_readiness()
    assert readiness["code"] == 503
    assert readiness["status"] == "DOWN"
    print(f"  Resultado: {readiness['status']} (Status Code: {readiness['code']}) - O tráfego é REMOVIDO.")
    
    # Verificação crucial: Liveness deve continuar OK mesmo com DB Down
    liveness = hc.get_liveness()
    assert liveness["status"] == "UP"
    print(f"  Liveness Check: {liveness['status']} (O processo não foi morto!)")

    # --- CENÁRIO 4: Teste de Carga e Latência ---
    print("\n[Cenário 4] Teste de Carga (100 requisições simultâneas)")
    avg_lat, max_lat = run_load_test(hc, 100)
    print(f"  Latência Média: {avg_lat:.4f}ms")
    print(f"  Latência Máxima: {max_lat:.4f}ms")
    
    if avg_lat < 50:
        print("  ✅ SUCESSO: Latência dentro do limite de 50ms.")
    else:
        print("  ❌ FALHA: Latência acima do limite.")
        exit(1)

    # --- CENÁRIO 5: O Erro do Arquiteto (Demonstração do Death Spiral) ---
    # Se o Liveness checasse o DB, ele retornaria DOWN quando o DB caísse.
    print("\n[Cenário 5] Demonstração de Erro de Design (Death Spiral)")
    print("  Se o Liveness incluísse o DB, o status seria DOWN ao falhar o DB...")
    # Simulando lógica errada:
    erroneous_liveness_status = "DOWN" if not db.is_up else "UP"
    if erroneous_liveness_status == "DOWN":
        print("  ⚠️  ALERTA: O orquestrador reiniciaria o container agora!")
        print("  ⚠️  Isso causaria um loop de reinicialização sem fim enquanto o DB estivesse fora.")
    
    print("\n=== Testes Concluídos com Sucesso ===")

if __name__ == "__main__":
    main()