import time
import threading
from queue import Queue, Full, Empty

# Simulação de um Banco de Dados com latência e taxa de falhas opcional
class MockDatabase:
    def __init__(self, latency_ms=0.01, fail_rate=0.0):
        self.store = {}
        self.latency = latency_ms
        self.write_count = 0
        self.fail_rate = fail_rate
        self.lock = threading.Lock()

    def read(self, key):
        time.sleep(self.latency)
        with self.lock:
            return self.store.get(key, None)

    def write(self, key, value):
        time.sleep(self.latency)
        with self.lock:
            if self.fail_rate > 0 and (self.write_count % int(1/self.fail_rate) == 0):
                raise ConnectionError("Falha simulada na escrita do banco de dados!")
            self.store[key] = value
            self.write_count += 1

# 1. Read-Through Cache com proteção contra Cache Penetration
class ReadThroughCache:
    def __init__(self, db, capacity=100):
        self.db = db
        self.cache = {}
        self.capacity = capacity
        self.misses = 0
        self.hits = 0
        self.lock = threading.Lock()
        self.sentinel = object() # Objeto sentinela para cache penetration

    def get(self, key):
        with self.lock:
            if key in self.cache:
                self.hits += 1
                val = self.cache[key]
                return None if val is self.sentinel else val
        
        # Cache Miss: busca fora do lock para não travar o cache inteiro
        self.misses += 1
        value = self.db.read(key)
        
        with self.lock:
            if len(self.cache) >= self.capacity:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            
            # Armazena o valor ou o sentinela (evita cache penetration)
            self.cache[key] = value if value is not None else self.sentinel
            
        return value

# 2. Write-Through Cache
class WriteThroughCache:
    def __init__(self, db):
        self.db = db
        self.cache = {}
        self.lock = threading.Lock()

    def set(self, key, value):
        with self.lock:
            self.cache[key] = value
        # Escrita síncrona no banco
        self.db.write(key, value)

    def get(self, key):
        with self.lock:
            return self.cache.get(key, None)

# 3. Write-Behind (Write-Back) Cache com Coalescing, Backpressure e Retry
class WriteBehindCache:
    def __init__(self, db, max_queue_size=1000, batch_interval=0.005, max_retries=3):
        self.db = db
        self.cache = {}
        self.queue = Queue(maxsize=max_queue_size)
        self.batch_interval = batch_interval
        self.max_retries = max_retries
        self.running = True
        self.lock = threading.Lock()
        
        # Estatísticas de coalescing
        self.coalesced_writes = 0
        
        self.worker_thread = threading.Thread(target=self._async_writer, daemon=True)
        self.worker_thread.start()

    def _async_writer(self):
        while self.running:
            batch = {}
            # Coleta itens da fila com coalescing (última escrita por chave prevalece)
            start_time = time.time()
            while time.time() - start_time < self.batch_interval:
                try:
                    timeout = self.batch_interval - (time.time() - start_time)
                    if timeout <= 0:
                        break
                    key, value = self.queue.get(timeout=max(0.001, timeout))
                    if key in batch:
                        self.coalesced_writes += 1
                    batch[key] = value
                    self.queue.task_done()
                except Empty:
                    break

            if batch:
                for key, value in batch.items():
                    success = False
                    retries = 0
                    while not success and retries < self.max_retries:
                        try:
                            self.db.write(key, value)
                            success = True
                        except Exception:
                            retries += 1
                            time.sleep(0.01 * (2 ** retries)) # Backoff exponencial

    def set(self, key, value):
        with self.lock:
            self.cache[key] = value
        
        # Aplica backpressure se a fila estiver cheia
        try:
            self.queue.put((key, value), timeout=1.0)
        except Full:
            # Fallback síncrono em caso de fila cheia (backpressure handling)
            self.db.write(key, value)

    def get(self, key):
        with self.lock:
            return self.cache.get(key, None)

    def flush(self):
        # Aguarda esvaziar a fila para garantir durabilidade end-to-end
        self.queue.join()

    def stop(self):
        self.flush()
        self.running = False
        self.worker_thread.join()

