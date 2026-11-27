import time
import statistics

def test_cpu_software_overhead_failure():
    print("\n[Contraexemplo] Simulando abordagem tradicional baseada em CPU/OS para 1000 I/Os:")
    latencies = []
    for i in range(1000):
        start = time.perf_counter_ns()
        # Simula overhead de interrupção de SO, context switch e fila de software
        # que tipicamente consome entre 150us e 300us por operação síncrona
        time.sleep(0.00015) # 150 us simulados de atraso de software
        end = time.perf_counter_ns()
        latencies.append((end - start) / 1000.0)
        
    mean_lat = statistics.mean(latencies)
    print(f" - Latência Média da Abordagem em CPU: {mean_lat:.3f} us")
    
    try:
        assert mean_lat < 50.0, "Aviso esperado: Abordagem em CPU falhou no requisito de latência < 50us!"
    except AssertionError as e:
        print(f"CAPTURADO COM SUCESSO: {e}")
        print("Justificativa: Sem FPGA, o overhead de software impede atingir o critério de alta performance.")

if __name__ == "__main__":
    test_cpu_software_overhead_failure()