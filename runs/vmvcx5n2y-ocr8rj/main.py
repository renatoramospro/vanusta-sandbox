import time
import threading
import queue
import os
import json
from datetime import datetime

# Simulação do Repositório Central de Logs com Durabilidade (Append-only)
class CentralLogRepository:
    def __init__(self, storage_file="central_logs.jsonl"):
        self.storage_file = storage_file
        self.lock = threading.Lock()
        # Limpa arquivo anterior para o teste
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def ingest(self, log_entry):
        # Simula escrita durável em disco (Write-Ahead Log / Append)
        line = json.dumps(log_entry) + "\n"
        with self.lock:
            with open(self.storage_file, "a", encoding="utf-8") as f:
                f.write(line)

    def query(self, level=None, limit=100):
        start_time = time.time()
        results = []
        with self.lock:
            if not os.path.exists(self.storage_file):
                return [], 0.0
            with open(self.storage_file, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if level is None or entry["level"] == level:
                        results.append(entry)
                        if len(results) >= limit:
                            break
        latency_ms = (time.time() - start_time) * 1000
        return results, latency_ms

# Simulação de um Servidor Gerador de Logs
class LogServer(threading.Thread):
    def __init__(self, server_id, repository, total_logs=50):
        super().__init__()
        self.server_id = server_id
        self.repository = repository
        self.total_logs = total_logs
        self.levels = ["INFO", "WARN", "ERROR"]

    def run(self):
        for i in range(self.total_logs):
            log = {
                "timestamp": datetime.utcnow().isoformat(),
                "server_id": f"server-{self.server_id:02d}",
                "level": self.levels[i % len(self.levels)],
                "message": f"Log message {i} from server {self.server_id}"
            }
            self.repository.ingest(log)

def run_simulation():
    print("Iniciando simulação de sistema de logs distribuído (10 servidores)...")
    repository = CentralLogRepository()
    
    # 1. Inicia 10 servidores concorrentes enviando logs
    servers = [LogServer(i, repository, total_logs=50) for i in range(10)]
    
    start_time = time.time()
    for s in servers:
        s.start()
    for s in servers:
        s.join()
    ingestion_time = time.time() - start_time
    
    total_expected = 10 * 50
    print(f"Ingestão concluída: {total_expected} logs coletados em {ingestion_time:.4f}s.")

    # 2. Realiza consultas e mede a latência em tempo real
    latencies = []
    for _ in range(20):
        results, latency = repository.query(level="ERROR", limit=10)
        latencies.append(latency)

    avg_latency = sum(latencies) / len(latencies)
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

    print(f"Total de registros de ERROR encontrados por consulta: {len(results)}")
    print(f"Latência Média de Consulta: {avg_latency:.2f} ms")
    print(f"Latência P95 de Consulta: {p95_latency:.2f} ms")

    # Validação do Critério de Sucesso
    assert avg_latency < 500, f"Latência média alta: {avg_latency}ms (esperado < 500ms)"
    assert p95_latency < 500, f"Latência P95 alta: {p95_latency}ms (esperado < 500ms)"
    print("\n[Sucesso] O sistema atendeu aos requisitos de latência e agregação distribuída!")

if __name__ == "__main__":
    run_simulation()