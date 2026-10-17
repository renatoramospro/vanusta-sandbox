import time
import sys
import psutil

class SystemMonitor:
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        # Inicializa as contagens de I/O para cálculo de delta, se necessário
        self.last_net = psutil.net_io_counters()
        self.last_disk = psutil.disk_io_counters()

    def collect_metrics(self) -> dict:
        start_time = time.time()

        # 1. CPU: psutil.cpu_percent com intervalo=None usa o delta interno desde a última chamada
        cpu_usage = psutil.cpu_percent(interval=None)

        # 2. Memória
        mem = psutil.virtual_memory()
        memory_usage = {
            "total": mem.total,
            "available": mem.available,
            "percent": mem.percent,
            "used": mem.used
        }

        # 3. I/O de Rede (bytes enviados e recebidos desde o boot ou delta)
        net = psutil.net_io_counters()
        net_io = {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv
        }

        # 4. I/O de Disco
        disk = psutil.disk_io_counters()
        disk_io = {
            "read_bytes": disk.read_bytes if disk else 0,
            "write_bytes": disk.write_bytes if disk else 0
        }

        latency = time.time() - start_time

        return {
            "timestamp": time.time(),
            "cpu_percent": cpu_usage,
            "memory": memory_usage,
            "net_io": net_io,
            "disk_io": disk_io,
            "collection_latency_seconds": latency
        }

def test_monitor_execution():
    print("Iniciando teste do Sistema de Monitoramento...")
    monitor = SystemMonitor()
    
    # Executa uma leitura inicial para calibrar a CPU
    psutil.cpu_percent(interval=None)
    time.sleep(0.5)

    # Coleta 3 amostras para validação
    for i in range(3):
        metrics = monitor.collect_metrics()
        print(f"[{i+1}] Amostra coletada:")
        print(f"    - CPU: {metrics['cpu_percent']}%")
        print(f"    - Memória Usada: {metrics['memory']['percent']}%")
        print(f"    - Latência de Coleta: {metrics['collection_latency_seconds']:.6f}s")
        
        # Validação do critério de sucesso: latência de coleta deve ser estritamente < 1s
        assert metrics['collection_latency_seconds'] < 1.0, "Latência excedeu o limite de 1 segundo!"
        time.sleep(0.5)

    print("Sucesso: Todas as métricas foram coletadas dentro da latência esperada!")

if __name__ == "__main__":
    try:
        test_monitor_execution()
    except Exception as e:
        print(f"Erro no experimento: {e}")
        sys.exit(1)