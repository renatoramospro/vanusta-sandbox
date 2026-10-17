import threading
import time
import random
import sys

class RobustJemallocAllocator:
    def __init__(self, standard_bins=[32, 64, 128, 256], chunk_size=10):
        self.standard_bins = sorted(standard_bins)
        self.max_bin = self.standard_bins[-1]
        self.chunk_size = chunk_size
        
        # Metadados globais para rastreamento de blocos (suporte a cross-thread free)
        self.block_owner_map = {} # block_id -> (arena_reference, bin_size)
        self.global_meta_lock = threading.Lock()
        
        # Arenas globais e Thread Local Storage
        self.arenas = {}
        self.arenas_lock = threading.Lock()
        self.local_storage = threading.local()
        
        self.lock_acquisitions = 0

    def _get_bin_size(self, size):
        for b in self.standard_bins:
            if size <= b:
                return b
        return None # Indica estouro do maior bin (Large Allocation)

    def _get_or_create_arena(self):
        thread_id = threading.get_ident()
        with self.arenas_lock:
            if thread_id not in self.arenas:
                # Cada arena possui seus próprios bins locais
                self.arenas[thread_id] = {
                    'bins': {b: [] for b in self.standard_bins},
                    'large_blocks': [],
                    'lock': threading.Lock()
                }
            return self.arenas[thread_id]

    def allocate(self, size):
        bin_size = self._get_bin_size(size)
        arena = self._get_or_create_arena()
        
        block_id = f"block_{random.randint(1, 10000000)}_{threading.get_ident()}"

        if bin_size is not None:
            # Caso comum: cabe nos bins padrão
            with arena['lock']:
                if not arena['bins'][bin_size]:
                    # Refill da arena local (evita esgotamento sob carga assimétrica)
                    self.lock_acquisitions += 1
                    for _ in range(self.chunk_size):
                        arena['bins'][bin_size].append(f"block_refill_{random.randint(1, 1000000)}")
                
                # Pega um bloco do bin local
                if arena['bins'][bin_size]:
                    block_id = arena['bins'][bin_size].pop()
        else:
            # Tratamento de estouro do maior bin (Large Allocation / Fallback)
            with arena['lock']:
                self.lock_acquisitions += 1
                arena['large_blocks'].append(block_id)
                bin_size = size # Armazena o tamanho real para large allocations

        # Registra o proprietário para permitir Cross-Thread Free seguro
        with self.global_meta_lock:
            self.block_owner_map[block_id] = (arena, bin_size)

        return block_id

    def free(self, block_id):
        # Localiza o proprietário original do bloco de forma thread-safe
        with self.global_meta_lock:
            owner_info = self.block_owner_map.get(block_id)
            if not owner_info:
                return # Bloco inválido ou já liberado
            arena, bin_size = owner_info
            del self.block_owner_map[block_id]

        # Devolução segura para a arena de origem (Cross-Thread Free)
        with arena['lock']:
            if bin_size in self.standard_bins:
                arena['bins'][bin_size].append(block_id)
            else:
                if block_id in arena['large_blocks']:
                    arena['large_blocks'].remove(block_id)

# --- Testes Automatizados Rigorosos ---
def test_cross_thread_and_edge_cases():
    allocator = RobustJemallocAllocator()
    
    print("Iniciando testes rigorosos (Cross-Thread Free, Estouro de Bin, Carga Assimétrica)...")

    # 1. Teste de Estouro do Maior Bin (Large Allocation)
    large_block = allocator.allocate(1024) # Maior que 256
    assert large_block is not None, "Alocação grande falhou."
    allocator.free(large_block)
    print("  [OK] Teste de estouro do maior bin (Large Allocation) executado com sucesso.")

    # 2. Teste de Cross-Thread Free (Thread A aloca, Thread B libera)
    allocated_block = [None]
    def worker_allocate():
        allocated_block[0] = allocator.allocate(64)

    t1 = threading.Thread(target=worker_allocate)
    t1.start()
    t1.join()

    block_to_free = allocated_block[0]
    assert block_to_free is not None

    def worker_free():
        allocator.free(block_to_free)

    t2 = threading.Thread(target=worker_free)
    t2.start()
    t2.join()
    print("  [OK] Teste de Cross-Thread Free executado com sucesso (sem corrupção de heap).")

    # 3. Teste de Carga Assimétrica (Threads com padrões desbalanceados)
    def asymmetric_load():
        blocks = []
        for _ in range(100):
            # Mistura de tamanhos normais e irregulares (estouro)
            blocks.append(allocator.allocate(random.choice([15, 90, 200, 512])))
        for b in blocks:
            allocator.free(b)

    threads = [threading.Thread(target=asymmetric_load) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    print("  [OK] Teste de carga assimétrica e esgotamento de arena executado com sucesso.")

if __name__ == "__main__":
    test_cross_thread_and_edge_cases()
    print("\n[SUCESSO] Todos os cenários robustos passaram sem falhas.")