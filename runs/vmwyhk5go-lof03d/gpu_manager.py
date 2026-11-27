import time
import threading
import random
import statistics
from dataclasses import dataclass
from typing import List

@dataclass
class InferenceTask:
    task_id: int
    model_type: str  # ex: 'BERT' ou 'ResNet'
    memory_required_mb: float
    compute_cost_s: float

@dataclass
class TaskResult:
    task_id: int
    latency: float
    success: bool
    error_msg: str = ""

class GPUMonitor:
    def __init__(self, total_vram_mb: float):
        self.total_vram_mb = total_vram_mb
        self.used_vram_mb = 0.0
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.utilization_history: List[float] = []

    def allocate(self, amount_mb: float, timeout: float = 5.0) -> bool:
        """Aguarda (backpressure) até que haja VRAM suficiente disponível ou ocorra timeout."""
        start_time = time.time()
        with self.condition:
            while self.used_vram_mb + amount_mb > self.total_vram_mb:
                elapsed = time.time() - start_time
                remaining = timeout - elapsed
                if remaining <= 0:
                    return False  # Timeout na espera por recursos
                self.condition.wait(timeout=remaining)
            
            # Aloca efetivamente
            self.used_vram_mb += amount_mb
            return True

    def release(self, amount_mb: float):
        with self.condition:
            self.used_vram_mb = max(0.0, self.used_vram_mb - amount_mb)
            self.condition.notify_all()  # Acorda threads em espera

    def record_utilization(self):
        with self.lock:
            util = (self.used_vram_mb / self.total_vram_mb) * 100.0
            self.utilization_history.append(util)

    def get_average_utilization(self) -> float:
        with self.lock:
            if not self.utilization_history:
                return 0.0
            return statistics.mean(self.utilization_history)

class GPUInferenceManager:
    def __init__(self, total_vram_mb: float, max_concurrent_streams: int):
        self.monitor = GPUMonitor(total_vram_mb)
        self.stream_semaphore = threading.Semaphore(max_concurrent_streams)
        self.results: List[TaskResult] = []
        self.results_lock = threading.Lock()

    def execute_task(self, task: InferenceTask):
        start_time = time.time()
        
        # 1. Tenta alocar VRAM com backpressure (fila de espera)
        allocated = self.monitor.allocate(task.memory_required_mb, timeout=3.0)
        if not allocated:
            with self.results_lock:
                self.results.append(TaskResult(task.task_id, time.time() - start_time, False, "OOM / Timeout de VRAM"))
            return

        # 2. Controla concorrência por Streams CUDA simulados
        with self.stream_semaphore:
            try:
                # Amostragem contínua de utilização durante a execução
                steps = max(1, int(task.compute_cost_s / 0.05))
                for _ in range(steps):
                    time.sleep(task.compute_cost_s / steps)
                    self.monitor.record_utilization()
                
                latency = time.time() - start_time
                with self.results_lock:
                    self.results.append(TaskResult(task.task_id, latency, True))
            finally:
                self.monitor.release(task.memory_required_mb)

    def run_workload(self, tasks: List[InferenceTask]):
        threads = []
        for task in tasks:
            t = threading.Thread(target=self.execute_task, args=(task,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()

if __name__ == "__main__":
    print("Iniciando simulação com Fila de Espera (Backpressure) em Gerenciamento de GPU...")
    
    # Simulação de GPU com 4096 MB de VRAM e 3 streams simultâneos
    manager = GPUInferenceManager(total_vram_mb=4096.0, max_concurrent_streams=3)

    # Carga simulada de 15 processos concorrentes com diferentes demandas
    simulated_tasks = [
        InferenceTask(task_id=i, model_type="BERT" if i % 2 == 0 else "ResNet",
                      memory_required_mb=random.choice([1000.0, 1500.0, 2000.0]),
                      compute_cost_s=random.uniform(0.1, 0.25))
        for i in range(15)
    ]

    start_total = time.time()
    manager.run_workload(simulated_tasks)
    total_time = time.time() - start_total

    latencies = [r.latency for r in manager.results if r.success]
    failures = [r for r in manager.results if not r.success]
    avg_util = manager.monitor.get_average_utilization()
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)

    print(f"\n--- RELATÓRIO DE DESEMPENHO DO MÓDULO (COM BACKPRESSURE) ---")
    print(f"Total de Tarefas: {len(simulated_tasks)}")
    print(f"Tarefas com Sucesso: {len(latencies)}")
    print(f"Tarefas com Falha (OOM/Erro): {len(failures)}")
    print(f"Utilização Média da GPU: {avg_util:.2f}%")
    print(f"Latência Média: {statistics.mean(latencies):.4f}s")
    print(f"Latência P95: {p95_latency:.4f}s")
    print(f"Tempo Total de Execução: {total_time:.4f}s")

    # Validação rigorosa do critério de sucesso (> 85% de utilização média com fila de espera)
    assert len(failures) == 0, fEsperado 0 falhas com backpressure, obtido {len(failures)}."
    assert avg_util >= 85.0, f"Utilização média da GPU ({avg_util:.2f}%) ficou abaixo do critério de 85%."
    print("\n[SUCESSO] O módulo com fila de espera gerenciou a VRAM eficientemente e atingiu o critério de sucesso.")