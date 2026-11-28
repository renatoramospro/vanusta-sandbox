import time
import random
from collections import deque

# --- Configurações do Cenário ---
NUM_CPUS = 4
NUM_GPUS = 2
NUM_NPUS = 1
TOTAL_RESOURCES = NUM_CPUS + NUM_GPUS + NUM_NPUS

# --- Estrutura de Tarefa ---
class Task:
    def __init__(self, task_id, resource_type, required_time, deadline, priority):
        self.id = task_id
        self.resource_type = resource_type  # 'CPU', 'GPU', 'NPU'
        self.required_time = required_time  # Tempo de execução simulado em ms
        self.deadline = deadline            # Deadline em ms
        self.priority = priority            # 'baixa', 'alta'
        self.start_time = -1
        self.finish_time = -1

    def is_critical(self):
        # Critério definido pelo Arquiteto: deadline < 10ms OU prioridade == "alta"
        return self.deadline < 10 or self.priority == "alta"

    def __repr__(self):
        crit = "CRITICAL" if self.is_critical() else "Normal"
        return f"Task({self.id}, {self.resource_type}, {crit}, D={self.deadline}ms)"

# --- Scheduler FIFO ---
def run_fifo(tasks):
    # FIFO: Processa na ordem de chegada
    task_queue = deque(tasks)
    resource_availability = {
        'CPU': NUM_CPUS, 'GPU': NUM_GPUS, 'NPU': NUM_NPUS
    }
    
    completed_tasks = []
    current_time = 0

    while task_queue:
        task = task_queue.popleft()
        
        # Espera por recurso
        while resource_availability[task.resource_type] <= 0:
            current_time += 1
        
        # Alocação
        resource_availability[task.resource_type] -= 1
        task.start_time = current_time
        current_time += task.required_time
        task.finish_time = current_time
        resource_availability[task.resource_type] += 1
        
        completed_tasks.append(task)
        current_time += 1 # Simulação de overhead de troca de contexto

    return completed_tasks

# --- Scheduler Otimizado (EDF + Afinidade) ---
def run_optimized(tasks):
    # Otimizado: Prioriza por Deadline (EDF) e respeita afinidade
    # Ordenação: 1. Crítico (Alta Prioridade), 2. Deadline mais cedo, 3. Chegada (implícito)
    sorted_tasks = sorted(tasks, key=lambda t: (not t.is_critical(), t.deadline))
    
    task_queue = deque(sorted_tasks)
    resource_availability = {
        'CPU': NUM_CPUS, 'GPU': NUM_GPUS, 'NPU': NUM_NPUS
    }
    
    completed_tasks = []
    current_time = 0

    while task_queue:
        task = task_queue.popleft()
        
        # Espera por recurso
        while resource_availability[task.resource_type] <= 0:
            current_time += 1
        
        # Alocação
        resource_availability[task.resource_type] -= 1
        task.start_time = current_time
        current_time += task.required_time
        task.finish_time = current_time
        resource_availability[task.resource_type] += 1
        
        completed_tasks.append(task)
        current_time += 1 # Simulação de overhead de troca de contexto

    return completed_tasks

# --- Geração de Dados Sintéticos ---
def generate_tasks(num_tasks=20):
    task_types = ['CPU', 'GPU', 'NPU']
    tasks = []
    for i in range(num_tasks):
        r_type = random.choice(task_types)
        # Tempo de execução simulado (1-15ms)
        req_time = random.randint(1, 15) 
        # Deadline: 5% chance de ser crítico (<10ms)
        deadline = random.randint(5, 50)
        priority = 'alta' if random.random() < 0.15 else 'baixa'
        
        # Forçar algumas tarefas críticas para garantir o teste
        if i % 5 == 0:
            deadline = random.randint(1, 9)
            priority = 'alta'
            
        tasks.append(Task(i, r_type, req_time, deadline, priority))
    return tasks

# --- Avaliação ---
def evaluate(completed_tasks):
    critical_latencies = []
    for task in completed_tasks:
        if task.is_critical():
            latency = task.finish_time - task.start_time
            critical_latencies.append(latency)
    
    if not critical_latencies:
        return 0, 0, 0 # Não há tarefas críticas
        
    avg_latency = sum(critical_latencies) / len(critical_latencies)
    return avg_latency, len(critical_latencies), len(completed_tasks)

# --- Execução Principal ---
if __name__ == "__main__":
    # Gerar um conjunto de tarefas
    tasks_input = generate_tasks(num_tasks=50)
    
    # 1. Executar FIFO
    tasks_fifo_copy = [Task(t.id, t.resource_type, t.required_time, t.deadline, t.priority) for t in tasks_input]
    completed_fifo = run_fifo(tasks_fifo_copy)
    avg_latency_fifo, count_critical_fifo, _ = evaluate(completed_fifo)

    # 2. Executar Otimizado
    tasks_opt_copy = [Task(t.id, t.resource_type, t.required_time, t.deadline, t.priority) for t in tasks_input]
    completed_opt = run_optimized(tasks_opt_copy)
    avg_latency_opt, count_critical_opt, _ = evaluate(completed_opt)
    
    # 3. Comparação
    print(f"--- Relatório de Simulação Heterogênea ({NUM_CPUS}C/{NUM_GPUS}G/{NUM_NPUS}N) ---")
    print(f"Total de Tarefas Críticas Encontradas: FIFO={count_critical_fifo}, Otimizado={count_critical_opt}")
    print(f"Latência Média Crítica (FIFO): {avg_latency_fifo:.2f} ms")
    print(f"Latência Média Crítica (Otimizado): {avg_latency_opt:.2f} ms")
    
    if avg_latency_fifo > 0:
        reduction = ((avg_latency_fifo - avg_latency_opt) / avg_latency_fifo) * 100
        print(f"Redução Percentual na Latência Média Crítica: {reduction:.2f}%")
        
        # Critério de Sucesso: Redução de 15%
        if reduction >= 15.0:
            print("\n✅ CRITÉRIO DE SUCESSO ATINGIDO: Redução >= 15% demonstrada.")
        else:
            print("\n❌ CRITÉRIO DE SUCESSO NÃO ATINGIDO: Redução < 15%.")
    else:
        print("⚠️ Aviso: Nenhuma tarefa crítica foi identificada para avaliação.")
