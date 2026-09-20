import time
import threading
from functools import wraps

def _make_hashable(obj):
    """Converte objetos mutáveis em imutáveis para permitir o uso como chave de cache."""
    if isinstance(obj, (list, tuple)):
        return tuple(_make_hashable(i) for i in obj)
    if isinstance(obj, dict):
        return frozenset((k, _make_hashable(v)) for k, v in obj.items())
    if isinstance(obj, set):
        return frozenset(_make_hashable(i) for i in obj)
    return obj

def memoize(ttl=5, maxsize=128):
    """
    Decorador de memoização com TTL e limite de tamanho.
    :param ttl: Tempo de vida em segundos.
    :param maxsize: Número máximo de entradas no cache.
    """
    def decorator(func):
        cache = {}
        lock = threading.RLock()

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Criar chave hashable baseada nos argumentos
            hashable_args = _make_hashable(args)
            hashable_kwargs = _make_hashable(kwargs)
            key = (hashable_args, hashable_kwargs)

            now = time.time()

            # 2. Tentativa de leitura do cache (Thread-safe)
            with lock:
                if key in cache:
                    result, expiry = cache[key]
                    if now < expiry:
                        return result
                    else:
                        # Expira o item
                        del cache[key]

            # 3. Execução da função (fora do lock para não bloquear outras threads)
            # Nota: Em cenários de 'thundering herd', múltiplas threads podem
            # executar a função simultaneamente se o cache estiver vazio.
            # Isso é preferível a travar o cache inteiro durante uma operação lenta.
            result = func(*args, **kwargs)

            # 4. Escrita no cache (Thread-safe)
            with lock:
                # Gerenciamento de tamanho (FIFO simples)
                if len(cache) >= maxsize:
                    oldest_key = next(iter(cache))
                    del cache[oldest_key]
                
                cache[key] = (result, time.time() + ttl)
            
            return result

        # Método auxiliar para testes/inspeção
        def cache_info():
            with lock:
                return len(cache)
        
        wrapper.cache_info = cache_info
        return wrapper
    return decorator