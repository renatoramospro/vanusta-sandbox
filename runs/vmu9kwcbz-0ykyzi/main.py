import threading
import time
import random
from collections import OrderedDict

class ThreadSafeLRUCache:
    def __init__(self, max_size: int):
        self.max_size = max_size
        self._cache = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry = self._cache[key]
            
            if expiry is not None and time.time() > expiry:
                del self._cache[key]
                return None
            
            self._cache.move_to_end(key)
            return value

    def set(self, key, value, ttl=None):
        expiry = (time.time() + ttl) if ttl is not None else None
        
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            
            self._cache[key] = (value, expiry)
            
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def __len__(self):
        with self._lock:
            return len(self._cache)

def stress_test(cache, num_threads, ops_per_thread, key_space_size):
    hits = 0
    misses = 0
    keys = list(range(key_space_size))
    weights = [1.0 / (i + 1) for i in keys] 

    results = []
    lock_results = threading.Lock()

    def worker():
        nonlocal hits, misses
        local_hits = 0
        local_misses = 0
        for _ in range(ops_per_thread):
            op = random.random()
            key = random.choices(keys, weights=weights, k=1)[0]
            
            if op < 0.7:
                val = cache.get(key)
                if val is not None:
                    local_hits += 1
                else:
                    local_misses += 1
            else:
                cache.set(key, f"val_{key}", ttl=random.uniform(0.1, 0.5))
        
        with lock_results:
            results.append((local_hits, local_misses))

    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    for h, m in results:
        hits += h
        misses += m

    total_ops = hits + misses
    hit_ratio = (hits / total_ops) * 100 if total_ops > 0 else 0
    return hit_ratio, len(cache)

def run_experiment():
    # 1. Teste de Corretness: TTL
    ttl_cache = ThreadSafeLRUCache(max_size=10)
    ttl_cache.set("temp", "data", ttl=0.1)
    assert ttl_cache.get("temp") == "data"
    time.sleep(0.2)
    assert ttl_cache.get("temp") is None
    
    # 2. Teste de Corretness: LRU Eviction
    lru_cache = ThreadSafeLRUCache(max_size=2)
    lru_cache.set(1, "a")
    lru_cache.set(2, "b")
    lru_cache.get(1)
    lru_cache.set(3, "c")
    assert lru_cache.get(1) == "a"
    assert lru_cache.get(2) is None
    
    # 3. Teste de Stress
    stress_cache = ThreadSafeLRUCache(max_size=50)
    hit_ratio, final_size = stress_test(stress_cache, 20, 1000, 100)

    print(f"Hit Ratio: {hit_ratio:.2f}%")
    print(f"Final Size: {final_size}")
    
    assert final_size <= 50
    assert hit_ratio > 40 # Threshold ajustado para a distribuição de pesos
    print("EXPERIMENTO CONCLUÍDO COM SUCESSO")

if __name__ == "__main__":
    run_experiment()