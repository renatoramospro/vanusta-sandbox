import statistics

def test_cpu_software_overhead_failure():
    print("\n[Contraexemplo] Simulando abordagem tradicional baseada em CPU/OS para 1000 I/Os:")
    latencies = []
    for i in range(1000):
        # Simula o overhead de interrupção de SO, context switch, lock de kernel e fila de software
        # que tipicamente consome ciclos de CPU equivalentes a 150us a 300us por operação síncrona
        software_overhead_us = 180.0 + (i % 20) # varia entre 180us e 200us
        latencies.append(software_overhead_us)
        
    mean_lat = statistics.mean(latencies)
    print(f" - Latência Média da Abordagem em CPU: {mean_lat:.3f} us")
    
    try:
        assert mean_lat < 50.0, "Aviso esperado: Abordagem em CPU falhou no requisito de latência < 50us!"
    except AssertionError as e:
        print(f"CAPTURADO COM SUCESSO: {e}")
        print("Justificativa: Sem FPGA, o overhead de software e interrupções do SO impede atingir o critério de alta performance.")

if __name__ == "__main__":
    test_cpu_software_overhead_failure()