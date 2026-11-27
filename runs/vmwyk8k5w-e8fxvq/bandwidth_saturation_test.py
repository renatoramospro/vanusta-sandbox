import time
import heapq
import statistics

class NetworkPacket:
    def __init__(self, packet_id, priority, send_time):
        self.packet_id = packet_id
        self.priority = priority  # 0 para crítico, 1 para normal
        self.send_time = send_time

    def __lt__(self, other):
        return self.priority < other.priority

class SaturatedNetworkSimulator:
    def __init__(self, link_capacity_pps=1000):
        self.queue = []
        self.link_capacity_pps = link_capacity_pps
        self.transmission_delay = 1.0 / link_capacity_pps
        self.dropped_packets = 0

    def enqueue(self, packet):
        # Controle de Admissão / Proteção contra saturação extrema para pacotes normais
        # Se a fila estiver muito cheia, descartamos tráfego non-critical para preservar o crítico
        if len(self.queue) > self.link_capacity_pps * 0.5 and packet.priority == 1:
            self.dropped_packets += 1
            return
        heapq.heappush(self.queue, packet)

    def run_simulation(self):
        received_packets = []
        start_time = time.time()
        
        while self.queue:
            packet = heapq.heappop(self.queue)
            # Simulação determinística do tempo de transmissão sob capacidade finita
            receive_time = start_time + self.transmission_delay * (len(received_packets) + 1)
            latency = (receive_time - packet.send_time) * 1000  # ms
            
            received_packets.append({
                "id": packet.packet_id,
                "priority": packet.priority,
                "latency": latency
            })
            
        return received_packets, self.dropped_packets

def test_bandwidth_saturation_scenario():
    # Cenário Adversarial: Demanda total de 2000 pps, mas enlace suporta apenas 1000 pps
    simulator = SaturatedNetworkSimulator(link_capacity_pps=1000)
    total_packets = 2000
    
    send_time = time.time()
    for i in range(total_packets):
        # 50% crítico (1000 pps), 50% normal (1000 pps) -> Demanda total excede a capacidade do enlace (1000 pps)
        priority = 0 if i % 2 == 0 else 1
        pkt = NetworkPacket(packet_id=i, priority=priority, send_time=send_time)
        simulator.enqueue(pkt)
        
    received, dropped = simulator.run_simulation()
    
    # Filtra latências apenas dos pacotes críticos que conseguiram passar
    critical_latencies = [p["latency"] for p in received if p["priority"] == 0]
    
    if critical_latencies:
        critical_latencies.sort()
        p99_index = int(len(critical_latencies) * 0.99)
        p99_latency = critical_latencies[p99_index]
    else:
        p99_latency = 0.0

    print(f"Pacotes críticos processados: {len(critical_latencies)}")
    print(f"Pacotes normais descartados por controle de saturação: {dropped}")
    print(f"P99 Latência Crítica sob Saturação: {p99_latency:.4f} ms")
    
    # O critério de sucesso exige P99 < 5ms para pacotes críticos mesmo sob contenção/saturação
    assert p99_latency < 5.0, f"Falha: P99 crítico ({p99_latency}ms) excedeu o limite de 5ms sob saturação."
    print("Sucesso: Módulo manteve latência determinística (P99 < 5ms) para pacotes críticos através de controle de saturação.")

if __name__ == "__main__":
    test_bandwidth_saturation_scenario()