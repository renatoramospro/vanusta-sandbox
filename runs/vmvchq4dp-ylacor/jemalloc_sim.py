import threading
import time
import random

# --- 1. Alocador Global (Padrão com Contenção) ---
class GlobalAllocator:
    def __init__(self):
        self.lock = threading.Lock()
        self.memory_pool = {}
        self.lock_acquisitions = 0
        self.total_wait_time = 0.0

    def allocate(self, size):
        start = time.perf_counter()
        with self.lock:
            self.lock_acquisitions += 1
            # Simula busca de bloco
            block_id = random.randint(1, 1000000)
            self.memory_pool[block_id] = size
        self.total_wait_time += (time.perf_counter() - start)
        return block_id

    def free(self, block_id):
        with self.lock:
            self.lock_acquisitions += 1
            if block_id in self.memory_pool:
                del self.memory_pool[block_id]

# --- 2. Alocador Jemalloc-style (Arenas por Thread + Bins Fixos) ---
class ThreadLocalArenaAllocator:
    def __init__(self):
        self.bins = {32: [], 64: [], 128: [], 256: []}
        # Thread Local Storage simulado via thread-local data
        self.local_storage = threading.local()
        self.global_lock = threading.Lock()
        self.lock_acquisitions = 0

    def _get_bin_size(self, size):
        for b in sorted(self.bins.keys()):
            if size <= b:
                return b
        return 256 # Máximo suportado no bin fixo

    def allocate(self, size):
        bin_size = self._get_bin_size(size)
        
        # Inicializa arena local da thread se não existir
        if not hasattr(self.local_storage, 'arena'):
            self.local_storage.arena = {32: [], 64: [], 128: [], 256: []}
        
        # Tenta alocar na arena local (SEM LOCK)
        if self.local_storage.arena[bin_size]:
            return self.local_storage.arena[bin_size].pop()
        
        # Se a arena local estiver vazia, pega um lote do pool global (com lock mínimo)
        with self.global_lock:
            self.lock_acquisitions += 1
            return random.randint(1, 1000000)

    def free(self, block_id, size):
        bin_size = self._get_bin_size(size)
        # Retorna para a arena local da thread para reuso rápido
        if hasattr(self.local_storage, 'arena'):
            self.local_storage.arena[bin_size].append(block_id)

# --- 3. Função de Benchmark ---
def run_benchmark(allocator_type, num_threads, iterations_per_thread):
    if allocator_type == "global":
        allocator = GlobalAllocator()
    else:
        allocator = ThreadLocalArenaAllocator()

    def worker():
        for _ in range(iterations_per_thread):
            size = random.choice([16, 48, 90, 200])
            if allocator_type == "global":
                ptr = allocator.allocate(size)
                allocator.free(ptr)
            else:
                ptr = allocator.allocate(size)
                allocator.free(ptr, size)

    threads = [threading.Thread(target=worker) for _ in range(num_threads)]
    
    start_time = time.perf_counter()
    for t in threads: t.start()
    for t in threads: t.join()
    duration = time.perf_counter() - start_time

    return duration, allocator.lock_acquisitions

if __name__ == "__main__":
    NUM_THREADS = 8
    ITERATIONS = 5000

    print(f"Executando benchmarks com {NUM_THREADS} threads e {ITERATIONS} iterações por thread...\n")

    t_global, locks_global = run_benchmark("global", NUM_THREADS, ITERATIONS)
    t_jemalloc, locks_jemalloc = run_benchmark("jemalloc", NUM_THREADS, ITERATIONS)

    print(f"Alocador Global (Lock Único):")
    print(f"  - Tempo total: {t_global:.4f} segundos")
    print(f"  - Aquisições de Lock: {locks_global}\n")

    print(f"Alocador Jemalloc-style (Arenas por Thread):")
    print(f"  - Tempo total: {t_jemalloc:.4f} segundos")
    print(f"  - Aquisições de Lock: {locks_jemalloc}\n")

    reduction = ((locks_global - locks_jemalloc) / locks_global) * 100
    print(f"Redução de contenção de locks: {reduction:.2f}%")
    
    # Validação do critério de sucesso
    assert locks_jemalloc < locks_global, "O alocador jemalloc-style deve ter menos aquisições de lock global."
    print("\n[SUCESSO] O experimento demonstrou com sucesso a eliminação de contenção via arenas por thread.")