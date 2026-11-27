imports = """
import asyncio
import time
import os
import statistics
"""

import asyncio
import time
import os
import statistics

async def simulate_cloud_disk_io(file_path: str, data: str):
    """
    Simula uma operação de disco assíncrona (ex: escrita em SSD/EBS na nuvem).
    Utilizamos run_in_executor para evitar o bloqueio da thread principal do event loop
    caso a biblioteca de disco seja síncrona, ou usamos I/O não bloqueante.
    """
    start_time = time.perf_counter()
    # Simulando latência de I/O de disco em nuvem (ex: 5ms a 15ms)
    await asyncio.sleep(0.010) 
    
    # Escrita real simulada em arquivo temporário para teste reprodutível
    def write_file():
        with open(file_path, "w") as f:
            f.write(data)
            
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, write_file)
    
    elapsed = (time.perf_counter() - start_time) * 1000 # em milissegundos
    return elapsed

async def simulate_cloud_network_io():
    """
    Simula uma chamada de rede assíncrona (ex: requisição HTTP para S3 ou microsserviço).
    """
    start_time = time.perf_counter()
    # Simulando latência de rede em nuvem (ex: 10ms a 30ms)
    await asyncio.sleep(0.020)
    elapsed = (time.perf_counter() - start_time) * 1000
    return elapsed

async def handle_request(req_id: int, temp_dir: str):
    """
    Processa uma requisição combinando I/O de rede e de disco de forma totalmente assíncrona.
    """
    req_start = time.perf_counter()
    
    file_path = os.path.join(temp_dir, f"req_{req_id}.txt")
    
    # Executa I/O de rede e de disco concorrentemente para a mesma requisição
    disk_task = simulate_cloud_disk_io(file_path, f"Dados da requisicao {req_id}")
    network_task = simulate_cloud_network_io()
    
    disk_latency, net_latency = await asyncio.gather(disk_task, network_task)
    
    total_req_latency = (time.perf_counter() - req_start) * 1000
    return {
        "req_id": req_id,
        "total_latency": total_req_latency,
        "disk_latency": disk_latency,
        "net_latency": net_latency
    }

async def main():
    total_requests = 100
    temp_dir = "./temp_test_io"
    os.makedirs(temp_dir, exist_ok=True)
    
    print(f"Iniciando processamento assíncrono de {total_requests} requisições simultâneas (Rede + Disco)...")
    
    start_total = time.perf_counter()
    
    # Dispara 100 requisições simultâneas via asyncio.gather
    tasks = [handle_request(i, temp_dir) for i in range(total_requests)]
    results = await asyncio.gather(*tasks)
    
    total_duration = (time.perf_counter() - start_total) * 1000
    
    # Coleta de métricas de latência
    latencies = [r["total_latency"] for r in results]
    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18] # Percentil 95 aproximado
    
    print(f"\n--- RELATÓRIO DE DESEMPENHO ---")
    print(f"Total de Requisições: {total_requests}")
    print(f"Tempo total de execução concorrente: {total_duration:.2f} ms")
    print(f"Latência Média por Requisição: {avg_latency:.2f} ms")
    print(f"Latência Percentil 95 (P95): {p95_latency:.2f} ms")
    
    # Validação do critério de sucesso
    assert avg_latency < 50.0, f"Falha: Latência média ({avg_latency:.2f}ms) acima do limite de 50ms!"
    print("\n[SUCESSO] Critério de sucesso atingido: Latência média inferior a 50ms sem bloqueio de thread principal!")
    
    # Limpeza
    for i in range(total_requests):
        f_path = os.path.join(temp_dir, f"req_{i}.txt")
        if os.path.exists(f_path):
            os.remove(f_path)
    os.rmdir(temp_dir)

if __name__ == "__main__":
    asyncio.run(main())