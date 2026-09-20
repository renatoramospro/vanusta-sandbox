import time
import threading
from collections import OrderedDict

class ThreadSafeLRUCache:
    """
    Um cache em memória thread-safe com suporte a LRU eviction e per-item TTL.
    """
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Capacity must be greater than 0")
        self.capacity = capacity
        self.cache = OrderedDict()
        self.ttls = {}  # Mapeia chave -> timestamp de expiração absoluta
        self.lock = threading.Lock()

    def _is_expired(self, key: str, now: float) -> bool:
        """Verifica se um item expirou com base no TTL."""
        if key in self.ttls and self.ttls[key] <= now:
            return True
        return False

    def _remove(self, key: str):
        """Remove a chave do cache e do dicionário de TTL."""
        self.cache.pop(key, None)
        self.ttls.pop(key, None)

    def get(self, key: str):
        now = time.time()
        with self.lock:
            if key not in self.cache:
                return None
            
            # Checagem de TTL (Lazy eviction)
            if self._is_expired(key, now):
                self._remove(key)
                return None
            
            # Move para o fim para indicar uso recente (LRU)
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: str, value, ttl: float = None):
        now = time.time()
        expire_at = now + ttl if ttl is not None else None

        with self.lock:
            # Se a chave já existe, removemos para atualizar a ordem e o TTL
            if key in self.cache:
                self._remove(key)
            
            # Se atingiu a capacidade máxima, removemos o item menos recentemente usado (início do OrderedDict)
            elif len(self.cache) >= self.capacity:
                oldest_key = next(iter(self.cache))
                self._remove(oldest_key)

            self.cache[key] = value
            if expire_at is not None:
                self.ttls[key] = expire_at
            self.cache.move_to_end(key)

    def size(self) -> int:
        now = time.time()
        with self.lock:
            # Remove expirados antes de retornar o tamanho (para precisão)
            expired_keys = [k for k in self.cache if self._is_expired(k, now)]
            for k in expired_keys:
                self._remove(k)
            return len(self.cache)


# --- Experimento Concreto e Testes de Comportamento ---

def test_lru_eviction():
    print("Executando teste de LRU Eviction...")
    cache = ThreadSafeLRUCache(capacity=2)
    cache.put("a", 1)
    cache.put("b", 2)
    
    # Acessa 'a', tornando 'b' o menos recentemente usado
    assert cache.get("a") == 1
    
    # Adiciona 'c', o que deve evictar 'b'
    cache.put("c", 3)
    
    assert cache.get("a") == 1
    assert cache.get("b") is None  # 'b' foi evictado
    assert cache.get("c") == 3
    print("-> Teste de LRU Eviction passou com sucesso!")

def test_ttl_expiration():
    print("Executando teste de TTL Expiration...")
    cache = ThreadSafeLRUCache(capacity=10)
    cache.put("fast_expire", "val", ttl=0.1) # expira em 100ms
    
    assert cache.get("fast_expire") == "val"
    time.sleep(0.15) # espera expirar
    assert cache.get("fast_expire") is None
    print("-> Teste de TTL Expiration passou com sucesso!")

def test_concurrency_stress():
    print("Executando teste de concorrência (Stress Test)...")
    cache = ThreadSafeLRUCache(capacity=100)
    num_threads = 20
    ops_per_thread = 500

    def worker(thread_id):
        for i in range(ops_per_thread):
            key = f"key_{i % 150}" # Chaves sobrepostas para forçar contenção e evictions
            if i % 2 == 0:
                cache.put(key, thread_id * 1000 + i, ttl=2.0)
            else:
                cache.get(key)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(num_threads)]
    
    start_time = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    duration = time.time() - start_time

    print(f"-> {num_threads * ops_per_thread} operações concorrentes concluídas em {duration:.3f}s")
    # Verifica invariant de capacidade máxima
    assert cache.size() <= cache.capacity
    print("-> Teste de concorrência passou sem corromper o estado ou violar a capacidade!")

if __name__ == "__main__":
    test_lru_eviction()
    test_ttl_expiration()
    test_concurrency_stress()
    print("TODOS OS EXPERIMENTOS EXECUTADOS COM SUCESSO!")