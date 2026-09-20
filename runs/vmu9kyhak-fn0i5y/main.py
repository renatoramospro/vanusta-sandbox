import threading
import time
import random
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class CacheEntry:
    value: Any
    expires_at: float

class LRUCacheWithTTL:
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.cache: OrderedDict[Any, CacheEntry] = OrderedDict()
        self.lock = threading.Lock()

    def get(self, key: Any) -> Optional[Any]:
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            # Verificação de TTL (Expiração Passiva)
            if time.time() > entry.expires_at:
                del self.cache[key]
                return None
            
            # Atualiza para LRU (move para o fim)
            self.cache.move_to_end(key)
            return entry.value

    def set(self, key: Any, value: Any, ttl: float) -> None:
        expiry = time.time() + ttl
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            
            self.cache[key] = CacheEntry(value, expiry)
            
            # Evicção LRU se exceder o tamanho
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    def size(self) -> int:
        with self.lock:
            return len(self.cache)

def run_stress_test():
    print("--- Iniciando Stress Test ---")
    cache_size = 100
    cache = LRUCacheWithTTL(max_size=cache_size)
    num_threads = 100
    ops_per_thread = 1000 
    
    # Espaço de chaves limitado para garantir hits (conforme sugerido pelo Arquiteto)
    # Se o range for muito grande, o hit ratio cai. 
    # Com range 150 e cache 100, o hit ratio será alto.
    key_range = 150 
    
    stats = {"hits": 0, "misses": 0}
    stats_lock = threading.Lock()

    def worker():
        for _ in range(ops_per_thread):
            key = random.randint(0, key_range)
            op = random.random()
            
            if op < 0.4:  # 40% de chance de SET
                cache.set(key, f"val_{key}", ttl=10.0)
            else:         # 60% de chance de GET
                val = cache.get(key)
                with stats_lock:
                    if val is not None:
                        stats["hits"] += 1
                    else:
                        stats["misses"] += 1

    threads = []
    start_time = time.time()
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    
    duration = time.time() - start_time
    total_ops = stats["hits"] + stats["misses"]
    hit_ratio = (stats["hits"] / total_ops) * 100 if total_ops > 0 else 0

    print(f"Tempo: {duration:.2f}s")
    print(f"Total de Ops: {total_ops}")
    print(f"Hits: {stats['hits']}, Misses: {stats['misses']}")
    print(f"Hit Ratio: {hit_ratio:.2f}%")
    print(f"Tamanho final do cache: {cache.size()} (Max: {cache_size})")
    
    # Validações de integridade
    assert cache.size() <= cache_size, "Erro: Cache excedeu o tamanho máximo!"
    print("--- Stress Test Concluído com Sucesso ---")

def test_logic():
    print("--- Testando Lógica de LRU e TTL ---")
    cache = LRUCacheWithTTL(max_size=2)

    # Teste LRU
    cache.set("a", 1, ttl=10)
    cache.set("b", 2, ttl=10)
    cache.get("a")      # 'a' agora é o mais recente
    cache.set("c", 3, ttl=10) # deve evictar 'b'
    
    assert cache.get("b") is None, "Erro: 'b' deveria ter sido evicto por LRU"
    assert cache.get("a") == 1, "Erro: 'a' deveria estar no cache"
    print("LRU OK")

    # Teste TTL
    cache.set("d", 4, ttl=0.1)
    time.sleep(0.2)
    assert cache.get("d") is None, "Erro: 'd' deveria ter expirado por TTL"
    print("TTL OK")

if __name__ == "__main__":
    test_logic()
    run_stress_test()