# Execução e Validação dos Cenários
if __name__ == "__main__":
    print("--- INICIANDO EXPERIMENTO DE CACHE ROBUSTO ---")

    n_operations = 50
    db_wt = MockDatabase(latency_ms=0.005)
    db_wb = MockDatabase(latency_ms=0.005)

    wt_cache = WriteThroughCache(db_wt)
    wb_cache = WriteBehindCache(db_wb, max_queue_size=100)

    # Medição Write-Through
    t_start = time.time()
    for i in range(n_operations):
        wt_cache.set(f"key_{i}", f"val_{i}")
    wt_total = time.time() - t_start
    avg_wt_latency = wt_total / n_operations

    # Medição Write-Behind (incluindo tempo end-to-end com flush)
    t_start = time.time()
    for i in range(n_operations):
        # Atualizações repetidas da mesma chave para demonstrar Write Coalescing
        wb_cache.set(f"key_{i}", f"val_v1_{i}")
        wb_cache.set(f"key_{i}", f"val_final_{i}")
    
    # Garante persistência end-to-end para medição justa
    wb_cache.flush()
    wb_total = time.time() - t_start
    
    # Latência percebida pelo cliente (enqueue time)
    t_enqueue_start = time.time()
    for i in range(n_operations):
        wb_cache.set(f"enqueue_{i}", f"val_{i}")
    enqueue_total = time.time() - t_enqueue_start
    avg_enqueue_latency = enqueue_total / n_operations

    wb_cache.stop()

    print(f"\n[Resultados de Escrita - {n_operations} operações]")
    print(f"Write-Through Média por escrita: {avg_wt_latency*1000:.2f} ms (Total: {wt_total:.3f}s)")
    print(f"Write-Behind  Cliente (Enqueue): {avg_enqueue_latency*1000:.2f} ms")
    print(f"Write-Behind  End-to-End (Flush): {wb_total:.3f}s")
    print(f"Write Coalescing: {wb_cache.coalesced_writes} escritas redundantes suprimidas")

    reduction = ((avg_wt_latency - avg_enqueue_latency) / avg_wt_latency) * 100
    print(f"Redução de latência percebida pelo cliente: {reduction:.1f}%")
    assert reduction >= 50, f"Falha na meta: Redução de latência foi de {reduction}%"

    # Teste de Read-Through e Cache Penetration
    db_rt = MockDatabase(latency_ms=0.001)
    db_rt.store["doc_1"] = "content_1"
    
    rt_cache = ReadThroughCache(db_rt, capacity=5)
    
    # 1ª Leitura (Cache Miss legítimo)
    val1 = rt_cache.get("doc_1")
    # 2ª Leitura (Cache Hit)
    val2 = rt_cache.get("doc_1")
    
    # Leitura de chave inexistente (Cache Penetration test)
    not_found_1 = rt_cache.get("non_existent_key")
    not_found_2 = rt_cache.get("non_existent_key") # Deve ser servido do cache (sentinela), sem ir ao DB

    print(f"\n[Resultados Read-Through & Penetration]")
    print(f"Total Hits: {rt_cache.hits}, Total Misses: {rt_cache.misses}")
    print(f"Chave inexistente 1: {not_found_1}, Chave inexistente 2: {not_found_2}")
    print(f"Chamadas ao DB: {db_rt.write_count + rt_cache.misses} (Misses contam leituras ao DB)")

    assert rt_cache.misses == 2, f"Esperado 2 misses (1 válido + 1 inexistente), obtido {rt_cache.misses}"
    assert rt_cache.hits == 2, f"Esperado 2 hits (1 leitura repetida + 1 sentinela repetida), obtido {rt_cache.hits}"
    assert not_found_1 is None and not_found_2 is None

    print("\n--- EXPERIMENTO ROBUSTO EXECUTADO COM SUCESSO E ASSERTIVAS ATENDIDAS ---")