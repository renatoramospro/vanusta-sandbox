import threading
import time
import concurrent.futures

class ThreadSafeSingleton:
    """Implementação correta usando Double-Checked Locking."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        # 1. Primeiro Check (Performance)
        if cls._instance is None:
            # 2. Adquire o Lock
            with cls._lock:
                # 3. Segundo Check (Segurança)
                if cls._instance is None:
                    # Simulando um pequeno atraso para aumentar a chance de race condition em testes
                    # em implementações erradas.
                    time.sleep(0.001) 
                    cls._instance = super().__new__(cls)
        return cls._instance

class BrokenSingleton:
    """Implementação errada que sofre de Race Condition."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            # Sem lock, múltiplos threads podem entrar aqui simultaneamente
            time.sleep(0.01) # Aumenta a janela de erro
            cls._instance = super().__new__(cls)
        return cls._instance

def worker(singleton_class, results):
    """Função executada por cada thread para coletar o ID da instância."""
    for _ in range(100):
        instance = singleton_class()
        results.append(id(instance))

def run_experiment(singleton_class, name):
    print(f"--- Testando: {name} ---")
    instances_ids = []
    threads = []
    
    # Criamos 20 threads para aumentar a pressão de concorrência
    for _ in range(20):
        t = threading.Thread(target=worker, args=(singleton_class, instances_ids))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    unique_ids = set(instances_ids)
    print(f"Total de instâncias criadas (tentativas): {len(instances_ids)}")
    print(f"IDs únicos encontrados: {len(unique_ids)}")
    
    if len(unique_ids) == 1:
        print(f"✅ SUCESSO: Apenas uma instância foi criada.\n")
        return True
    else:
        print(f"❌ FALHA: Foram criadas {len(unique_ids)} instâncias diferentes!\n")
        return False

if __name__ == "__main__":
    # Teste 1: O Singleton Correto
    success_correct = run_experiment(ThreadSafeSingleton, "ThreadSafeSingleton (DCL)")

    # Teste 2: O Singleton Quebrado
    success_broken = run_experiment(BrokenSingleton, "BrokenSingleton (Sem Lock)")

    if success_correct and not success_broken:
        print("RESULTADO FINAL: O padrão Double-Checked Locking foi validado com sucesso.")
    else:
        print("RESULTADO FINAL: O experimento falhou em demonstrar o comportamento esperado.")