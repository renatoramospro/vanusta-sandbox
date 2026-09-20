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
    - Conversão recursiva de argumentos mutáveis (list, dict, set, tuple) para tipos hasháveis
    """
    def decorator(func):
        # cache armazena: { hashable_key: (result, expiry_timestamp) }
        cache = OrderedDict()
        lock = threading.RLock()

        def _make_hashable(obj):
            """Converte recursivamente objetos mutáveis em imutáveis para permitir hashing."""
            if isinstance(obj, (list, tuple)):
                return tuple(_make_hashable(item) for item in obj)
            if isinstance(obj, dict):
                # Converte dict em frozenset de pares (chave, valor_hashável)
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
                        # Expira o item antigo
                        del cache[key]

                # 3. Executar a função original (fora do lock para não bloquear outras chamadas de chaves diferentes?)
                # Nota: Para garantir thread-safety total na escrita do cache, mantemos o lock 
                # ou usamos um lock granular. Para este nível, o lock no wrapper é seguro.
                # Para evitar gargalo, o ideal seria liberar o lock durante a execução da func,
                # mas isso abriria para "cache stampede". Manteremos o lock para garantir consistência.
                
                # Para evitar que o lock segure a execução de funções lentas por muito tempo,
                # em implementações de produção, usaríamos um lock por chave.
                # Aqui, para simplicidade e correção do requisito, mantemos o lock.
                
                result = func(*args, **kwargs)
                
                # 4. Atualizar cache e gerenciar maxsize (FIFO)
                cache[key] = (result, now + ttl)
                if len(cache) > maxsize:
                    cache.popitem(last=False) # Remove o primeiro inserido (FIFO)
                
                return result

        def clear_cache():
            with lock:
                cache.clear()

        wrapper.clear_cache = clear_cache
        return wrapper
    return decorator

# --- Testes de Rigor ---

class Counter:
    def __init__(self):
        self.count = 0
        self._lock = threading.Lock()
    def increment(self):
        with self._lock:
            self.count += 1

def run_tests():
    print("--- Iniciando Testes de Rigor ---")

    # Teste 1: Memoização básica
    call_count = 0
    @memoize(ttl=10)
    def basic_func(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    assert basic_func(5) == 10
    assert basic_func(5) == 10
    assert call_count == 1
    print("✅ Teste 1: Memoização básica passou.")

    # Teste 2: Expiração de TTL
    @memoize(ttl=1)
    def ttl_func(x):
        nonlocal call_count
        call_count += 1
        return x

    call_count = 0
    ttl_func(1)
    ttl_func(1)
    assert call_count == 1
    time.sleep(1.1)
    ttl_func(1)
    assert call_count == 2
    print("✅ Teste 2: Expiração de TTL passou.")

    # Teste 3: Argumentos mutáveis aninhados (O erro que causou a reprovação)
    @memoize(ttl=10)
    def complex_arg_func(data):
        return len(data)

    # Teste com lista dentro de tupla e dict dentro de lista
    complex_data = ([1, 2], {"a": [3, 4]})
    # Se não converter recursivamente, isso falhará com TypeError
    try:
        res = complex_arg_func(complex_data)
        assert res == 2
        # Segunda chamada deve ser cache hit
        res2 = complex_arg_func(complex_data)
        assert res2 == 2
        print("✅ Teste 3: Argumentos mutáveis aninhados passaram.")
    except TypeError as e:
        print(f"❌ Teste 3: Falhou com TypeError: {e}")
        exit(1)

    # Teste 4: TTL Zero (Expiração imediata)
    @memoize(ttl=0)
    def zero_ttl_func(x):
        nonlocal call_count
        call_count += 1
        return x

    call_count = 0
    zero_ttl_func(1)
    zero_ttl_func(1) # Deve reexecutar pois ttl=0 faz expiry = now
    assert call_count == 2
    print("✅ Teste 4: TTL=0 (expiração imediata) passou.")

    # Teste 5: Limite de Tamanho (Maxsize FIFO)
    @memoize(ttl=10, maxsize=2)
    def size_func(x):
        nonlocal call_count
        call_count += 1
        return x

    call_count = 0
    size_func(1) # count 1
    size_func(2) # count 2
    size_func(3) # count 3, expulsa o '1'
    size_func(1) # count 4, pois o '1' foi expulso
    assert call_count == 4
    print("✅ Teste 5: Limite de maxsize (FIFO) passou.")

    # Teste 6: Concorrência (Thread-safety)
    counter = Counter()
    @memoize(ttl=10)
    def concurrent_func(x):
        time.sleep(0.01) # Simula carga para aumentar janela de race condition
        counter.increment()
        return x

    concurrent_func.clear_cache()
    threads = []
    for _ in range(20):
        t = threading.Thread(target=concurrent_func, args=(10,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()

    # Com o lock correto, apenas uma thread deve ter incrementado o contador
    assert counter.count == 1
    print(f"✅ Teste 6: Concorrência passou (Chamadas reais: {counter.count}).")

    print("\n--- TODOS OS TESTES PASSARAM COM SUCESSO ---")

if __name__ == "__main__":
    run_tests()