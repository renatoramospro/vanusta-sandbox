import time
import random

class ContainerRuntimeSimulator:
    """Simula um container e o subsistema cgroups v2 do kernel."""
    def __init__(self, initial_cpu_limit_cores: float):
        self.cpu_limit = initial_cpu_limit_cores  # ex: 1.0 = 1 núcleo
        self.throttled_count = 0

    def update_cpu_limit(self, new_limit: float):
        # Simula a escrita em /sys/fs/cgroup/cpu.max
        self.cpu_limit = max(0.2, min(4.0, new_limit))

    def simulate_request(self, load_intensity: float) -> float:
        """Simula a latência de uma requisição com base na carga e no limite de CPU atual."""
        # Se a carga exige mais do que o container tem de CPU, ocorre throttling severo
        cpu_shortage = max(0.0, load_intensity - self.cpu_limit)
        if cpu_shortage > 0:
            self.throttled_count += 1
            # Latência aumenta drasticamente devido ao throttling do cgroup (CFS scheduler)
            base_latency = 50.0 + (cpu_shortage * 300.0)
        else:
            base_latency = 20.0 + (load_intensity * 10.0)
            
        # Adiciona ruído estocástico simulando variabilidade de rede/IO
        return base_latency + random.uniform(-2.0, 2.0)

class DynamicResourceController:
    """Módulo de monitoramento e ajuste dinâmico baseado em latência."""
    def __init__(self, runtime: ContainerRuntimeSimulator, target_latency_ms: float = 50.0):
        self.runtime = runtime
        self.target_latency = target_latency_ms
        self.latency_history = []

    def evaluate_and_adjust(self, recent_latencies: list[float]):
        avg_latency = sum(recent_latencies) / len(recent_latencies)
        self.latency_history.append(avg_latency)

        # Lógica de ajuste reativo: se a latência média ultrapassar o alvo, aumentamos o limite de CPU
        if avg_latency > self.target_latency:
            # Incremento proporcional para aliviar o gargalo do cgroup
            new_limit = self.runtime.cpu_limit + 0.3
            self.runtime.update_cpu_limit(new_limit)
        elif avg_latency < (self.target_latency * 0.7) and self.runtime.cpu_limit > 0.5:
            # Reduz conservadoramente se houver folga de recursos
            new_limit = self.runtime.cpu_limit - 0.1
            self.runtime.update_cpu_limit(new_limit)

def run_experiment():
    print("=== INICIANDO EXPERIMENTO DE CONTROLE DINÂMICO DE RECURSOS (CGROUPS v2) ===")
    
    # Inicializa o container com um limite restrito de CPU (0.8 núcleos) sob alta carga (1.5 de intensidade)
    runtime = ContainerRuntimeSimulator(initial_cpu_limit_cores=0.8)
    controller = DynamicResourceController(runtime, target_latency_ms=50.0)

    load_intensity = 1.5  # Simula carga superior a 80% de utilização de CPU

    # Fase 1: Coleta de Baseline com limite restrito (gerando alta latência por throttling)
    baseline_latencies = []
    for _ in range(30):
        lat = runtime.simulate_request(load_intensity)
        baseline_latencies.append(lat)

    baseline_avg = sum(baseline_latencies) / len(baseline_latencies)
    print(f"[Baseline] Limite Inicial de CPU: {runtime.cpu_limit:.1f} cores | Latência Média Inicial: {baseline_avg:.2f} ms")

    # Fase 2: Ativação do Loop de Controle Dinâmico
    adjusted_latencies = []
    for step in range(50):
        # Simula o recebimento de lote de requisições
        window = [runtime.simulate_request(load_intensity) for _ in range(5)]
        controller.evaluate_and_adjust(window)
        adjusted_latencies.extend(window)

    final_avg = sum(adjusted_latencies[-20:]) / 20.0
    print(f"[Ajustado] Limite Final de CPU: {runtime.cpu_limit:.1f} cores | Latência Média Final: {final_avg:.2f} ms")

    # Cálculo da redução percentual
    reduction = ((baseline_avg - final_avg) / baseline_avg) * 100.0
    print(f"Redução de latência obtida: {reduction:.2f}%")

    # Validação do critério de sucesso (>15% de redução)
    assert reduction >= 15.0, f"Falha no critério: redução foi de apenas {reduction:.2f}%"
    print("=== SUCESSO: O módulo atingiu a meta de redução de latência em mais de 15% ===")

if __name__ == "__main__":
    run_experiment()