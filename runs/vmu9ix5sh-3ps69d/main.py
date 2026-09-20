import time
import threading
from functools import wraps
from collections import OrderedDict

class Counter:
    def __init__(self):
        self.count = 0
        self._lock = threading.Lock()
    def increment(self):
        with self._lock:
            self.count += 1

def memoize(ttl=5, maxsize=128):
    """
    Decorador de memoização robusto com:
    - TTL (Time-To-Live)
    - Limite de tamanho (maxsize) com política FIFO
    - Thread-safety via RLock (prevenção de Cache Stampede)
    - Conversão recursiva de argumentos mutáveis para tipos hasháveis
    """
    def decorator(func):
        # cache armazena: { hashable_key: (result, expiry_timestamp) }
        cache = OrderedDict()
        lock = threading.RLock()

        def _make_hashable(obj):
            """Converte recursivamente objetos mutáveis em imutáveis."""
            if isinstance(obj, (list, tuple)):
                return tuple(_make_hashable(item) for item in obj)
            if isinstance(obj, dict):
                return frozenset((k, _make_hashable(v)) for k, v in obj.items())
            if isinstance(obj, set):
                return frozenset(_make_hashable(item) for item in obj)
            return obj

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Preparar a chave de cache de forma robusta e recursiva
            hashable_args = _make_hashable(args)
            hashable_kwargs = _make_hashable(kwargs)
            key = (hashable_args, hashable_kwargs)

            now = time.time()

            with lock:
                # 2. Verificar se existe no cache e se não expirou
                if key in cache:
                    result, expiry = cache[key]
                    if now < expiry:
                        return result
                    else:
                        # Expira o item
                        del cache[key]

                # 3. Executar a função (dentro do lock para evitar Cache Stampede)
                result = func(*args, **kwargs)
                
                # 4. Gerenciar tamanho do cache (FIFO)
                if len(cache) >= maxsize and maxsize > 0:
                    cache.popitem(last=False)
                
                # 5. Salvar no cache
                expiry = now + ttl
                cache[key] = (result, expiry)
                return result

        def clear_cache():
            with lock:
                cache.clear()

        wrapper.clear_cache = clear_cache
        return wrapper
    return decorator

def run_tests():
    print("--- Iniciando Testes de Rigor ---")

    # Teste 1: Memoização básica
    call_count = 0
    @memoize(ttl=10)
    def basic_func(x):
        nonlocal call_count
        call_count += 1
        return x

    assert basic_func(1) == 1
    assert basic_func(1) == 1
    assert call_count == 1
    print("✅ Teste 1: Memoização básica passou.")

    # Teste 2: Expiração de TTL
    @memoize(ttl=1)
    def ttl_func(x):
        return x

    ttl_func.clear_cache()
    ttl_func(1)
    time.sleep(1.1)
    # Para testar re-execução, usamos um contador
    counter_ttl = Counter()
    @memoize(ttl=1)
    def ttl_counter_func(x):
        counter_ttl.increment()
        return x
    
    ttl_counter_func.clear_cache()
    ttl_counter_func(1) # call 1
    time.sleep(1.1)
    ttl_counter_func(1) # call 2
    assert counter_ttl.count == 2
    print("✅ Teste 2: Expiração de TTL passou.")

    # Teste 3: Argumentos mutáveis (O ponto de falha anterior)
    counter_mut = Counter()
    @memoize(ttl=10)
    def mutable_func(a, b):
        counter_mut.increment()
        return f"{a}-{b}"

    # Teste com lista e dict aninhados
    res = mutable_func([1, 2], {"key": [3, 4]})
    assert res == "[1, 2]-{'key': [3, 4]}"
    assert mutable_func([1, 2], {"key": [3, 4]}) == res
    assert counter_mut.count == 1
    print("✅ Teste 3: Argumentos mutáveis (list/dict) passaram.")

    # Teste 4: Concorrência (Cache Stampede prevention)
    counter_con = Counter()
    @memoize(ttl=10)
    def concurrent_func(x):
        time.sleep(0.1) # Simula carga
        counter_con.increment()
        return x

    concurrent_func.clear_cache()
    threads = []
    for _ in range(10):
        t = threading.Thread(target=concurrent_func, args=(10,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    # Se o lock funcionar, apenas 1 thread deve ter incrementado o contador
    assert counter_con.count == 1
    print(f"✅ Teste 4: Concorrência passou (Chamadas reais: {counter_con.count}).")

    # Teste 5: Limite de Tamanho (Maxsize FIFO)
    counter_size = Counter()
    @memoize(ttl=10, maxsize=2)
    def size_func(x):
        counter_size.increment()
        return x

    size_func.clear_cache()
    size_func(1) # count 1
    size_func(2) # count 2
    size_func(3) # count 3 (expulsa o 1)
    size_func(1) # count 4 (pois o 1 foi expulso)
    assert counter_size.count == 4
    print("✅ Teste 5: Limite de maxsize (FIFO) passou.")

    # Teste 6: TTL Zero (Execução sempre)
    counter_zero = Counter()
    @memoize(ttl=0)
    def zero_ttl_func(x):
        counter_zero.increment()
        return x
    
    zero_ttl_func.clear_cache()
    zero_ttl_func(1)
    zero_ttl_func(1)
    assert counter_zero.count == 2
    print("✅ Teste 6: TTL=0 passou.")

    # Teste 7: Independência de instâncias
    counter_ind = Counter()
    @memoize(ttl=10)
    def func_a(x):
        counter_ind.increment()
        return x
    @memoize(ttl=10)
    def func_b(x):
        counter_ind.increment()
        return x
    
    func_a.clear_cache()
    func_b.clear_cache()
    func_a(1)
    func_b(1)
    assert counter_ind.count == 2
    print("✅ Teste 7: Independência de instâncias passou.")

    print("\n--- TODOS OS TESTES PASSARAM COM SUCESSO ---")

if __name__ == "__main__":
    run_tests()