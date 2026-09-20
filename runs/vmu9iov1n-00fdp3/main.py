import time
import threading
from functools import wraps
from collections import OrderedDict

def memoize(ttl=5, maxsize=128):
    """
    Decorador de memoização com suporte a:
    - TTL (Time-To-Live)
    - Limite de tamanho (maxsize) com política FIFO
    - Thread-safety via RLock
    - Conversão recursiva de argumentos mutáveis para tipos hasháveis
    """
    def decorator(func):
        # cache armazena: { hashable_key: (result, expiry_timestamp) }
        cache = OrderedDict()
        lock = threading.RLock()

        def _make_hashable(obj):
            """Converte recursivamente objetos mutáveis em imutáveis para permitir hashing."""
            if isinstance(obj, list):
                return tuple(_make_hashable(item) for item in obj)
            if isinstance(obj, dict):
                return frozenset((k, _make_hashable(v)) for k, v in obj.items())
            if isinstance(obj, set):
                return frozenset(_make_hashable(item) for item in obj)
            return obj

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Preparar a chave de cache de forma robusta
            hashable_args = _make_hashable(args)
            hashable_kwargs = _make_hashable(kwargs)
            key = (hashable_args, hashable_kwargs)

            now = time.time()

            with lock:
                # 2. Verificar se existe no cache e se não expirou
                if key in cache:
                    result, expiry = cache[key]
                    if now < expiry:
                        # Cache Hit
                        # Move para o fim para manter a ordem de uso (opcional para FIFO puro, 
                        # mas aqui usamos para gerenciar o maxsize)
                        cache.move_to_end(key)
                        return result
                    else:
                        # Expired
                        del cache[key]

                # 3. Cache Miss ou Expirado: Executar a função
                result = func(*args, **kwargs)
                
                # 4. Gerenciar tamanho do cache (FIFO)
                if len(cache) >= maxsize:
                    cache.popitem(last=False) # Remove o mais antigo

                # 5. Armazenar no cache
                cache[key] = (result, now + ttl)
                return result

        # Método auxiliar para limpeza em testes
        def clear_cache():
            with lock:
                cache.clear()
        
        wrapper.clear_cache = clear_cache
        return wrapper
    return decorator

# --- EXPERIMENTO E TESTES ---

class Counter:
    def __init__(self):
        self.count = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.count += 1
        return self.count

def run_tests():
    print("--- Iniciando Testes de Rigor ---")
    
    # Teste 1: Memoização Básica
    @memoize(ttl=10)
    def add(a, b):
        return a + b

    assert add(2, 3) == 5
    assert add(2, 3) == 5  # Cache hit
    print("✅ Teste 1: Memoização básica passou.")

    # Teste 2: Expiração de TTL
    @memoize(ttl=1)
    def slow_func():
        return time.time()

    val1 = slow_func()
    time.sleep(1.1)
    val2 = slow_func()
    assert val1 != val2
    print("✅ Teste 2: Expiração de TTL passou.")

    # Teste 3: Argumentos Mutáveis (O ponto crítico do erro anterior)
    @memoize(ttl=10)
    def process_list(data):
        return sum(data)

    assert process_list([1, 2, 3]) == 6
    assert process_list([1, 2, 3]) == 6  # Deve usar cache mesmo sendo lista
    assert process_list([4, 5]) == 9
    print("✅ Teste 3: Argumentos mutáveis (listas) passaram.")

    # Teste 4: Concorrência e Thread-Safety
    counter = Counter()
    
    @memoize(ttl=10)
    def concurrent_func(x):
        counter.increment()
        return x

    # Limpar cache para garantir que as threads encontrem o cache vazio
    concurrent_func.clear_cache()

    def worker():
        for _ in range(50):
            concurrent_func(10)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()

    # Se o lock e a lógica de cache funcionarem, o contador deve ser exatamente 1
    # pois todas as threads chamam o mesmo argumento (10)
    assert counter.count == 1
    print(f"✅ Teste 4: Concorrência passou (Chamadas reais: {counter.count}).")

    # Teste 5: Limite de Tamanho (Maxsize)
    @memoize(ttl=10, maxsize=2)
    def size_test(x):
        return x

    size_test.clear_cache()
    size_test(1)
    size_test(2)
    size_test(3) # Deve expulsar o '1'
    
    # Para verificar se o '1' foi expulso, vamos forçar uma nova execução
    # Como não temos acesso direto ao cache interno para ver o tamanho, 
    # vamos usar um contador para validar a re-execução.
    c2 = Counter()
    @memoize(ttl=10, maxsize=2)
    def size_check(x):
        c2.increment()
        return x
    
    size_check.clear_cache()
    size_check(1) # count=1
    size_check(2) # count=2
    size_check(3) # count=3, expulsa 1
    size_check(1) # count=4 (pois 1 foi expulso)
    
    assert c2.count == 4
    print("✅ Teste 5: Limite de maxsize (FIFO) passou.")

    print("\n--- TODOS OS TESTES PASSARAM COM SUCESSO ---")

if __name__ == "__main__":
    run_tests()