path=main.py
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
    def __init__(self, server_id, repository, total_logs=100):
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
            # Simula intervalo entre logs
            time.sleep(0.001)

def run_simulation():
    print("=== Iniciando Simulação do Sistema de Logs Distribuído ===")
    repo = CentralLogRepository()
    
    num_servers = 10
    logs_per_server = 50
    threads = []

    start_ingest = time.time()
    # Inicia 10 servidores gerando logs simultaneamente
    for s_id in range(num_servers):
        t = LogServer(server_id=s_id, repository=repo, total_logs=logs_per_server)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    
    ingest_duration = time.time() - start_ingest
    total_expected = num_servers * logs_per_server
    print(f"[Ingestão] {total_expected} logs coletados de {num_servers} servidores em {ingest_duration:.4f}s.")

    # Testando Consultas em Tempo Real e Latência
    print("\n=== Executando Testes de Consulta ===")
    latencies = []
    for _ in range(100):
        results, latency = repo.query(level="ERROR", limit=10)
        latencies.append(latency)

    avg_latency = sum(latencies) / len(latencies)
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

    print(f"Total de registros de ERROR encontrados: {len(results)}")
    print(f"Latência Média de Consulta: {avg_latency:.2f} ms")
    print(f"Latência P95 de Consulta: {p95_latency:.2f} ms")

    # Validação do Critério de Sucesso
    assert avg_latency < 500, f"Latência média alta: {avg_latency}ms (esperado < 500ms)"
    assert p95_latency < 500, f"Latência P95 alta: {p95_latency}ms (esperado < 500ms)"
    print("\n[Sucesso] O sistema atendeu aos requisitos de latência e agregação distribuída!")

if __name__ == "__main__":
    run_simulation()