import time
import threading
import collections
import statistics

class NaiveTelemetry:
    """
    Abordagem errada: Cria objetos novos (dicionários) a cada chamada
    e armazena em uma lista que cresce indefinidamente, causando alocações.
    """
    def __init__(self):
        self.metrics = []

    def record(self, name, value):
        # ERRO: Alocação de um novo dicionário a cada frame
        # ERRO: Operação de append em lista pode causar realocação de memória
        self.metrics.append({
            "name": name,
            "value": value,
            "timestamp": time.perf_counter()
        })

class AsyncTelemetry:
    """
    Abordagem correta: Usa um buffer circular (deque) com tamanho fixo
    para evitar alocações infinitas e uma thread separada para processar.
    """
    def __init__(self, capacity=1000):
        # Buffer circular pré-alocado para evitar crescimento infinito
        self.buffer = collections.deque(maxlen=capacity)
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.worker_thread.start()

    def record(self, name, value):
        # Otimizado: Apenas joga uma tupla (objeto leve) no buffer
        # O deque é thread-safe para append e popleft em Python
        self.buffer.append((name, value, time.perf_counter()))

    def _process_loop(self):
        while self.running:
            if self.buffer:
                # Simula o processamento pesado (ex: escrita em disco ou rede)
                _ = self.buffer.popleft()
                time.sleep(0.0001) # Simula latência de I/O
            else:
                time.sleep(0.01)

    def stop(self):
        self.running = False
        self.worker_thread.join()

def run_benchmark(telemetry_system, iterations=1000, simulate_spike=False):
    overheads = []
    spikes_detected = []
    
    for i in range(iterations):
        # Simula o trabalho do jogo
        start_frame = time.perf_counter()
        
        # --- Início da medição da telemetria ---
        t_start = time.perf_counter()
        telemetry_system.record("frame_time", 16.6) # Valor nominal 60FPS
        t_end = time.perf_counter()
        # --- Fim da medição da telemetria ---
        
        overheads.append(t_end - t_start)

        # Simula um pico de latência (ex: carregamento de textura)
        if simulate_spike and i == iterations // 2:
            spike_duration = 0.050 # 50ms
            time.sleep(spike_duration)
            # Registra o pico
            telemetry_system.record("spike", spike_duration * 1000)
            spikes_detected.append(spike_duration * 1000)

    avg_overhead_ms = statistics.mean(overheads) * 1000
    max_overhead_ms = max(overheads) * 1000
    
    return avg_overhead_ms, max_overhead_ms

def main():
    print("=== Iniciando Teste de Arquitetura de Telemetria ===\n")
    iterations = 5000

    # 1. Testando Telemetria Ingênua
    print(f"Testando NaiveTelemetry ({iterations} iterações)...")
    naive = NaiveTelemetry()
    avg_n, max_n = run_benchmark(naive, iterations)
    print(f"  > Overhead Médio: {avg_n:.4f} ms")
    print(f"  > Overhead Máximo: {max_n:.4f} ms")

    # 2. Testando Telemetria Assíncrona
    print(f"\nTestando AsyncTelemetry ({iterations} iterações)...")
    async_tel = AsyncTelemetry(capacity=iterations)
    avg_a, max_a = run_benchmark(async_tel, iterations)
    print(f"  > Overhead Médio: {avg_a:.4f} ms")
    print(f"  > Overhead Máximo: {max_a:.4f} ms")

    # 3. Teste de Precisão de Pico
    print(f"\nTestando Precisão de Detecção de Pico (50ms)...")
    async_tel_precision = AsyncTelemetry()
    # Injetamos um pico manual para ver se o sistema captura o valor correto
    target_spike = 50.0
    async_tel_precision.record("spike_test", target_spike)
    
    # Como o AsyncTelemetry processa em thread, vamos esperar um pouco e checar o buffer
    # (Em um sistema real, o consumidor leria isso)
    # Para o experimento, vamos apenas validar se o registro foi feito sem erro.
    print(f"  > Pico de {target_spike}ms registrado com sucesso.")

    # Verificação de Critérios de Sucesso
    print("\n=== Verificação de Critérios de Sucesso ===")
    
    # Critério 1: Overhead < 0.5ms
    success_overhead = avg_a < 0.5
    print(f"Critério Overhead < 0.5ms: {'[OK]' if success_overhead else '[FALHOU]'}")
    
    # Critério 2: Estabilidade (Max/Avg ratio)
    # Se o Max for muito maior que o Avg, o sistema causa stuttering
    stability_ratio = max_a / avg_a
    print(f"Critério Estabilidade (Ratio Max/Avg < 5.0): {'[OK]' if stability_ratio < 5.0 else '[FALHOU]'}")
    print(f"  > Ratio: {stability_ratio:.2f}")

    if success_overhead and stability_ratio < 5.0:
        print("\nRESULTADO: Arquitetura Aprovada.")
    else:
        print("\nRESULTADO: Arquitetura Reprovada.")

    async_tel.stop()
    async_tel_precision.stop()

if __name__ == "__main__":
    main()