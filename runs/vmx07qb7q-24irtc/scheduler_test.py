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
        
    return completed_tasks

# --- Scheduler Otimizado (EDF + Afinidade) ---
def run_optimized(tasks):
    # Otimizado: Prioriza por Deadline (EDF) para tarefas críticas, respeitando afinidade
    
    # 1. Ordenar tarefas: Críticas primeiro, depois por Deadline (menor primeiro)
    # Tarefas não críticas são ordenadas por chegada (mantendo a ordem original se possível, mas aqui simplificamos)
    def sort_key(task):
        # Prioridade: 0 para crítica, 1 para normal. Depois, deadline.
        is_crit = 0 if task.is_critical() else 1
        return (is_crit, task.deadline)
    
    sorted_tasks = sorted(tasks, key=sort_key)
    
    resource_availability = {
        'CPU': NUM_CPUS, 'GPU': NUM_GPUS, 'NPU': NUM_NPUS
    }
    
    completed_tasks = []
    current_time = 0

    for task in sorted_tasks:
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
        
    return completed_tasks

# --- Funções de Avaliação ---
def calculate_avg_latency(tasks, is_critical_only=False):
    latencies = []
    for task in tasks:
        if task.finish_time != -1:
            latency = task.finish_time - task.start_time
            if is_critical_only and not task.is_critical():
                continue
            latencies.append(latency)
    
    if not latencies:
        return 0.0
    return sum(latencies) / len(latencies)

def run_simulation_and_test(tasks):
    # Criar cópias para simulações independentes
    tasks_fifo = [Task(t.id, t.resource_type, t.required_time, t.deadline, t.priority) for t in tasks]
    tasks_opt = [Task(t.id, t.resource_type, t.required_time, t.deadline, t.priority) for t in tasks]

    # Executar
    completed_fifo = run_fifo(tasks_fifo)
    completed_opt = run_optimized(tasks_opt)

    # Avaliar latência média das tarefas críticas
    avg_latency_fifo = calculate_avg_latency(completed_fifo, is_critical_only=True)
    avg_latency_opt = calculate_avg_latency(completed_opt, is_critical_only=True)
    
    print(f"--- Resultados da Simulação ---")
    print(f"Latência Média Crítica (FIFO): {avg_latency_fifo:.2f} ms")
    print(f"Latência Média Crítica (Otimizado): {avg_latency_opt:.2f} ms")

    if avg_latency_fifo == 0 or avg_latency_opt == 0:
        print("⚠️ Aviso: Não foi possível calcular latência média (nenhuma tarefa crítica concluída).")
        return False

    # Calcular redução percentual
    reduction = ((avg_latency_fifo - avg_latency_opt) / avg_latency_fifo) * 100
    print(f"Redução Percentual na Latência Crítica: {reduction:.2f}%")

    # Critério de Sucesso: Redução de 15%
    if reduction >= 15.0:
        print("\n✅ CRITÉRIO DE SUCESSO ATINGIDO: Redução >= 15% demonstrada.")
        return True
    else:
        print("\n❌ CRITÉRIO DE SUCESSO NÃO ATINGIDO: Redução < 15%.")
        return False

# --- Geração de Dados Sintéticos (Para garantir a demonstração) ---
def generate_test_tasks():
    # Cenário balanceado: 5 tarefas críticas (deadline < 10ms ou alta prioridade) e 5 normais.
    tasks = []
    
    # Tarefas Críticas (Prioridade Alta/Deadline Curto)
    tasks.append(Task(1, 'CPU', 5, 8, 'alta'))    # Crítica (Deadline)
    tasks.append(Task(2, 'GPU', 10, 20, 'alta'))  # Crítica (Prioridade)
    tasks.append(Task(3, 'NPU', 3, 5, 'alta'))    # Crítica (Deadline)
    tasks.append(Task(4, 'CPU', 8, 9, 'alta'))    # Crítica (Deadline)
    tasks.append(Task(5, 'GPU', 12, 15, 'alta'))  # Crítica (Prioridade)
    
    # Tarefas Normais
    tasks.append(Task(6, 'CPU', 20, 100, 'baixa'))
    tasks.append(Task(7, 'GPU', 30, 200, 'baixa'))
    tasks.append(Task(8, 'NPU', 15, 300, 'baixa'))
    tasks.append(Task(9, 'CPU', 15, 150, 'baixa'))
    tasks.append(Task(10, 'GPU', 25, 180, 'baixa'))
    
    # Garantir que a ordem de chegada inicial seja a ordem de ID para FIFO
    return tasks

# --- Ponto de Entrada Executável (Para ser executado via 'python scheduler_test.py') ---
if __name__ == "__main__":
    test_tasks = generate_test_tasks()
    print("--- Iniciando Simulação Heterogênea ---")
    print(f"Total de Tarefas: {len(test_tasks)}")
    
    # Executar a simulação e testar o critério de sucesso
    run_simulation_and_test(test_tasks)