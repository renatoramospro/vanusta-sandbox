import heapq
import threading
import time
import random

class Task:
    def __init__(self, priority: int, task_id: int):
        self.priority = priority
        self.task_id = task_id

    # Necessário para comparar tarefas no heap caso tenham a mesma prioridade
    def __lt__(self, other):
        return self.priority < other.priority

class PriorityTaskScheduler:
    def __init__(self, max_concurrency: int):
        self.max_concurrency = max_concurrency
        self.queue = []
        self.lock = threading.Lock()
        self.semaphore = threading.Semaphore(max_concurrency)
        
        # Métricas para validação
        self.current_active = 0
        self.max_observed_concurrency = 0
        self.metrics_lock = threading.Lock()
        self.execution_log = []

    def add_task(self, priority: int, task_id: int):
        with self.lock:
            task = Task(priority, task_id)
            heapq.heappush(self.queue, task)

    def worker(self, stop_event):
        while not stop_event.is_set():
            with self.lock:
                if not self.queue:
                    break
                task = heapq.heappop(self.queue)

            # Adquire permissão para executar respeitando o limite de concorrência
            self.semaphore.acquire()
            
            with self.metrics_lock:
                self.current_active += 1
                if self.current_active > self.max_observed_concurrency:
                    self.max_observed_concurrency = self.current_active

            try:
                # Simula trabalho da tarefa (curta duração)
                time.sleep(0.005)
                with self.metrics_lock:
                    self.execution_log.append((task.priority, task.task_id))
            finally:
                with self.metrics_lock:
                    self.current_active -= 1
                self.semaphore.release()

    def run(self, num_workers: int = 8):
        stop_event = threading.Event()
        threads = []
        
        for _ in range(num_workers):
            t = threading.Thread(target=self.worker, args=(stop_event,))
            t.start()
            threads.append(t)

        # Aguarda a fila esvaziar
        while True:
            with self.lock:
                if not self.queue and self.current_active == 0:
                    break
            time.sleep(0.001)

        stop_event.set()
        for t in threads:
            t.join()

if __name__ == "__main__":
    print("Iniciando teste do Agendador de Tarefas Concorrente...")
    
    # Configuração do teste: Limite de concorrência 4, 100 tarefas
    MAX_CONCURRENCY = 4
    NUM_TASKS = 100
    
    scheduler = PriorityTaskScheduler(max_concurrency=MAX_CONCURRENCY)
    
    # Adiciona 100 tarefas com prioridades aleatórias entre 1 e 10
    random.seed(42)
    for i in range(NUM_TASKS):
        priority = random.randint(1, 10)
        scheduler.add_task(priority, task_id=i)
        
    start_time = time.time()
    scheduler.run(num_workers=8)
    elapsed = time.time() - start_time
    
    print(f"Executadas {NUM_TASKS} tarefas em {elapsed:.3f} segundos.")
    print(f"Concorrência máxima observada: {scheduler.max_observed_concurrency} (Limite configurado: {MAX_CONCURRENCY})")
    
    # Validação 1: O limite de concorrência nunca foi violado?
    assert scheduler.max_observed_concurrency <= MAX_CONCURRENCY, f"Violação de concorrência! Máximo: {scheduler.max_observed_concurrency}"
    
    # Validação 2: Todas as 100 tarefas foram executadas?
    assert len(scheduler.execution_log) == NUM_TASKS, f"Esperado {NUM_TASKS} execuções, obtido {len(scheduler.execution_log)}"
    
    # Validação 3: Verificação parcial da ordem de prioridade
    # Tarefas de prioridade mais alta (menor número) tendem a sair antes. 
    # Vamos verificar se as primeiras tarefas executadas possuem prioridade média menor que as últimas.
    first_quartile = [p for p, tid in scheduler.execution_log[:25]]
    last_quartile = [p for p, tid in scheduler.execution_log[-25:]]
    
    avg_first = sum(first_quartile) / len(first_quartile)
    avg_last = sum(last_quartile) / len(last_quartile)
    
    print(f"Média de prioridade do 1º quartil executado: {avg_first:.2f}")
    print(f"Média de prioridade do último quartil executado: {avg_last:.2f}")
    
    assert avg_first <= avg_last, "A fila de prioridade não ordenou corretamente a execução!"
    
    print("SUCESSO: Todas as validações passaram sem condições de corrida ou violação de limites!")