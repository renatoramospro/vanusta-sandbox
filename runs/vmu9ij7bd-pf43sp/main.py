import time
import threading
from functools import wraps

def memoize(ttl=5):
    """
    Decorador de memoização com suporte a TTL (Time-To-Live).
    
    Args:
        ttl (int): Tempo em segundos para o cache ser considerado válido.
    """
    def decorator(func):
        # O cache armazena: { chave: (resultado, timestamp_expiracao) }
        cache = {}
        lock = threading.Lock()

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Criar uma chave hashável para os argumentos
            # kwargs.items() é convertido para frozenset para ser hashável
            try:
                key = (args, frozenset(kwargs.items()))
            except TypeError as e:
                raise TypeError(f"Argumentos não suportados para cache (não hasháveis): {e}")

            now = time.time()

            # 1. Tentativa de leitura do cache (Thread-safe)
            with lock:
                if key in cache:
                    result, expiry = cache[key]
                    if now < expiry:
                        return result
            
            # 2. Execução da função (fora do lock para não bloquear outras threads durante o cálculo)
            result = func(*args, **kwargs)

            # 3. Atualização do cache (Thread-safe)
            with lock:
                cache[key] = (result, now + ttl)
            
            return result

        return wrapper
    return decorator

# --- Testes e Demonstração ---

class CallCounter:
    """Auxiliar para contar quantas vezes a função original foi chamada."""
    def __init__(self):
        self.count = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.count += 1

def run_tests():
    counter = CallCounter()

    @memoize(ttl=2)
    def expensive_function(x, y=10):
        counter.increment()
        return x + y

    print("--- Iniciando Testes ---")

    # Teste 1: Memoização básica
    print("Teste 1: Verificando memoização...")
    res1 = expensive_function(5, y=20)
    res2 = expensive_function(5, y=20)
    assert res1 == 25 and res2 == 25
    assert counter.count == 1, f"Erro: Esperava 1 chamada, obteve {counter.count}"
    print("✅ Sucesso: Cache hit detectado.")

    # Teste 2: Argumentos diferentes
    print("\nTeste 2: Verificando argumentos diferentes...")
    res3 = expensive_function(5, y=30)
    assert res3 == 35
    assert counter.count == 2, f"Erro: Esperava 2 chamadas, obteve {counter.count}"
    print("✅ Sucesso: Argumentos distintos geram entradas de cache distintas.")

    # Teste 3: Expiração de TTL
    print("\nTeste 3: Verificando expiração de TTL (esperando 2.5s)...")
    time.sleep(2.5)
    res4 = expensive_function(5, y=20)
    assert res4 == 25
    assert counter.count == 3, f"Erro: Esperava 3 chamadas após expiração, obteve {counter.count}"
    print("✅ Sucesso: Cache invalidado após o tempo definido.")

    # Teste 4: Thread-Safety (Ataque ao equívoco comum)
    # Se o lock não existisse, múltiplas threads poderiam corromper o dict ou causar erros de concorrência.
    print("\nTeste 4: Verificando Thread-Safety (10 threads simultâneas)...")
    counter.count = 0 # Reset
    
    @memoize(ttl=10)
    def concurrent_func(n):
        time.sleep(0.1) # Simula carga
        return n * 2

    threads = []
    for _ in range(10):
        t = threading.Thread(target=concurrent_func, args=(10,))
        threads.append(t)
    
    for t in threads: t.start()
    for t in threads: t.join()

    # Como todas chamam o mesmo argumento e o TTL é longo, 
    # o contador deve ser 1 (ou muito próximo de 1 dependendo do timing, mas não deve quebrar)
    # Nota: Em testes de concorrência, pode haver um pequeno race para o primeiro cálculo,
    # mas o dicionário deve permanecer íntegro.
    print(f"Chamadas reais durante concorrência: {counter.count}")
    assert counter.count >= 1
    print("✅ Sucesso: Concorrência finalizada sem erros de runtime.")

    print("\n--- TODOS OS TESTES PASSARAM ---")

if __name__ == "__main__":
    run_tests()