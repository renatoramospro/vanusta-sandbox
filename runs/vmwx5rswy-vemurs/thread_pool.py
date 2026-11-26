import threading
import queue
import time
import random

class ThreadPool:
    def __init__(self, num_threads):
        self.num_threads = num_threads
        # Fila de tarefas segura (thread-safe por design)
        self.task_queue = queue.Queue()
        # Lock para proteger o contador de resultados (recurso compartilhado)
        self.results_lock = threading.Lock()
        self.completed_tasks = 0
        self.is_running = True
        self.workers = []

        # Inicia os workers
        for _ in range(num_threads):
            worker = threading.Thread(target=self._worker)
            worker.daemon = True  # Permite que o programa principal termine mesmo se threads estiverem bloqueadas
            worker.start()
            self.workers.append(worker)

    def _worker(self):
        """Função executada por cada thread worker."""
        while self.is_running or not self.task_queue.empty():
            try:
                # Espera por uma tarefa com timeout para permitir checagem de is_running
                task, args, kwargs = self.task_queue.get(timeout=0.1)
                
                try:
                    # Executa a tarefa
                    task(*args, **kwargs)
                    
                    # Acesso seguro ao recurso compartilhado (contador)
                    with self.results_lock:
                        self.completed_tasks += 1
                        
                except Exception as e:
                    print(f"Erro ao executar tarefa: {e}")
                finally:
                    # Sinaliza que a tarefa foi processada
                    self.task_queue.task_done()
            except queue.Empty:
                # Se a fila estiver vazia e o pool ainda estiver rodando, continua o loop
                continue
            except Exception as e:
                # Captura erros inesperados no worker
                print(f"Erro inesperado no worker: {e}")
                break

    def submit(self, func, *args, **kwargs):
        """Adiciona uma tarefa à fila."""
        if not self.is_running:
            raise RuntimeError("Pool está encerrando e não aceita novas tarefas.")
        self.task_queue.put((func, args, kwargs))

    def shutdown(self, wait_for_tasks=True):
        """Encerra o pool de forma segura."""
        print("\nIniciando shutdown do pool...")
        self.is_running = False
        
        if wait_for_tasks:
            # Espera que todas as tarefas na fila sejam processadas
            self.task_queue.join()
            print("Todas as tarefas foram processadas.")
        
        # Aguarda os workers terminarem (embora sejam daemon, é boa prática)
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=1) # Timeout para evitar bloqueio infinito
        print("Pool encerrado com sucesso.")

# --- Teste de Carga ---
NUM_TASKS = 100
NUM_THREADS = 5

# Tarefa de exemplo que simula trabalho e modifica o estado compartilhado
def worker_task(task_id):
    # Simula trabalho variável
    time.sleep(random.uniform(0.001, 0.01))
    # A modificação do contador é feita DENTRO do pool, não aqui diretamente,
    # mas esta função representa o trabalho que precisa ser atômico em relação ao estado global.
    pass

if __name__ == "__main__":
    pool = ThreadPool(NUM_THREADS)
    
    start_time = time.time()
    
    # Submete as tarefas
    for i in range(NUM_TASKS):
        pool.submit(worker_task, i)
        
    # Garante que o pool processe tudo e encerra de forma segura
    pool.shutdown(wait_for_tasks=True)
    
    end_time = time.time()

    print("-" * 40)
    print(f"Total de tarefas submetidas: {NUM_TASKS}")
    print(f"Total de tarefas concluídas (verificado pelo Lock): {pool.completed_tasks}")
    print(f"Tempo total de execução: {end_time - start_time:.4f} segundos")
    
    # Critério de sucesso: 100 tarefas processadas sem deadlocks/condições de corrida
    assert pool.completed_tasks == NUM_TASKS, "Falha: O número de tarefas concluídas não corresponde ao submetido."
    print("✅ Critério de sucesso atendido: Todas as tarefas foram processadas com integridade de dados.")
