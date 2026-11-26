import threading
import queue
import time
import random

class ThreadPool:
    def __init__(self, num_threads):
        self.num_threads = num_threads
        self.task_queue = queue.Queue()
        self.results_lock = threading.Lock()
        self.completed_tasks = 0
        
        # CORREÇÃO 1: Usar threading.Event para sinalização de parada segura
        self._stop_event = threading.Event()
        
        self.workers = []
        self.is_running = True # Mantido para checagem rápida, mas _stop_event é a fonte da verdade
        
        # Inicia os workers (NÃO daemon=True)
        for _ in range(num_threads):
            worker = threading.Thread(target=self._worker)
            # CORREÇÃO 2: Threads NÃO são daemon para garantir shutdown graceful
            worker.daemon = False 
            worker.start()
            self.workers.append(worker)

    def _worker(self):
        """Função executada por cada thread worker."""
        while not self._stop_event.is_set():
            try:
                # Espera por uma tarefa com timeout para checar o evento de parada
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
                # Se a fila estiver vazia, checa o evento de parada e continua
                continue
            except Exception as e:
                print(f"Erro inesperado no worker: {e}")
                break

    def submit(self, func, *args, **kwargs):
        """Adiciona uma tarefa à fila, validando entrada e estado."""
        # CORREÇÃO 3: Validação de entrada e verificação de estado
        if not callable(func):
            raise TypeError("A função fornecida para submit deve ser chamável.")
        if not self.is_running:
            raise RuntimeError("Não é possível submeter tarefas: o pool foi encerrado.")
            
        self.task_queue.put((func, args, kwargs))

    def shutdown(self, wait_for_tasks=True):
        """Encerra o pool de forma segura."""
        print("Iniciando shutdown do pool...")
        
        if wait_for_tasks:
            # Espera que todas as tarefas submetidas sejam processadas
            self.task_queue.join()
            
        # Sinaliza aos workers que devem parar
        self._stop_event.set()
        self.is_running = False
        
        # Espera todos os workers terminarem
        for worker in self.workers:
            worker.join()
            
        print("Todas as tarefas foram processadas.")
        print("Pool encerrado com sucesso.")


# --- Teste de Execução ---
NUM_TASKS = 100
NUM_THREADS = 5

def sample_task(task_id):
    # Simula trabalho com pequena variação de tempo
    time.sleep(random.uniform(0.001, 0.005))
    # print(f"Tarefa {task_id} concluída.")

if __name__ == "__main__":
    start_time = time.time()
    
    pool = ThreadPool(NUM_THREADS)
    
    # Submissão de tarefas
    for i in range(NUM_TASKS):
        try:
            pool.submit(sample_task, i)
        except (TypeError, RuntimeError) as e:
            print(f"Erro ao submeter tarefa {i}: {e}")
            break
            
    # Shutdown seguro
    pool.shutdown(wait_for_tasks=True)
    
    end_time = time.time()
    
    # Verificação de integridade
    print(f"Total de tarefas submetidas: {NUM_TASKS}")
    print(f"Total de tarefas concluídas (verificado pelo Lock): {pool.completed_tasks}")
    print(f"Tempo total de execução: {end_time - start_time:.4f} segundos")
    
    # Critério de sucesso: 100 tarefas processadas sem deadlocks/condições de corrida
    assert pool.completed_tasks == NUM_TASKS, "Falha: O número de tarefas concluídas não corresponde ao submetido."
    print("✅ Critério de sucesso atendido: Todas as tarefas foram processadas com integridade de dados.")