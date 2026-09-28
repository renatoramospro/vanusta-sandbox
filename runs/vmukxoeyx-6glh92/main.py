import time
import threading
from queue import Queue, Empty

# Simulação de um Banco de Dados com latência síncrona
class MockDatabase:
    def __init__(self, latency_ms=0.05):
        self.store = {}
        self.latency = latency_ms
        self.write_count = 0

    def read(self, key):
        time.sleep(self.latency)
        return self.store.get(key, None)

    def write(self, key, value):
        time.sleep(self.latency)
        self.store[key] = value
        self.write_count += 1

# 1. Read-Through Cache
class ReadThroughCache:
    def __init__(self, db, capacity=100):
        self.db = db
        self.cache = {}
        self.capacity = capacity
        self.misses = 0
        self.hits = 0

    def get(self, key):
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        
        # Cache Miss: busca no DB (Read-Through pattern)
        self.misses += 1
        value = self.db.read(key)
        if value is not None:
            if len(self.cache) >= self.capacity:
                # Remove o primeiro item arbitrário (simulação simples de política)
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            self.cache[key] = value
        return value

# 2. Write-Through Cache
class WriteThroughCache:
    def __init__(self, db):
        self.db = db
        self.cache = {}

    def set(self, key, value):
        # Atualiza cache e banco de dados simultaneamente (síncrono)
        self.cache[key] = value
        self.db.write(key, value)

    def get(self, key):
        return self.cache.get(key, None)

# 3. Write-Behind (Write-Back) Cache
class WriteBehindCache:
    def __init__(self, db, batch_interval=0.01):
        self.db = db
        self.cache = {}
        self.queue = Queue()
        self.running = True
        self.worker_thread = threading.Thread(target=self._async_writer, daemon=True)
        self.worker_thread.start()

    def _async_writer(self):
        while self.running:
            try:
                # Coleta itens da fila para escrita em background
                key, value = self.queue.get(timeout=0.01)
                self.db.write(key, value)
                self.queue.task_done()
            except Empty:
                continue

    def set(self, key, value):
        # Atualiza apenas o cache de forma imediata e enfileira para escrita posterior
        self.cache[key] = value
        self.queue.put((key, value))

    def get(self, key):
        return self.cache.get(key, None)

    def stop(self):
        self.queue.join() # Aguarda a fila esvaziar
        self.running = False
        self.worker_thread.join()

if __name__ == "__main__":
    print("--- INICIANDO EXPERIMENTO DE CACHE (CORRIGIDO) ---")
    
    db_wt = MockDatabase(latency_ms=0.02)
    db_wb = MockDatabase(latency_ms=0.02)

    wt_cache = WriteThroughCache(db_wt)
    wb_cache = WriteBehindCache(db_wb)

    n_operations = 50

    # Teste de Write-Through
    wt_latencies = []
    t_start = time.time()
    for i in range(n_operations):
        start = time.time()
        wt_cache.set(f"key_{i}", f"val_{i}")
        wt_latencies.append(time.time() - start)
    wt_total = time.time() - t_start
    avg_wt_latency = sum(wt_latencies) / len(wt_latencies)

    # Teste de Write-Behind
    wb_latencies = []
    t_start = time.time()
    for i in range(n_operations):
        start = time.time()
        wb_cache.set(f"key_{i}", f"val_{i}")
        wb_latencies.append(time.time() - start)
    
    # Aguardar o worker esvaziar a fila para garantir persistência no teste
    wb_cache.stop()
    wb_total = time.time() - t_start
    avg_wb_latency = sum(wb_latencies) / len(wb_latencies)

    print(f"\n[Resultados de Escrita - {n_operations} operações]")
    print(f"Write-Through Média por escrita: {avg_wt_latency*1000:.2f} ms (Total: {wt_total:.3f}s)")
    print(f"Write-Behind  Média por escrita: {avg_wb_latency*1000:.2f} ms (Total: {wb_total:.3f}s)")
    
    reduction = ((avg_wt_latency - avg_wb_latency) / avg_wt_latency) * 100
    print(f"Redução de latência de escrita obtida: {reduction:.1f}%")
    assert reduction >= 30, f"Falha na meta: Redução foi de apenas {reduction}%"

    # Teste de Read-Through e Cache Misses
    db_rt = MockDatabase(latency_ms=0.01)
    for i in range(10):
        db_rt.store[f"doc_{i}"] = f"content_{i}"
        
    rt_cache = ReadThroughCache(db_rt, capacity=5)
    
    # 1ª Leitura (Deve gerar Cache Miss e popular o cache)
    val1 = rt_cache.get("doc_1")
    # 2ª Leitura da mesma chave (Deve ser Cache Hit)
    val2 = rt_cache.get("doc_1")
    
    print(f"\n[Resultados Read-Through]")
    print(f"Total Hits: {rt_cache.hits}, Total Misses: {rt_cache.misses}")
    print(f"Taxa de Miss na segunda requisição: {(rt_cache.misses / (rt_cache.hits + rt_cache.misses))*100}%")
    
    assert rt_cache.misses == 1, "Deveria ter ocorrido exatamente 1 miss inicial."
    assert rt_cache.hits == 1, "A segunda leitura deveria ser um hit."

    print("\n--- EXPERIMENTO EXECUTADO COM SUCESSO E ASSERTIVAS ATENDIDAS ---")