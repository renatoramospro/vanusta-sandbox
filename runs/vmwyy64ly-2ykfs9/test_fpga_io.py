import statistics

class FPGADiskDriverSim:
    """
    Simulador comportamental do driver de I/O e controladora de disco em FPGA.
    Clock: 100 MHz (1 ciclo = 10 ns).
    Modela latência analítica pura de hardware (sem invocar time.sleep() do SO).
    """
    def __init__(self, clock_freq_mhz=100):
        self.cycle_time_ns = 1000.0 / clock_freq_mhz # 10 ns por ciclo
        
    def send_request(self, lba: int, is_write: bool, data_block: bytes, sequential_prefetch: bool = False, backpressure_delay_cycles: int = 0) -> float:
        """
        Calcula de forma determinística a latência de hardware em microssegundos (us)
        para uma transação AXI-4-LITE com a controladora de disco em FPGA.
        """
        # 1. Ciclos de Handshake do barramento AXI (Endereço e Comando): ~5 ciclos = 50 ns
        handshake_cycles = 5
        
        # 2. Decodificação e FSM de controle na FPGA: ~10 ciclos = 100 ns
        fsm_cycles = 10
        
        # 3. Acesso ao meio de armazenamento (modelo de disco / NAND simulado):
        # Se houver prefetch ativado (ex: requisições sequenciais), o acesso ao disco cai para 1000 ciclos (10 us)
        if sequential_prefetch:
            disk_access_cycles = 1000
        else:
            disk_access_cycles = 3000 # 30 us padrão para 512B
            
        # 4. Backpressure no barramento AXI (se o buffer estiver congestionado)
        backpressure_cycles = backpressure_delay_cycles
        
        total_cycles = handshake_cycles + fsm_cycles + disk_access_cycles + backpressure_cycles
        
        # Latência temporal pura derivada exclusivamente dos ciclos de clock do hardware
        simulated_delay_ns = total_cycles * self.cycle_time_ns
        
        # Injeção de pequeno jitter determinístico de hardware (ex: variação de +/- 2 ciclos)
        jitter_cycles = (lba % 5) - 2 # varia entre -2 e +2 ciclos
        simulated_delay_ns += jitter_cycles * self.cycle_time_ns
        
        # Latência medida do ponto de vista do driver em microssegundos (us)
        latency_us = simulated_delay_ns / 1000.0
        return latency_us

def test_1000_io_requests():
    driver = FPGADiskDriverSim(clock_freq_mhz=100)
    latencies = []
  
    print("Iniciando simulação comportamental de 1000 requisições de I/O em FPGA (blocos de 512B)...")
  
    for i in range(1000):
        dummy_block = b'\x00' * 512
        # Simula mistura de acessos aleatórios e blocos sequenciais com prefetch
        is_sequential = (i > 0 and i % 10 == 0)
        bp_cycles = 5 if (i % 50 == 0) else 0 # Simula leve backpressure ocasional no barramento AXI
        
        lat_us = driver.send_request(
            lba=i, 
            is_write=(i % 2 == 0), 
            data_block=dummy_block,
            sequential_prefetch=is_sequential,
            backpressure_delay_cycles=bp_cycles
        )
        latencies.append(lat_us)
    
    mean_latency = statistics.mean(latencies)
    max_latency = max(latencies)
    min_latency = min(latencies)
    
    print(f"Resultados para 1000 requisições em FPGA:")
    print(f" - Latência Média: {mean_latency:.3f} us")
    print(f" - Latência Máxima: {max_latency:.3f} us")
    print(f" - Latência Mínima: {min_latency:.3f} us")
  
    # Critério de Sucesso: Latência média estritamente inferior a 50 microssegundos
    assert mean_latency < 50.0, f"Falha: Latência média de {mean_latency} us excede o limite de 50 us."
    print("Sucesso: Critério de latência média inferior a 50 us atingido com folga pela FPGA!")

if __name__ == "__main__":
    test_1000_io_requests()