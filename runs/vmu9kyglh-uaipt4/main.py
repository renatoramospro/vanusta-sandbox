import threading
import time
import random
from collections import OrderedDict

class ThreadSafeLRUCache:
    """
    Implementação robusta de um cache LRU com TTL e Thread-Safety.
    """
    def __init__(self, max_size: int):
        self.max_size = max_size
        self._cache = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry = self._cache[key]
            
            # Verificação de TTL (Lazy Expiration)
            if expiry is not None and time.monotonic() > expiry:
                del self._cache[key]
                return None
            
            # LRU: Move para o final para marcar como recentemente usado
            self._cache.move_to_end(key)
            return value

    def set(self, key, value, ttl=None):
        expiry = (time.monotonic() + ttl) if ttl is not range else None
        # Nota: Corrigindo lógica de TTL para aceitar float/int
        expiry = (time.monotonic() + ttl) if ttl is not None else None
        
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            
            self._cache[key] = (value, expiry)
            
            # Evicção LRU
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def size(self):
        with self._lock:
            return len(self._cache)

class BrokenCache:
    """
    Implementação propositalmente insegura para demonstrar Race Conditions.
    Não usa Lock em operações compostas.
    """
    def __init__(self, max_size: int):
        self.max_size = max_size
        self._cache = OrderedDict()

    def get(self, key):
        # ERRO: Operação composta sem lock. 
        # O 'if' e o 'move_to_end' não são atômicos.
        if key in self._cache:
            # Outro thread pode deletar a chave aqui (evicção ou TTL)
            self._cache.move_to_end(key)
            return self._cache[key][0]
        return None

    def set(self, key, value, ttl=None):
        expiry = (time.monotonic() + ttl) if ttl is not None else None
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, expiry)
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

def stress_test(cache_instance, num_threads=100, ops_per_thread=1000, key_range=1000):
    hits = 0
    misses = 0
    errors = 0
    
    # Usamos uma distribuição de pesos para simular "Hot Keys" (Zipfian-like)
    # Isso garante que o LRU seja testado e o hit ratio seja alto.
    keys = [f"key_{i}" for i in range(key_range)]
    weights = [1.0 / (i + 1) for i in range(key_range)]
    
    def worker():
        nonlocal hits, misses, errors
        for _ in range(ops_per_thread):
            try:
                op = random.random()
                key = random.choices(keys, weights=weights)[0]
                
                if op < 0.7:  # 70% GET
                    res = cache_instance.get(key)
                    if res is not None:
                        hits += 1
                    else:
                        misses += 1
                else:  # 30% SET
                    # TTL curto para testar expiração
                    ttl = random.choice([None, 0.1, 0.5])
                    cache_instance.set(key, "val", ttl=ttl)
            except Exception:
                errors += 1

    threads = []
    start_time = time.time()
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    duration = time.time() - start_time

    total_ops = hits + misses
    hit_ratio = (hits / total_ops) * 100 if total_ops > 0 else 0
    
    return {
        "hit_ratio": hit_ratio,
        "errors": errors,
        "duration": duration,
        "final_size": cache_instance.size() if hasattr(cache_instance, 'size') else len(cache_instance._cache)
    }

if __name__ == "__main__":
    print("--- Iniciando Teste de Stress: ThreadSafeLRUCache ---")
    safe_cache = ThreadSafeLRUCache(max_size=500)
    results = stress_test(safe_cache, num_threads=100, ops_per_thread=1000)
    
    print(f"Resultado: Hit Ratio: {results['hit_ratio']:.2f}% | Erros: {results['errors']} | Tempo: {results['duration']:.2f}s")
    print(f"Tamanho Final: {results['final_size']} (Esperado <= 500)")
    
    assert results['errors'] == 0, "Cache seguro apresentou erros!"
    assert results['hit_ratio'] > 80, f"Hit ratio muito baixo: {results['hit_ratio']}%"
    assert results['final_size'] <= 500, "Cache excedeu o tamanho máximo!"

    print("\n--- Iniciando Teste de Stress: BrokenCache (Esperado Falhar) ---")
    broken_cache = BrokenCache(max_size=500)
    results_broken = stress_test(broken_cache, num_threads=100, ops_per_thread=1000)
    
    print(f"Resultado: Hit Ratio: {results_broken['hit_ratio']:.2f}% | Erros: {results_broken['errors']}")
    
    if results_broken['errors'] > 0:
        print("SUCESSO: O BrokenCache falhou como esperado (Race Condition detectada via KeyError).")
    else:
        print("FALHA: O BrokenCache não apresentou erros. Tente aumentar a carga.")